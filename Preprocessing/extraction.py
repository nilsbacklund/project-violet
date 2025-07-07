from pathlib import Path
from Utils.jsun import save_json_to_file, load_json
from typing import Dict

BASE_DIR = Path(__file__).resolve().parent.parent

def extract_session(log: Dict):
    session = {}
    session["full_session"] = []

    commands = []

    for entry in log:
        llm_response = entry["llm_response"]
        if llm_response["function"] == "run_command":
            arguments = llm_response["arguments"]

            command = arguments["command"]
            tactic = arguments["tactic_used"]
            technique = arguments["technique_used"]

            commands.append(command)
            
            label = tactic.split(":")[-1]

            session["full_session"].append({
                "command": command,
                "label": label,
                "tactic": tactic,
                "technique": technique
            })  

    session["session"] = " ; ".join(commands)
    print(session)
    return session

if __name__ == "__main__":
    experiment_path = BASE_DIR / "logs" / "experiment_2025-06-25T" / "hp_config_1"
    log_path = experiment_path / "full_logs" / "attack_1.json"
    log = load_json(log_path)
    
    session = extract_session(log)
    session_path = experiment_path / "sessions" / "session_1.json"
    save_json_to_file(session, session_path)