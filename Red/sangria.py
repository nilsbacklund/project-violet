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
from langfuse_sdk import Langfuse

import os

# test if key works

tools = sangria_config.tools
messages = sangria_config.messages
mitre_method_used_list = []
max_itterations = 1

def run_single_attack(max_itterations, save_logs):
    # start SSH connection to Kali Linux
    if not config.simulate_command_line:
        ssh = start_ssh()
    else:
        ssh = None

    full_logs = []
    
    for i in range(max_itterations):
        print(f'Iteration {i+1} / {max_itterations}')

        data_log = DataLogObject(i)

        # get response from OpenAI
        assistant_response = response(sangria_config.model_host, config.llm_model_sangria, messages, tools)
        data_log.llm_response = assistant_response

        print(assistant_response)

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
            data_log.mitre_attack_method = mitre_method_used
        else:
            user_response = {
                "role": "user",
                "content": "Create a plan and execute it with the tools aviable."
            }
            
            messages.append(user_response)

        mitre_method_used_list.append(mitre_method_used)

        # print the respones
        print(f"Assistant: {assistant_response.message}")
        print(f"Tool call: {assistant_response.function, assistant_response.arguments}")
        print(f"Command response: {tool_response['content'] if tool_response else 'No tool call made'}")
        print(f"Mitre Method Used: {mitre_method_used if mitre_method_used else 'No Mitre Method Used'}")
        print("-" * 50)
        
        if save_logs:
            beelzebub_logs = get_new_hp_logs()
            data_log.beelzebub_response = beelzebub_logs

        if save_logs:
            full_logs.append(data_log)

    return full_logs

def run_attacks(n_attacks, save_logs):
    all_logs = []

    for i in range(n_attacks):
        print(f"Running attack session {i + 1} / {n_attacks}")
        logs = run_single_attack(max_itterations, save_logs)
        all_logs.append(logs)

    return all_logs


def save_logs_to_file(all_logs, session_id, save_logs=True):
    if not save_logs:
        print("Saving logs is disabled.")
        return
    
    print(f"Saving logs to file for session {session_id}...")
    print([[log.to_dict() for log in session_log] for session_log in all_logs])
    # Create the logs directory if it doesn't exist
    
    os.makedirs('logs', exist_ok=True)
    path = f'logs/full_logs_{session_id}.json'
    data = [[log.to_dict() for log in session_log] for session_log in all_logs]

    with open(path, 'w') as f:
        json.dump(data, f, indent=4)

    print("File written:", os.path.exists(path), "Size:", os.path.getsize(path))

    print(f"\nMessages saved to logs/full_logs_{str(session_id)}.json")

# %%

# all_logs = run_attacks(2, save_logs=True)
# save_logs_to_file(all_logs, 'test_id', save_logs_flag=True)

# %%
