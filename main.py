# %%
import os
print(os.getcwd())
import config
import Red.sangria_config as sangria_config
from pathlib import Path
from Red.sangria import run_single_attack
from Blue.new_config_pipeline import generate_new_honeypot_config, get_honeypot_config, set_honeypot_config
from Blue_Lagoon.honeypot_tools import init_docker, start_dockers, stop_dockers
from Preprocessing.extraction import extract_session
from Utils.meta import create_experiment_folder
from Utils.jsun import save_json_to_file, append_json_to_file
from dotenv import load_dotenv

load_dotenv()

def main():
    base_path = create_experiment_folder(config.save_logs, experiment_name=config.experiment_name)
    base_path = Path(base_path)

    honeypot_config = get_honeypot_config(id="00", path="")
    set_honeypot_config(honeypot_config)
    init_docker()

    config_counter = 1
    config_attack_counter = 0
    seen_techniques = set()

    if not config.simulate_command_line:
        start_dockers()

    tokens_used_list = []
    print(f"Configuration {config_counter}")
    config_path = base_path / f"hp_config_{config_counter}"
    full_logs_path = config_path / "full_logs"
    os.makedirs(full_logs_path, exist_ok=True)

    if config.save_configuration and not config.simulate_command_line:
        save_json_to_file(honeypot_config, config_path / f"honeypot_config.json")

    for i in range(config.num_of_attacks):
        if config.save_logs:
            os.makedirs(config_path, exist_ok=True) 
    
        print(f"Attack {i+1} / {config.num_of_attacks}")
        logs_path = full_logs_path / f"attack_{i+1}.json"

        messages = sangria_config.messages.copy()
        logs, tokens_used = run_single_attack(messages, config.max_session_length, logs_path)
        
        if config.save_logs:
            # save logs
            # save_json_to_file(logs, full_logs_path / f"attack_{i+1}.json")
            # update tokens used
            append_json_to_file(tokens_used, config_path / f"tokens_used.json")

        # append tokens
        tokens_used_list.append(tokens_used)

        # extract session and add attack pattern to set
        session = extract_session(logs)

        # Extract individual techniques from full_session
        current_techniques = set()
        for command_entry in session.get("full_session", []):
           if "technique" in command_entry and command_entry["technique"]:
               current_techniques.add(command_entry["technique"])

        if config.save_logs:
            # update sessions
            append_json_to_file(session, config_path / f"sessions.json")

        config_attack_counter += 1

        new_techniques = current_techniques - seen_techniques
        has_new_techniques = len(new_techniques) > 0

        if config_attack_counter >= config.min_num_of_attacks_reconfig and not has_new_techniques:
            print(f"Reconfiguring: No new techniques found after {config_attack_counter} attacks.")

            if not config.simulate_command_line:
                stop_dockers()

            config_id, honeypot_config = generate_new_honeypot_config(base_path)
            set_honeypot_config(honeypot_config)

            config_counter += 1
            config_attack_counter = 0
            print(f"Configuration {config_counter}")
            config_path = base_path / f"hp_config_{config_counter}"
            full_logs_path = config_path / "full_logs"
            os.makedirs(full_logs_path, exist_ok=True)

            if config.save_configuration:
                save_json_to_file(honeypot_config, config_path / f"honeypot_config.json")

            if not config.simulate_command_line:
                start_dockers()

        seen_techniques.update(current_techniques)

        print("\n\n")

if __name__ == "__main__":
    main()

# %%
