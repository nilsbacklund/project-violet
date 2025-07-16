from pathlib import Path
from typing import Dict, Any
import sys
import json
import os

# Add parent directory to sys.path to allow imports from project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Utils.jsun import save_json_to_file, load_json
from Utils.logprecis import recombine_labels, divide_statements

BASE_DIR = Path(__file__).resolve().parent.parent

# only keep commands when the attacker has gained access
def extract_session(logs: Dict[str, Any]) -> Dict[str, Any]:
    session_log = {}

    session_string = ""
    tactics = []
    techniques = []
    full_session = []

    for i, entry in enumerate(logs):
        if entry["role"] != "assistant":
            continue

        if not entry["tool_calls"]:
            continue
    
        # Get follow up message
        num_tool_calls = len(entry["tool_calls"])
        tool_entry_index = i + num_tool_calls + 1

        # If terminates before tool call
        if tool_entry_index >= len(logs):
            continue

        follow_up_entry = logs[tool_entry_index]
        assert follow_up_entry["role"] == "assistant"
        follow_up_content = follow_up_entry["content"]
        
        for j, tool in enumerate(entry["tool_calls"]):
            if tool["function"]["name"] != "terminal_input":
                continue

            arguments = tool["function"]["arguments"]
            if type(arguments) is str:
                arguments = json.loads(arguments)

            if "tactic_used" in arguments:
                tactic = arguments["tactic_used"]
                tactic_clean = str(tactic).split(":")[-1]
            else:
                tactic = "Error: No tactic found"
                tactic_clean = "Error: No tactic found"
            if "technique_used" in arguments:
                technique = arguments["technique_used"]
                technique_clean = str(technique).split(":")[-1]
            else:
                technique = "Error: No technique found"
                technique_clean = "Error: No technique found"

            hp_entry = logs[i + j + 1]
            # check that hp iteration is a tool
            assert hp_entry["role"] == "tool"
            if "honeypot_logs" not in hp_entry:
                continue
            for log in hp_entry["honeypot_logs"]:
                if "event" not in log:
                    continue
                
                event = log["event"]
                if str(event["Protocol"]).lower() != "ssh":
                    continue

                if "Command" in event and str(event["Command"]).strip():
                    hp_commands = str(event["Command"]).strip()
                    for hp_command in divide_statements(hp_commands):
                        session_string += hp_command + " "
                        full_session.append({
                            "command": hp_command,
                            "tactic_raw": tactic,
                            "tactic": tactic_clean,
                            "technique_raw": technique,
                            "technique": technique_clean,
                            "content": follow_up_content
                        })
                        tactics.append(tactic_clean)
                        techniques.append(technique_clean)

    session_string = session_string.strip()
    session_log["session"] = session_string
    session_log["tactics"] = recombine_labels(tactics)
    session_log["techniques"] = recombine_labels(techniques)
    assert len(tactics) == len(techniques)
    session_log["length"] = len(tactics)
    session_log["full_session"] = full_session
    return session_log

def extract_everything_session(logs: Dict[str, Any]) -> Dict[str, Any]:
    session_log = {}
    session_string = ""
    tactics = []
    techniques = []
    full_session = []

    for i, entry in enumerate(logs):
        if entry["role"] != "assistant":
            continue

        if not entry["tool_calls"]:
            continue
    
        # Get follow up message
        num_tool_calls = len(entry["tool_calls"])
        tool_entry_index = i + num_tool_calls + 1

        # If terminates before tool call
        if tool_entry_index >= len(logs):
            continue

        follow_up_entry = logs[tool_entry_index]
        assert follow_up_entry["role"] == "assistant"
        follow_up_content = follow_up_entry["content"]
        
        for tool in entry["tool_calls"]:
            if tool["function"]["name"] != "terminal_input":
                continue

            arguments = tool["function"]["arguments"]
            if type(arguments) is str:
                arguments = json.loads(arguments)

            if "tactic_used" in arguments:
                tactic = arguments["tactic_used"]
                tactic_clean = str(tactic).split(":")[-1]
            else:
                tactic = "Error: No tactic found"
                tactic_clean = "Error: No tactic found"
            if "technique_used" in arguments:
                technique = arguments["technique_used"]
                technique_clean = str(technique).split(":")[-1]
            else:
                technique = "Error: No technique found"
                technique_clean = "Error: No technique found"

            commands = str(arguments["input"]).strip() 
            if commands:
                for command in divide_statements(commands):
                    session_string += command + " "
                    full_session.append({
                        "command": command,
                        "tactic_raw": tactic,
                        "tactic": tactic_clean,
                        "technique_raw": technique,
                        "technique": technique_clean,
                        "content": follow_up_content
                    })
                    tactics.append(tactic_clean)
                    techniques.append(technique_clean)

    # grab terminate command
    discovered_honeypot = "unknown"
    terminate_entry = logs[-2]
    if terminate_entry["role"] == "tool" and terminate_entry["name"] == "terminate":
        discovered_honeypot = "yes" if terminate_entry["content"] else "no"

    session_string = session_string.strip()
    session_log["session"] = session_string
    session_log["discovered_honeypot"] = discovered_honeypot
    session_log["tactics"] = recombine_labels(tactics)
    session_log["techniques"] = recombine_labels(techniques)
    assert len(tactics) == len(techniques)
    session_log["length"] = len(tactics)
    session_log["full_session"] = full_session
    return session_log

if __name__ == "__main__":
    experiment_path = BASE_DIR / "logs" / "experiment_2025-06-25T" / "hp_config_1"
    log_path = experiment_path / "full_logs" / "attack_1.json"
    logs = load_json(log_path)
    
    session_log = extract_session(logs)
    session_path = experiment_path / "sessions" / "session_1.json"
    save_json_to_file(session_log, session_path)