# %%

import ollama
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
import time

import json

load_dotenv()

openai.api_key = os.getenv('OPENAI_API_KEY')
openai_client = openai.OpenAI()

# openai_client = openai.OpenAI(
#     base_url="http://localhost:11434/v1",
#     api_key="ollama",
# )

def start_ssh():
    ssh = pexpect.spawn('ssh -p 3022 root@localhost', encoding='utf-8')
    ssh.expect("root@localhost's password: ")
    ssh.sendline('toor')
    ssh.expect(r'└─\x1b\[1;31m#', timeout=4)
    a = ssh.before.strip()
    # Real ghetto to put here but just want it to run after the hp has spun up
    global last_checked
    last_checked = datetime.datetime.now(datetime.UTC).isoformat()

    return ssh

# rep_openai = response_openai(messages=[{"role": "user", "content": "Can you see my current directory using your tool/function_call terminal_input?"}], tools=tools, model="gpt-4o-mini")

# %%
def response_ollama(messages: list, tools, model: str):
    print(f"Using model: {model}")
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

    print("running ollama.chat")
    resp = ollama.chat(
        model=model,
        messages=messages,
        stream=False
    )
    print(resp)

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
last_checked = datetime.datetime.now(datetime.UTC).isoformat()
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
    last_checked = datetime.datetime.now(datetime.UTC).isoformat()

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
