# %% 
import openai
import os
import json
import time
import Red.sangria_config as sangria_config
import config
import Red.log_extractor as log_extractor
import Red.tools as red_tools
from Utils.jsun import append_json_to_file, save_json_to_file
from Red.terminal_io import start_ssh

tools = sangria_config.tools
messages = sangria_config.get_messages()

openai.api_key = os.getenv('OPENAI_API_KEY')
openai_client = openai.OpenAI()

# %% save messages as json to file

def create_json_log(messages):
    # Convert messages to JSON serializable format
    serializable_messages = []
    for msg in messages:
        if hasattr(msg, 'model_dump'):
            # For Pydantic models (like ChatCompletionMessage)
            serializable_messages.append(msg.model_dump())
        elif hasattr(msg, 'dict'):
            # Alternative method for some object types
            serializable_messages.append(msg.dict())
        else:
            # For regular dictionaries
            serializable_messages.append(msg)

    # Parse string JSON fields to actual JSON objects
    for msg in serializable_messages:
        if msg.get('role') == 'assistant' and msg.get('tool_calls'):
            for tool_call in msg['tool_calls']:
                if 'function' in tool_call and 'arguments' in tool_call['function']:
                    try:
                        tool_call['function']['arguments'] = json.loads(tool_call['function']['arguments'])
                    except (json.JSONDecodeError, TypeError):
                        pass  # Keep as string if not valid JSON

        elif msg.get('role') == 'tool' and 'content' in msg:
            try:
                msg['content'] = json.loads(msg['content'])
            except (json.JSONDecodeError, TypeError):
                # If it's not valid JSON, try to evaluate as Python literal
                try:
                    import ast
                    msg['content'] = ast.literal_eval(msg['content'])
                except (ValueError, SyntaxError):
                    # Keep as string if neither JSON nor valid Python literal
                    pass
            

    # Convert to JSON string without saving to file
    return serializable_messages
    # json_string = json.dumps(serializable_messages, indent=4)
    # return json_string
# %%

def openai_call(model, messages, tools, tool_choice, wait_time=1):
    try:
        return openai_client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice
        )

    except openai.RateLimitError as e:
        print("OpenAI API limit reached, waiting", wait_time, "seconds...")
        print("Might also be out of money", e.message)
        time.sleep(wait_time)
        return openai_call(model, messages, tools, tool_choice, wait_time * 2)

def run_single_attack(messages, max_session_length, full_logs_path, attack_counter=0, config_counter=0):
    '''
        Main loop for running a single attack session.
        This function will let the LLM respond to the user, call tools, and log the responses.
        The goal is to let it run a series of commands to a console and log the responses.
    '''
    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_cached_tokens = 0

    # using full logs and messages, full logs will also include the the honeypot logs

    ssh = None
    if not config.simulate_command_line:
        ssh = start_ssh()

    for message in messages:
        append_json_to_file(message, full_logs_path, False)

    for i in range(max_session_length):
        BOLD   = "\033[1m"
        RESET  = "\033[0m"

        print(f'{BOLD}Iteration {i+1} / {max_session_length}, Attack {attack_counter+1}, Configuration {config_counter}{RESET}')

        assistant_response = openai_call(config.llm_model_sangria, messages, tools, "auto")

        total_cached_tokens += assistant_response.usage.prompt_tokens_details.cached_tokens
        total_completion_tokens += assistant_response.usage.completion_tokens
        total_prompt_tokens += assistant_response.usage.prompt_tokens - assistant_response.usage.prompt_tokens_details.cached_tokens

        message = assistant_response.choices[0].message
        tool_calls = message.tool_calls or []
        tool_use = None
        fn_name = ""

        messages.append(message.model_dump())
        append_json_to_file(message.model_dump(), full_logs_path, False)

        print(f"Prompt tokens: {assistant_response.usage.prompt_tokens}, Completion tokens: {assistant_response.usage.completion_tokens}, Cached tokens: {total_cached_tokens}")

        if message.content:
            print(f"Assistant message: {message.content}")

        if message.content == "I’m sorry, but I can’t help with that.":
            print("LLM refused to help, ending session.")
            break


        for tool_use in tool_calls:
            fn_name = tool_use.function.name
            fn_args = json.loads(tool_use.function.arguments)

            terminal_input_tools = list(filter(lambda x: x['role'] == 'tool' and x['name'] == 'terminal_input', messages))
            if not config.simulate_command_line:
                beelzebub_logs = log_extractor.get_new_hp_logs()
                if terminal_input_tools:
                    last_terminal_input_tool = terminal_input_tools[-1]
                    last_terminal_input_tool["honeypot_logs"] = beelzebub_logs
                
            result, mitre_method_used = red_tools.handle_tool_call(fn_name, fn_args, ssh)

            tool_response = {
                "role": "tool",
                "name": fn_name,
                "tool_call_id": tool_use.id,
                "content": str(result['content'])

            }
            messages.append(tool_response)
            append_json_to_file(tool_response, full_logs_path, False)

            # messages[-1]["honeypot_logs"] = last_terminal_input_tool.get("honeypot_logs", "")


            BOLD   = "\033[1m"
            RESET  = "\033[0m"
            print(f"{BOLD}Tool call: {RESET} {fn_name}")
            print(f"{BOLD}With args: {RESET}")
            for key, value in fn_args.items():
                print(f"\t{key}: {value}")
            print(f"\n{BOLD}Tool response: \n{RESET} {result['content']}")
            print("\x1b[0m")


        if tool_use:
            followup = openai_call(config.llm_model_sangria, messages, None, None)
            assistant_msg = followup.choices[0].message
            messages.append(assistant_msg.model_dump())
            append_json_to_file(assistant_msg.model_dump(), full_logs_path, False)

            BOLD   = "\033[1m"
            RESET  = "\033[0m"
            print(f"{BOLD}Follow‑up message:{RESET} {assistant_msg.content}")

        if fn_name == "terminate":
            print("Termination tool called, ending session.")
            break

        
    messages_log_json = create_json_log(messages)
    save_json_to_file(messages_log_json, full_logs_path)

    total_tokens_used = {
        "prompt_tokens": total_prompt_tokens,
        "completion_tokens": total_completion_tokens,
        "cached_tokens": total_cached_tokens
    }

    return messages_log_json, total_tokens_used

if __name__ == "__main__":
    test_single_attack = run_single_attack(messages, 2, "test_logs.json")


# %%
