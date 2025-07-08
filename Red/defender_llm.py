from ollama import chat, ChatResponse
from pydantic import BaseModel
import subprocess
import openai
import pexpect
from config import simulate_command_line
from dotenv import load_dotenv

import os

TIMEOUT = 100

# openai.api_key = os.getenv("OPENAI_API_KEY")
# This is my private key, do not share it. Do not use it in production or use it too much eather. If I notice it being abused, I will remove it.
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')
openai_client = openai.OpenAI()

prompt_patterns = [pexpect.EOF, 
                    r'└─\x1b\[1;31m#',
                    r' \x1b\[0m> ', 
                    r'Are you sure you want to continue connecting \(yes/no/\[fingerprint\]\)\? ',
                    'password: ',
                    r'\:\~\$ ',
                    "Please type 'yes', 'no' or the fingerprint: "]

def send_terminal_command(connection, command):
    try:
        connection.sendline(command)
        connection.expect(prompt_patterns, timeout=TIMEOUT)    
    except pexpect.exceptions.TIMEOUT:
        connection.expect(r'.*')

    matched_pattern = connection.match.group(0) if connection.match else ""

    command_response = f"{connection.before.strip()}{matched_pattern}"
    return command_response

command_messages = [
    {
        'role': 'system',
        'content': 'You are simulating a command execution system in Kali Linux. You will receive commands to run and you should respond with the output of the command as if it was executed in a terminal.'
    },
]

def terminal_input(command: str, ssh, simulate_execution=simulate_command_line):
    """
        Run a command on the Kali Linux machine over SSH or simulate its execution with an LLM.
    """
    command_response = ""
    
    # Run command on Kali over SSH
    if not simulate_execution:
        command_response = send_terminal_command(ssh, command)
        if len(command_response) > 10000:
            command_response = command_response[-10000:]
        
        return command_response

    # Simulate command execution
    if simulate_execution:
        command_messages.append({
            'role': 'user',
            'content': f'Run the command: {command}'
        })

        # send to OpenAI and get back the assistant message
        raw_resp = openai_client.chat.completions.create(
            model='gpt-4o-mini',
            messages=command_messages
        )
        msg = raw_resp.choices[0].message
        # extract content string and append
        command_text = msg.content
        command_messages.append({
            'role': 'assistant',
            'content': command_text
        })
        
    return command_text
    
    # return shell output in non-simulated or if simulate_execution is False
