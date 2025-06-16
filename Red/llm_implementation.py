# %%
import json
from schema import response, start_ssh, upload_langfuse, get_new_hp_logs
import config
from defender_llm import run_command
from config import simulate_command_line
from tools import handle_tool_call
from model import MitreMethodUsed, DataLogObject
from config import log_output
import time

from langfuse_sdk import Langfuse
import uuid

import os

# test if key works

tools = config.tools
messages = config.messages
mitre_method_used_list = []
n_it = 25


# start SSH connection to Kali Linux
if not simulate_command_line:
    ssh = start_ssh()
else:
    ssh = None

if log_output == True:
    command_log = []
    response_log = []
    dialogue_log = ""
    tactics_log = set()
    techniques_log = set()
    honeypot_log = []
    langfuse = Langfuse(
    secret_key=os.getenv('SCT_KEY_LANGFUSE'),
    public_key="pk-lf-9eb0f9b3-a939-4f73-bc29-753c200c3e38",
    host="https://cloud.langfuse.com"
    )

    logger = langfuse.trace()

# %%
for i in range(n_it):
    print(f'Iteration {i+1} / {n_it}')

    session_id = str(uuid.uuid4())
    data_log = DataLogObject(i)

    # get response from OpenAI
    assistant_response = response(config.model_host, config.model, messages, tools)
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
        data_log.llm_response = assistant_response.message

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
    if log_output == True:
        command_log.append({
        "iteration": i,
        "Command": assistant_response.arguments,
        "Reasoning": assistant_response.message
        })

        response_log.append({
            "iteration": i,
            "Command Response": tool_response['content'] if tool_response else 'No tool call made'
        })

        dialogue_log += (
            f"Iteration {i+1}:\n"
            f"Command: {assistant_response.arguments}\n"
            f"Tactic: {mitre_method_used.tactic_used if mitre_method_used else 'N/A'}\n\n"
            f"Technique: {mitre_method_used.technique_used if mitre_method_used else 'N/A'}\n\n"
            f"Response: {tool_response['content'] if tool_response else 'No tool call made'}\n"
        )

        if mitre_method_used and mitre_method_used.tactic_used and mitre_method_used.technique_used:
            tactics_log.add(mitre_method_used.tactic_used)
            techniques_log.add(mitre_method_used.technique_used)

    # print the respones
    print(f"Assistant: {assistant_response.message}")
    print(f"Tool call: {assistant_response.function, assistant_response.arguments}")
    print(f"Command response: {tool_response['content'] if tool_response else 'No tool call made'}")
    print(f"Mitre Method Used: {mitre_method_used if mitre_method_used else 'No Mitre Method Used'}")
    print("-" * 50)
    
    if config.get_honeypot_logs:
        new_logs = get_new_hp_logs()
        data_log.beelzebub_response = new_logs

    if log_output:
        honeypot_log.append(data_log)

if log_output:
    # honeypot_log = [log.to_dict() for log in honeypot_log]
    upload_langfuse(command_log, response_log, dialogue_log, tactics_log, techniques_log, honeypot_log, logger)

# %%
# for message in messages:
#     print(f"{message['role'].capitalize()}: {message['content']}")

# make messenges to json
messages_json = json.dumps(messages, indent=2)

print(mitre_method_used_list)
# %%
if log_output:
    import time
    timestamp = time.time()
    with open('logs/conversation_' + str(timestamp) + '.json', 'w') as f:
        # Convert DataLogObject instances to dictionaries before JSON serialization
        
        log_dicts = [log.to_dict() for log in honeypot_log]
        f.write(json.dumps(log_dicts, indent=2))

    print("\nMessages saved to conversation.json")

# %%