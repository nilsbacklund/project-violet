# %%
import os
print(os.getcwd())
import config
from pathlib import Path
from Red.sangria import run_single_attack
from Blue.new_config_pipeline import generate_new_honeypot_config, get_honeypot_config, set_honeypot_config
from Blue_Lagoon.honeypot_tools import init_docker, start_dockers, stop_dockers
from Preprocessing.extraction import extract_session
from Utils.meta import create_experiment_folder
from Utils.jsun import save_json_to_file, append_json_to_file

def main():
    base_path = create_experiment_folder(config.save_logs, experiment_name=config.experiment_name)
    base_path = Path(base_path)

    honeypot_config = get_honeypot_config(id="00", path="")
    set_honeypot_config(honeypot_config)
    init_docker()

    config_counter = 1
    config_attack_counter = 0
    all_attack_patterns = set()

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
        logs, tokens_used = run_single_attack(config.save_logs, config.max_session_length)
        # append tokens
        tokens_used_list.append(tokens_used)

        # extract session and add attack pattern to set
        session = extract_session(logs)
        attack_pattern = session["labels"]
        print(f"Attack pattern: {attack_pattern}")

        if config.save_logs and not config.simulate_command_line:
            logs = [log.to_dict() for log in logs]
            # save logs
            save_json_to_file(logs, full_logs_path / f"attack_{i+1}.json")
            # update sessions
            append_json_to_file(session, config_path / f"sessions.json")
            # update tokens used
            append_json_to_file(tokens_used, config_path + f"tokens_used.json")

        config_attack_counter += 1
        if config_attack_counter >= config.min_num_of_attacks_reconfig and attack_pattern in all_attack_patterns:
            
            print(f"Reconfiguring: Found same attack ({attack_pattern}) after {config_attack_counter} attacks.")

            if not config.simulate_command_line:
                stop_dockers()

            config_id, honeypot_config = generate_new_honeypot_config()
            set_honeypot_config(honeypot_config)

            config_counter += 1
            config_attack_counter = 0
            print(f"Configuration {config_counter}")
            config_path = base_path / f"hp_config_{config_counter}"
            full_logs_path = config_path / "full_logs"
            os.makedirs(full_logs_path, exist_ok=True)

            if config.save_configuration and not config.simulate_command_line:
                save_json_to_file(honeypot_config, config_path / f"honeypot_config.json")

            if not config.simulate_command_line:
                start_dockers()

        all_attack_patterns.update(attack_pattern)

        print("\n\n")

if __name__ == "__main__":
    main()

# %%
