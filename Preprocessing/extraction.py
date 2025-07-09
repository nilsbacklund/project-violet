from pathlib import Path
from typing import Dict
import sys
import os

# Add parent directory to sys.path to allow imports from project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Utils.jsun import save_json_to_file, load_json
from Utils.logprecis import recombine_labels, divide_statements

BASE_DIR = Path(__file__).resolve().parent.parent

# only keep commands when the attacker has gained access
def extract_session(logs: Dict):
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

        for j, tool in enumerate(entry["tool_calls"]):
            if tool["function"]["name"] != "terminal_input":
                continue

            arguments = tool["function"]["arguments"]
            attacker_command = arguments["command"]
            tactic = arguments["tactic_used"]
            tactic_clean = str(tactic).split(":")[-1]
            technique = arguments["technique_used"]
            technique_clean = str(technique).split(":")[-1]

            hp_entry = logs[i + j + 1]
            # check that hp iteration is a tool
            assert hp_entry["role"] == "tool"

            hp_logs = hp_entry["honeypot_logs"]

            for log in hp_logs:
                event = log["event"]
                if str(event["Protocol"]).lower() != "ssh":
                    continue

                if "Command" in event and event["Command"]:
                    hp_commands = event["Command"]

                    for hp_command in divide_statements(hp_commands):
                        session_string += hp_command + " "
                        full_session.append({
                            "command": hp_command,
                            "attacker_command": attacker_command,
                            "tactic": tactic,
                            "tactic_clean": tactic_clean,
                            "technique": technique,
                            "technique_clean": technique_clean
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

if __name__ == "__main__":
    experiment_path = BASE_DIR / "logs" / "experiment_2025-06-25T" / "hp_config_1"
    log_path = experiment_path / "full_logs" / "attack_1.json"
    logs = load_json(log_path)
    
    session_log = extract_session(logs)
    session_path = experiment_path / "sessions" / "session_1.json"
    save_json_to_file(session_log, session_path)