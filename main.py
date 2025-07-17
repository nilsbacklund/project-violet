# %%
import json
from dotenv import load_dotenv
load_dotenv()
import os
import config
from pathlib import Path

from Red import sangria_config
from Red.sangria import run_single_attack
from Red.model import ReconfigCriteria
from Red.extraction import extract_session
from Red.reconfiguration import EntropyReconfigCriterion, BasicReconfigCriterion, \
    MeanIncreaseReconfigCriterion, NeverReconfigCriterion

from Blue.new_config_pipeline import generate_new_honeypot_config, get_honeypot_config, set_honeypot_config
from Blue_Lagoon.honeypot_tools import init_docker, start_dockers, stop_dockers

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

    match config.reconfig_method:
        case ReconfigCriteria.NO_RECONFIG:
            reconfigurator = NeverReconfigCriterion(
                    config.reset_every_reconfig
                )
        case ReconfigCriteria.BASIC:
            reconfigurator = BasicReconfigCriterion(
                    config.interval,
                    config.reset_every_reconfig
                )
        case ReconfigCriteria.MEAN_INCREASE:
            reconfigurator = MeanIncreaseReconfigCriterion(
                    config.mi_variable,
                    config.mi_tolerance,
                    config.mi_window_size,
                    config.mi_reset_techniques,
                    config.reset_every_reconfig
                )
        case ReconfigCriteria.ENTROPY:
            reconfigurator = EntropyReconfigCriterion(
                    config.en_variable,
                    config.en_tolerance,
                    config.en_window_size,
                    config.reset_every_reconfig
                )
        case _:
            raise ValueError(f"The reconfiguration criterion {config.reconfig_method} is not supported.")
    reconfigurator.reset()

    if not config.simulate_command_line:
        start_dockers()

    tokens_used_list = []
    BOLD   = "\033[1m"
    RESET  = "\033[0m"
    print(f"{BOLD}New Configuration: configuration {config_counter}{RESET}")
    config_path = base_path / f"hp_config_{config_counter}"
    full_logs_path = config_path / "full_logs"
    os.makedirs(full_logs_path, exist_ok=True)

    if config.save_configuration and not config.simulate_command_line:
        save_json_to_file(honeypot_config, config_path / f"honeypot_config.json")

    for i in range(config.num_of_attacks):
        if config.save_logs:
            os.makedirs(config_path, exist_ok=True)

        print(f"{BOLD}Attack {i+1} / {config.num_of_attacks}, configuration {config_counter}{RESET}")
        logs_path = full_logs_path / f"attack_{i+1}.json"

        messages = sangria_config.get_messages(i)

        logs, tokens_used = run_single_attack(messages, config.max_session_length, logs_path, i, config_counter)

        if config.save_logs:
            # save logs
            # save_json_to_file(logs, full_logs_path / f"attack_{i+1}.json")
            # update tokens used
            append_json_to_file(tokens_used, config_path / f"tokens_used.json", False)

        # append tokens
        tokens_used_list.append(tokens_used)

        # extract session and add attack pattern to set
        session = extract_session(logs)
        reconfigurator.update(session)

        if config.save_logs:
            append_json_to_file(session, config_path / f"sessions.json", False)

        if (config_attack_counter >= config.min_num_of_attacks_reconfig) \
                and reconfigurator.should_reconfigure():
            
            BOLD   = "\033[1m"
            RESET  = "\033[0m"
            print(f"{BOLD}Reconfiguring: Using {config.reconfig_method}.{RESET}")
            if not config.simulate_command_line:
                stop_dockers()

            config_id, honeypot_config = generate_new_honeypot_config(base_path)
            set_honeypot_config(honeypot_config)

            if reconfigurator.reset_every_reconfig:
                reconfigurator.reset()

            config_counter += 1
            config_attack_counter = 0

            config_path = base_path / f"hp_config_{config_counter}"
            full_logs_path = config_path / "full_logs"
            os.makedirs(full_logs_path, exist_ok=True)

            if config.save_configuration:
                save_json_to_file(honeypot_config, config_path / f"honeypot_config.json")

            if not config.simulate_command_line:
                start_dockers()

        print("\n\n")

if __name__ == "__main__":
    main()

# %%
