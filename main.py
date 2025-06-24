# %%
from config import attacks_per_configuration, save_logs, n_configurations, save_configuration
from Red.sangria import run_attacks, save_logs_to_file
from Red.log_formatter import format_logs_to_lables, save_labels
from Blue.new_config_pipeline import generate_new_honeypot_config, save_config_as_file, get_honeypot_config, set_honeypot_config
from Blue_Lagoon.honeypot_tools import init_docker
import datetime
import os
import shutil 

def main():
    path = "logs/full_logs/" + datetime.datetime.now().isoformat()[:-7]
    if save_logs:
        os.makedirs(path, exist_ok=True)
        shutil.copy("config.py", path)

    honeypot_config = get_honeypot_config(id="00")
    set_honeypot_config(honeypot_config)
    init_docker()

    for i in range(n_configurations):
        print(f"Configuration Iteration {i + 1} / {n_configurations}")
        if save_logs:
            os.makedirs(f"{path}/hp_config_{i+1}", exist_ok=True) 

        
        if i != 0:
            config_id, honeypot_config = generate_new_honeypot_config()
            set_honeypot_config(honeypot_config)

        # Run attacks and save logs
        run_attacks(attacks_per_configuration, save_logs, f"{path}/hp_config_{i+1}/")
        if save_configuration:
            save_config_as_file(honeypot_config)


if __name__ == "__main__":
    main()

# %%
