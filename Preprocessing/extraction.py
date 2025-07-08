from pathlib import Path
from typing import Dict

from Utils.jsun import save_json_to_file, load_json
from Utils.logprecis import recombine_labels, divide_statements

BASE_DIR = Path(__file__).resolve().parent.parent

# only keep commands when the attacker has gained access
def extract_session(logs: Dict):
    session_log = {}

    session_string = ""
    labels = []
    full_session = []
    for entry in logs:
        llm_response = entry["llm_response"]
        if llm_response["function"] == "terminal_input" and entry["beelzebub_response"]:
            arguments = llm_response["arguments"]

            commands = arguments["command"]
            tactic = arguments["tactic_used"]
            technique = arguments["technique_used"]

            label = str(tactic).split(":")[-1]

            for command in divide_statements(commands):
                session_string += command + " "
                full_session.append({
                    "command": command,
                    "label": label,
                    "tactic": tactic,
                    "technique": technique
                })
                labels.append(label)

    session_string = session_string.strip()
    session_log["session"] = session_string
    session_log["labels"] = recombine_labels(labels)
    session_log["length"] = len(labels)
    session_log["full_session"] = full_session
    return session_log

if __name__ == "__main__":
    experiment_path = BASE_DIR / "logs" / "experiment_2025-06-25T" / "hp_config_1"
    log_path = experiment_path / "full_logs" / "attack_1.json"
    logs = load_json(log_path)
    
    session_log = extract_session(logs)
    session_path = experiment_path / "sessions" / "session_1.json"
    save_json_to_file(session_log, session_path)