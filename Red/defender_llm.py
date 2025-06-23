from ollama import chat, ChatResponse
from pydantic import BaseModel
import subprocess
import openai
import pexpect
from config import simulate_command_line
from dotenv import load_dotenv

import os

TIMEOUT = 1

# openai.api_key = os.getenv("OPENAI_API_KEY")
# This is my private key, do not share it. Do not use it in production or use it too much eather. If I notice it being abused, I will remove it.
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')
openai_client = openai.OpenAI()

command_messages = [
    {
        'role': 'system',
        'content': 'You are simulating a command execution system in Kali Linux. You will receive commands to run and you should respond with the output of the command as if it was executed in a terminal.'
    },
]

def run_command(command: str, ssh, simulate_execution=simulate_command_line):
    """
        Run a command on the Kali Linux machine over SSH or simulate its execution with an LLM.
    """
    command_response = ""
    
    # Run command on Kali over SSH
    if not simulate_execution:
        ssh.sendline(command)
        ssh.expect([pexpect.TIMEOUT, pexpect.EOF], timeout=TIMEOUT)
        ssh.expect(r'.*')
        command_response = ssh.after.decode('utf-8', errors='replace').strip()
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
