# %%
from config import attacks_per_configuration, save_logs

def main():
    base_honeypot_config = get_base_config(id=None)
    set_honeypot_config(base_honeypot_config)

    for i in range(10):
        print(f"Iteration {i + 1} / 10")
        
        if i != 0:
            new_config = generate_new_honeypot_config()
            set_honeypot_config(new_config)

        run_attacks(n_attacks=attacks_per_configuration, save_logs=save_logs)

        format_logs_for_network()

        save_configuration(new_config)
        save_labels()


if __name__ == "__main__":
    main()
