# %%
import json
import sys
import os
from Red.schema import response, start_ssh, get_new_hp_logs
import Red.sangria_config as sangria_config
from Utils import save_json_to_file, append_json_to_file

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

        # get response from LLM
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
        
        if config.simulate_command_line:
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
    tokens_used_list = []

    for i in range(n_attacks):
        
        messages = sangria_config.messages.copy()  # Reset messages for each attack

        if not config.simulate_command_line:
            start_dockers()

        print(f"Running attack session {i + 1} / {n_attacks}")
        logs, tokens_used = run_single_attack(save_logs, messages)
        tokens_used_list.append(tokens_used)


        # create path if not exists
        os.makedirs(log_path + "full_logs", exist_ok=True)
        logs = [log.to_dict() for log in logs]
        save_json_to_file(logs, log_path + f"full_logs/attack_{i+1}.json", save_logs)
        append_json_to_file(tokens_used, log_path + f"tokens_used.json", save_logs)

        if not config.simulate_command_line:
            stop_dockers()


# %%

# all_logs = run_attacks(2, save_logs=True)
# save_logs_to_file(all_logs, 'test_id', save_logs_flag=True)


# %%
