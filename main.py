# %%
from config import attacks_per_configuration, save_logs, n_configurations, save_configuration, experiment_name
from Red.sangria import run_attacks
from Red.log_formatter import format_logs_to_lables, save_labels
from Blue.new_config_pipeline import generate_new_honeypot_config, save_config_as_file, get_honeypot_config, set_honeypot_config
from Blue_Lagoon.honeypot_tools import init_docker
from Utils import create_experiment_folder, save_json_to_file
import datetime
import os
import shutil 

def main():
    base_path = create_experiment_folder(save_logs, experiment_name=experiment_name)

    honeypot_config = get_honeypot_config(id="00")
    set_honeypot_config(honeypot_config)
    init_docker()

    for i in range(n_configurations):
        print(f"Configuration Iteration {i + 1} / {n_configurations}")
        config_path = f"{base_path}/hp_config_{i+1}"
        if save_logs:
            os.makedirs(config_path, exist_ok=True) 

        
        if i != 0:
            config_id, honeypot_config = generate_new_honeypot_config()
            set_honeypot_config(honeypot_config)

        if save_configuration:
            save_json_to_file(honeypot_config, f"{config_path}/honeypot_config.json", save_logs)

        # Run attacks and save logs
        run_attacks(attacks_per_configuration, save_logs, f"{config_path}/")
        if save_configuration:
            save_config_as_file(honeypot_config, config_path)
            save_json_to_file(honeypot_config.to_dict(), f"{config_path}/honeypot_config.json", save_logs)


if __name__ == "__main__":
    main()

# %%
