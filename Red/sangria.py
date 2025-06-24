# %%
import json
import sys
import os
from Red.schema import response, start_ssh, get_new_hp_logs
import Red.sangria_config as sangria_config

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

from Red.defender_llm import run_command
from Red.tools import handle_tool_call
from Red.model import MitreMethodUsed, DataLogObject
from config import max_session_length
from Blue_Lagoon.honeypot_tools import start_dockers, stop_dockers

import os

# test if key works

tools = sangria_config.tools
messages = sangria_config.messages
mitre_method_used_list = []
max_itterations = 5

def run_single_attack(save_logs, messages):
    '''
        Main loop for running a single attack session.
        This function will let the LLM respond to the user, call tools, and log the responses.
        The goal is to let it run a series of commands to a console and log the responses.
    '''
    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_cached_tokens = 0

    # start SSH connection to Kali Linux
    if not config.simulate_command_line:
        ssh = start_ssh()
    else:
        ssh = None

    full_logs = []
    
    for i in range(max_session_length):
        print(f'Iteration {i+1} / {max_session_length}')

        data_log = DataLogObject(i)

        # get response from OpenAI
        assistant_response = response(sangria_config.model_host, config.llm_model_sangria, messages, tools)

        total_prompt_tokens += assistant_response.prompt_tokens - assistant_response.cached_tokens 
        total_completion_tokens += assistant_response.completion_tokens
        total_cached_tokens += assistant_response.cached_tokens
        print(f"Prompt tokens: {assistant_response.prompt_tokens}, Completion tokens: {assistant_response.completion_tokens}, Cached tokens: {assistant_response.cached_tokens}")
        
        data_log.llm_response = assistant_response

        tool_response = None
        mitre_method_used = MitreMethodUsed()

        # check for text in response
        if assistant_response.message:
            messages.append({
                "role": "assistant",
                "content": assistant_response.message
            })

        # check for tools in response
        if assistant_response.function:
            tool_response, mitre_method_used = handle_tool_call(assistant_response, ssh)
            messages.append(tool_response)
            
            data_log.tool_response = tool_response['content']
            # data_log.mitre_attack_method = mitre_method_used

            if tool_response['name'] == "terminate":
                print(f"The attack was {'successfull' if tool_response['content'] else 'unsucsessfull'} after {i + 1} iterations.")

                if tool_response['content'] == "True":
                    data_log.attack_success = True
                break

        mitre_method_used_list.append(mitre_method_used)

        # print the respones
        if config.print_output:
            if assistant_response.message:
                print(f"Sangria: {assistant_response.message}")
            if assistant_response.function:
                print(f"Tool call: {assistant_response.function, assistant_response.arguments}")
                print(f"Command response: {tool_response['content'] if tool_response else 'No tool call made'}")
                print(f"Mitre Method Used: {mitre_method_used if mitre_method_used else 'No Mitre Method Used'}")
                print("-" * 50)
        
        if save_logs:
            beelzebub_logs = get_new_hp_logs()
            data_log.beelzebub_response = beelzebub_logs

        if save_logs:
            full_logs.append(data_log)

    print(f"Total prompt tokens: {total_prompt_tokens}")
    print(f"Total completion tokens: {total_completion_tokens}")
    print(f"Total cashed tokens: {total_cached_tokens}")

    tokens_used = {
        "prompt_tokens": total_prompt_tokens,
        "completion_tokens": total_completion_tokens,
        "cached_tokens": total_cached_tokens
    }

    return full_logs, tokens_used

def run_attacks(n_attacks, save_logs, log_path):
    '''
        Run multiple attack sessions.
        Each session will run a attack and log the responses.
    '''
    all_logs = []
    tokens_used_list = []

    for i in range(n_attacks):
        
        messages = sangria_config.messages.copy()  # Reset messages for each attack
        start_dockers()
        print(f"Running attack session {i + 1} / {n_attacks}")
        logs, tokens_used = run_single_attack(save_logs, messages)
        all_logs.append(logs)
        tokens_used_list.append(tokens_used)

        append_logs_to_file(logs, log_path + f"attack_{i+1}", save_logs)
        save_tokens_used_to_file(tokens_used, log_path + f"tokens_used_{i+1}", save_logs)
        stop_dockers()

    return all_logs

def save_tokens_used_to_file(tokens_used_list, session_id, save_logs=True):
    '''
        Save the tokens used to a file, will be appended if file already exists.
        The file will be saved in the logs/tokens_used directory.
        The file will be named tokens_used_<session_id>.json
    '''

    if not save_logs:
        print("Saving tokens used is disabled.")
        return
    
    print(f"Saving tokens used to file for session {session_id}...")
    
    path = f'{session_id}.json'
    
    # Load existing data if the file exists
    if os.path.exists(path):
        with open(path, 'r') as f:
            existing_data = json.load(f)
    else:
        existing_data = []

    # Append new tokens used to existing data
    existing_data.append(tokens_used_list)

    with open(path, 'w') as f:
        json.dump(existing_data, f, indent=4)

    print("File written:", os.path.exists(path), "Size:", os.path.getsize(path))

def append_logs_to_file(logs, session_id, save_logs=True):
    '''
        Append the logs to a file, will be created if file does not exist.
        The file will be saved in the logs/full_logs directory.
        The file will be named full_logs_<session_id>.json
    '''

    if not save_logs:
        print("Saving logs is disabled.")
        return
    
    print(f"Appending logs to file for session {session_id}...")
    
    # Create the logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    os.makedirs('logs/full_logs', exist_ok=True)
    
    path = f'{session_id}.json'
    
    # Load existing data if the file exists
    if os.path.exists(path):
        with open(path, 'r') as f:
            existing_data = json.load(f)
    else:
        existing_data = []

    # Append new logs to existing data
    existing_data.append([log.to_dict() for log in logs])

    with open(path, 'w') as f:
        json.dump(existing_data, f, indent=4)

    print("File written:", os.path.exists(path), "Size:", os.path.getsize(path))


def save_logs_to_file(all_logs, session_id, save_logs=True):
    '''
        Save the logs to a file, will be appended if file already exists.
        The file will be saved in the logs/full_logs directory.
        The file will be named full_logs_<session_id>.json
    '''

    if not save_logs:
        print("Saving logs is disabled.")
        return
    
    print(f"Saving logs to file for session {session_id}...")
    # print([[log.to_dict() for log in session_log] for session_log in all_logs])
    # Create the logs directory if it doesn't exist
    
    os.makedirs('logs', exist_ok=True)
    os.makedirs('logs/full_logs', exist_ok=True)
    path = f'logs/full_logs/full_logs_{session_id}.json'
    data = [[log.to_dict() for log in session_log] for session_log in all_logs]

    with open(path, 'w') as f:
        json.dump(data, f, indent=4)

    print("File written:", os.path.exists(path), "Size:", os.path.getsize(path))

    print(f"\nMessages saved to logs/full_logs/full_logs_{str(session_id)}.json")

# %%

# all_logs = run_attacks(2, save_logs=True)
# save_logs_to_file(all_logs, 'test_id', save_logs_flag=True)


# %%
