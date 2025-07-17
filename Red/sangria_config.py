# %%
from Red.model import LLMHost
import json
from Red.attacker_prompts import AttackerPrompts

model_host = LLMHost.OPENAI  # change when using Ollama

# Can have prompt. C, I, A or general depending on intended purpose of attack.
# C = Confidentiality, I = Integrity, A = Availability.

def get_system_prompt(attacker_prompt: str) -> dict:
    system_prompt = {
        'role': 'system',
        'content': attacker_prompt
    }

    if model_host == LLMHost.OPENAI:
        system_prompt = system_prompt
    elif model_host == LLMHost.OLLAMA:
        system_prompt = system_prompt
    elif model_host == LLMHost.OLLAMA_NO_FC:
        system_prompt = get_system_prompt_workaround(attacker_prompt)
    else:
        raise ValueError(f"Unknown model host: {model_host}")
    
    return system_prompt

def get_messages(i=0):
    if i % 4 == 0:
        system_prompt = get_system_prompt(AttackerPrompts.GENERAL)
        prompt = "General"
    elif i % 4 == 1:
        system_prompt = get_system_prompt(AttackerPrompts.CONFIDENTIALITY)
        prompt = "Confidentiality"
    elif i % 4 == 2:
        system_prompt = get_system_prompt(AttackerPrompts.INTEGRITY)
        prompt = "Integrity"
    else:
        system_prompt = get_system_prompt(AttackerPrompts.AVAILABILITY)
        prompt = "Availability"

    print(f"Using prompt = {prompt}")
    messages = [
        system_prompt,
        {"role": "user", "content": "What is your next move?"}
    ]
    return messages


terminal_input = {
        "type": "function",
        "function": {
            "name": "terminal_input",
        "description": "Run a command on the Kali Linux SSH and name its connection to the MITRE ATT&CK Tactic and Technique. If the command is not an offensive tool, specify tactic and technique as 'Harmless'. Try not to use verbose options unless necessary. ",
            "parameters": {
                "type": "object",
                "properties": {
                    "input": {
                        "type": "string",
                        "description": "The terminal input to run in the Kali Linux machine. For example: 'nmap -sn 172.20.0.3', 'yes' 'root'"
                    },
                    "tactic_used": {
                        "type": "string",
                        "description": "The name of the tactic from MITRE ATT&CK. For example: 'TA0007:Discovery'"
                    },
                    "technique_used": {
                        "type": "string",
                        "description": "The name of the technique from MITRE ATT&CK. For example: 'T1018:Remote System Discovery'"
                    }
                },
                "required": ["input", "tactic_used", "technique_used"]
            }
        }    
    }

terminate_tool = {
        "type": "function",
        "function": {        
            "name": "terminate",
            "description": "Terminate the operation if the system is a honeypot or if you do not want to proceed. The operation will be terminated immediately.",
            "parameters": {
                "type": "object",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "description": "True if you discovered you where in a honeypot, false if you end due to other reasons."
                    }
                },
                "required": ['success']
            }
        }
    }

web_search_tool = {
        "type": "function",
        "function": {
            "name": "web_search_tool",
            "description": "Searches the web and returns the full content of top relevant pages.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to look up"
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "How many pages to fetch and scrape",
                        "default": 4
                    },
                    "max_chars": {
                        "type": "integer",
                        "description": "Maximum characters to return per page",
                        "default": 2500
                    }
                },
                "required": ["query"]
            }
        }
    }

tools = [
    terminal_input,
    terminate_tool
]



# if model_host == LLMHost.OPENAI:
#     tools = [
#         {
#             "type": "function",
#             "function": tool
#         } 
#         for tool in flat_tools
#     ]
# elif model_host == LLMHost.OLLAMA:
#     tools = tools
# elif model_host == LLMHost.ANTHROPIC:
#     from anthropic import Tool
#     tools = [
#         Tool(
#             name=tool["name"],
#             description=tool["description"],
#             parameters=tool["parameters"]
#         )
#         for tool in tools
#     ]

def get_system_prompt_workaround(attacker_prompt):
    system_prompt_ollama_workaround = {
        "role": "system",
        "content": (
            f"{attacker_prompt}"
            "## How to respond\n"
            "1. You may output **either**:\n"
            "   • normal assistant text (analysis, next steps, etc.), **or**\n"
            "   • **exactly one** tool call in **JSON** form, with no extra text.\n"
            "2. A tool call must be a single line that matches this schema *exactly*:\n"
            "   `{ \"name\": \"<tool-name>\", \"arguments\": { … } }`\n"
            "   – no markdown fences\n"
            "   – no additional keys\n"
            "3. After you call a tool, wait for the function result before continuing.\n\n"

            "### Example tool call\n"
            "{ \"name\": \"terminal_input\", \"arguments\": { \"command\": \"nmap -sS -p- 10.0.0.5\" } }\n\n"

            "## Available tools\n"
            f"{json.dumps(tools, indent=2)}\n"
        )
    }


# %%
