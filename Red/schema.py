# %%

#import ollama
import requests
import openai
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from types import SimpleNamespace
from Red.model import ResponseObject

import platform
if platform.system() != 'Windows':
    import pexpect

import subprocess
import datetime

import json

load_dotenv()

openai.api_key = os.getenv('OPENAI_API_KEY')
openai_client = openai.OpenAI()

def start_ssh():
    ssh = pexpect.spawn('ssh -p 3022 root@localhost')
    ssh.expect("root@localhost's password: ")
    ssh.sendline('toor')
    ssh.expect(pexpect.TIMEOUT, timeout=1)
    ssh.before.decode('utf-8').strip()
    return ssh

def response(model_host, model_name, messages, tools):
    if model_host == 'openai':
        return response_openai(messages, tools, model=model_name)
    elif model_host == 'ollama':
        return response_ollama(messages, tools, model=model_name)
    else:
        raise ValueError(f"Unsupported model host: {model_host}")

def response_openai(messages: list, tools, model: str = 'gpt-4o-mini'):
    response = openai_client.chat.completions.create(
        model=model,
        messages=messages,
        functions=tools,
    )

    choice = response.choices[0]
    content = choice.message.content
    function_call = choice.message.function_call

    prompt_tokens = response.usage.prompt_tokens
    completion_tokens = response.usage.completion_tokens

    # extract name & args safely (in case no call was made)
    fn_name = function_call.name if function_call else None
    fn_args = json.loads(function_call.arguments) if function_call else None

    # use a different var name so we don't shadow the class
    resp_obj = ResponseObject(
        message=content,
        function=fn_name,
        arguments=fn_args
    )
    resp_obj.prompt_tokens = prompt_tokens
    resp_obj.completion_tokens = completion_tokens

    return resp_obj

# rep_openai = response_openai(messages=[{"role": "user", "content": "Can you see my current directory using your tool/function_call run_command?"}], tools=tools, model="gpt-4o-mini")

# %%
def response_ollama(messages: list, tools, model: str):
    responde_to_user_tool = {
        "name": "respond_to_user",
        "description": "Responds to the user with a message.",
        "parameters": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "The message to respond with."
                }
            },
            "required": ["message"]
        }
    }

    tools.append(responde_to_user_tool)

    resp = ollama.chat(
        model=model,
        messages=messages,
        tools=tools,
        stream=False
    )

    # create response object of message
    content = resp.message.content if resp.message.content else None
    tool_calls = resp.message.tool_calls
    arguments = None
    if tool_calls:
        tool_call = tool_calls[0]
        arguments = tool_call.function.arguments if tool_call.function.arguments else {}

    tool_name = tool_calls[0].function.name if tool_calls else None
    if tool_name == "respond_to_user":
        content = tool_calls[0].function.arguments.get("message", content)
        tool_name = None
        arguments = None

    reply = ResponseObject(
        message=content,
        function=tool_name,
        arguments=arguments
    )
 
    return reply

# rep = response_ollama(messages=[{"role": "user", "content": "What files do i have?, only use the tools you are given."}], tools=tools, model="llama3.2:3b")

# %%

def _ns(**kw):
    """Shortcut: turn a dict into an attribute-style object."""
    return SimpleNamespace(**kw)

def response_ollama_workaround(messages, model="llama2"):
    """
    One shot request to Ollama.
    Returns an object whose shape mirrors
    openai.types.chat.chat_completion.Choice.
    """
    resp = ollama.chat(model=model, messages=messages)          # Ollama response
    text = resp["message"]["content"]

    # Did the model emit a JSON blob that looks like a function call?
    try:
        call = json.loads(text)
        
        if isinstance(call, dict) and {"name", "arguments"} <= call.keys():
            fn_call = _ns(
                name       = call["name"],
                arguments  = json.dumps(call["arguments"]),
            )
            # mirror OpenAI Choice
            return _ns(
                index          = 0,
                finish_reason  = "function_call",
                logprobs       = None,
                tool_calls     = None,
                annotations    = [],
                message        = _ns(
                    role          = "assistant",
                    content       = None,          # OpenAI leaves content empty on function calls
                    function_call = fn_call,
                    audio         = None,
                    refusal       = None,
                ),
            )
    except json.JSONDecodeError:
        pass

    # ----- normal assistant text ----------------------------------------
    return _ns(
        index          = 0,
        finish_reason  = "stop",
        logprobs       = None,
        tool_calls     = None,
        annotations    = [],
        message        = _ns(
            role          = "assistant",
            content       = text,
            function_call = None,
            audio         = None,
            refusal       = None,
        ),
    )

# %%
last_checked = datetime.datetime.utcnow().isoformat()
def get_new_hp_logs():
    """
    Fetch new logs from the Beelzebub container since the last check.
    Returns a list of parsed JSON objects or raw logs if parsing fails.
    """
    global last_checked

    process = subprocess.Popen(
        ["sudo", "docker", "logs", "blue_lagoon", "--since", last_checked],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    last_checked = datetime.datetime.utcnow().isoformat()

    log_output = process.stdout.read().strip()
    if log_output:
        #print(log_output)
        try:
            log_lines = log_output.strip().split('\n')
            logs = [json.loads(line) for line in log_lines if line.strip()]
            return logs  # Return parsed JSON objects instead of string
        except json.JSONDecodeError:
            # If parsing fails, return raw logs as fallback
            return {"raw_logs": log_output, "error": "Failed to parse JSON"}

        # trace = langfuse.trace(name="on-demand-log-check")
        # for line in log_output.splitlines():
        #     trace.span(name="log").log(line)

    return []  # Return empty list instead of empty string

# %%
def upload_langfuse(command_log, response_log, dialogue_log, tactics_log, techniques_log, honeypot_log, logger):
    """
    Uploads various logs to Langfuse for tracking and analysis.
    Not currently used, files stored in another place.
    """
    logger.generation(
        name="Offensive LLM Commands",
        input=json.dumps(command_log, indent=2),
        metadata={"label": "commands", "type": "LLM Commands"}
    )

    logger.generation(
        name="Offensive LLM Command Responses (Kali Linux)",
        input=json.dumps(response_log, indent=2),
        metadata={"label": "command responses", "type": "Command Responses"}
    )

    logger.generation(
        name="Dialogues",
        input=dialogue_log.strip(),
        metadata={"label": "dialogues", "type": "Dialogues"}
    )

    logger.generation(
        name="Tactics Used",
        input="\n".join(sorted(tactics_log)),
        metadata={"label": "tactics", "type": "Tactics"}
    )

    logger.generation(
        name="Techniques Used",
        input="\n".join(sorted(techniques_log)),
        metadata={"label": "techniques", "type": "Techniques"}
    )

    logger.generation(
        name="Honeypot Responses",
        input=json.dumps(honeypot_log, indent=2),
        metadata={"label": "honeypot responses", "type": "Honeypot Responses"}
    )