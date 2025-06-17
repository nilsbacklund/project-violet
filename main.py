# %%
import uuid
from config import attacks_per_configuration, save_logs, n_configurations
from Red.sangria import run_attacks, save_logs_to_file

def main():
    base_honeypot_config = get_base_config(id=None)
    set_honeypot_config(base_honeypot_config)

    for i in range(n_configurations):
        print(f"Iteration {i + 1} / 10")
        session_id = uuid.uuid4()
        
        if i != 0:
            new_config = generate_new_honeypot_config()
            set_honeypot_config(new_config)

        full_logs = run_attacks(n_attacks=attacks_per_configuration, save_logs=save_logs)
        if not full_logs:
            continue
        save_logs_to_file(full_logs, session_id, save_logs)

        format_logs_for_network(full_logs, session_id)

        save_configuration(new_config)
        save_labels()


if __name__ == "__main__":
    main()

# %%
