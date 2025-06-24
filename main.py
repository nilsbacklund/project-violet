# %%
from config import attacks_per_configuration, save_logs, n_configurations
from Red.sangria import run_attacks, save_logs_to_file
from Red.log_formatter import format_logs_to_lables, save_labels
from Blue.new_config_pipeline import generate_new_honeypot_config, save_config_as_file, get_honeypot_config, set_honeypot_config
from Blue_Lagoon.honeypot_tools import start_dockers, stop_dockers, init_docker

def main():
    config_id = "00"
    honeypot_config = get_honeypot_config(id=config_id)
    set_honeypot_config(honeypot_config)
    init_docker()
    start_dockers()

    for i in range(n_configurations):
        print(f"Configuration Iteration {i + 1} / {n_configurations}")
        
        if i != 0:
            stop_dockers()
            config_id, honeypot_config = generate_new_honeypot_config()
            set_honeypot_config(honeypot_config)
            start_dockers()

        # Run attacks and save logs
        full_logs = run_attacks(attacks_per_configuration, save_logs, config_id)
        if not full_logs:
            continue

        
        save_config_as_file(honeypot_config)

        # lables = format_logs_to_lables(full_logs, config_id)
        # save_labels(lables, config_id)

    stop_dockers()

if __name__ == "__main__":
    main()

# %%
