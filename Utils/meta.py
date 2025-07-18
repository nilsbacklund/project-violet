import config
import datetime
import os
import json
from Red.reconfiguration import EntropyReconfigCriterion, BasicReconfigCriterion, \
    MeanIncreaseReconfigCriterion, NeverReconfigCriterion
from Red.model import ReconfigCriteria

def create_experiment_folder(experiment_name=None):
    # timestamp = datetime.datetime.now().isoformat()[:-7]
    timestamp = datetime.datetime.now().strftime(config.ISO_FORMAT)

    folder_name = f"experiment_{timestamp}"
    if experiment_name:
        folder_name = f"{experiment_name}_{timestamp}"

    # create the logs folder if it doesn't exist
    path = "logs/" + folder_name

    os.makedirs("logs", exist_ok=True)
    os.makedirs(path, exist_ok=True)

    metadata = create_metadata()
    metadata_path = os.path.join(path, "metadata.json")

    with open(metadata_path, 'w') as f:
        json.dump(metadata.to_dict(), f, indent=2)
        print(f"Metadata saved to {metadata_path}")

    return path

class MetaDataObject:
    def __init__(self, llm_model_sangria, llm_model_honeypot, num_of_attacks, min_num_of_attacks_reconfig, max_session_length, reconfig_method):
        self.llm_model_sangria = llm_model_sangria
        self.llm_model_honeypot = llm_model_honeypot
        self.num_of_attacks = num_of_attacks
        self.min_num_of_attacks_reconfig = min_num_of_attacks_reconfig
        self.max_session_length = max_session_length
        self.reconfig_method = reconfig_method

    def to_dict(self):
        return {
            "llm_model_sangria": self.llm_model_sangria,
            "llm_model_honeypot": self.llm_model_honeypot,
            "num_of_attacks": self.num_of_attacks,
            "min_num_of_attacks_reconfig": self.min_num_of_attacks_reconfig,
            "max_session_length": self.max_session_length,
            "reconfig_method": self.reconfig_method
        }

def create_metadata():
    md = MetaDataObject(
        llm_model_sangria=config.llm_model_sangria,
        llm_model_honeypot=config.llm_model_config,
        num_of_attacks=config.num_of_attacks,
        min_num_of_attacks_reconfig=config.min_num_of_attacks_reconfig,
        max_session_length=config.max_session_length,
        reconfig_method=config.reconfig_method
    )

    return md

def select_reconfigurator(reconfigurator_method: ReconfigCriteria):
    match reconfigurator_method:
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
        
    return reconfigurator
