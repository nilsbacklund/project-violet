# %%
from config import attacks_per_configuration, save_logs, n_configurations
from Red.sangria import run_attacks, save_logs_to_file
from Red.log_formatter import format_logs_to_lables, save_labels
from Blue.new_config_pipeline import generate_new_honeypot_config, save_config_as_file, get_base_config, set_honeypot_config


def main():
    base_honeypot_config = get_base_config(id=00)
    set_honeypot_config(base_honeypot_config)

    for i in range(n_configurations):
        print(f"Iteration {i + 1} / 10")
        
        if i != 0:
            config_id, new_config = generate_new_honeypot_config()
            set_honeypot_config(new_config)

        full_logs = run_attacks(n_attacks=attacks_per_configuration, save_logs=save_logs)
        if not full_logs:
            continue

        save_logs_to_file(full_logs, config_id, save_logs)
        save_config_as_file(new_config)

        lables = format_logs_to_lables(full_logs)
        save_labels(lables, config_id)


if __name__ == "__main__":
    main()

# %%
