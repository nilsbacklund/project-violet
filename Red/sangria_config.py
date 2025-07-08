# %%

from Red.model import LLMHost, LLMModel
import json
import Red.attacker_prompts as prompt

model_host = LLMHost.OPENAI  # change when using Ollama, Anthropic is not supported yet

# Can have prompt. C, I, A or general depending on intended purpose of attack.
# C = Confidentiality, I = Integrity, A = Availability.

attacker_prompt: str = prompt.general          # prompt.C / I / A / general

tools = [
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Run a command on the Kali Linux SSH and name its connection to the MITRE ATT&CK Tacktic and Technique.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The command to run in the Kali Linux SSH."
                    },
                    "tactic_used": {
                        "type": "string",
                        "description": "The name of the tactic from MITRE ATT&CK." # , ex. TAxxxx."
                    },
                    "technique_used": {
                        "type": "string",
                        "description": "The name of the technique from MITRE ATT&CK" # , ex. Txxxx."
                    }
                },
                "required": ["command", "tactic_used", "technique_used"]
            }
        }    
    },
    {
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
    },
    {
        "type": "function",
        "function": {        
            "name": "terminate",
            "description": "Terminate the operation if the system is a honeypot or if you do not want to proceed. The operation will be terminated immediately.",
            "parameters": {
                "type": "object",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "description": "Whether the attack was successful or not."
                    }
                },
                "required": ['success']
            }
        }
    }
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
        "{ \"name\": \"run_command\", \"arguments\": { \"command\": \"nmap -sS -p- 10.0.0.5\" } }\n\n"

        "## Available tools\n"
        f"{json.dumps(tools, indent=2)}\n"
    )
}

system_prompt = {
    'role': 'system',
    'content': attacker_prompt
}

if model_host == LLMHost.OPENAI:
    system_prompt = system_prompt
elif model_host == LLMHost.OLLAMA:
    system_prompt = system_prompt
elif model_host == LLMHost.OLLAMA_NO_FC:
    system_prompt = system_prompt_ollama_workaround
else:
    raise ValueError(f"Unknown model host: {model_host}")

messages = [
    system_prompt,
    {"role": "user", "content": "What is your next move?"}
]
# %%
