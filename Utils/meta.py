import config
import datetime
import os
import json

def create_experiment_folder(save_logs=True, experiment_name=None):
    if not save_logs:
        print("Logs saving is disabled. No folder will be created.")
        return
    
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

def create_metadata():
    md = MetaDataObject(
        llm_model_sangria=config.llm_model_sangria,
        llm_model_honeypot=config.llm_model_config,
        num_of_attacks=config.num_of_attacks,
        min_num_of_attacks_reconfig=config.min_num_of_attacks_reconfig,
        max_session_length=config.max_session_length,
        save_logs=config.save_logs,
        system_prompt=config.attacker_prompt,
        reconfig_method=config.reconfig_method
    )

    return md
    

class MetaDataObject:
    def __init__(self, llm_model_sangria, llm_model_honeypot, num_of_attacks, min_num_of_attacks_reconfig, max_session_length, save_logs, system_prompt, reconfig_method):
        self.llm_model_sangria = llm_model_sangria
        self.llm_model_honeypot = llm_model_honeypot
        self.num_of_attacks = num_of_attacks
        self.min_num_of_attacks_reconfig = min_num_of_attacks_reconfig
        self.max_session_length = max_session_length
        self.save_logs = save_logs
        self.system_prompt = system_prompt
        self.reconfig_method = reconfig_method

    def to_dict(self):
        return {
            "llm_model_sangria": self.llm_model_sangria,
            "llm_model_honeypot": self.llm_model_honeypot,
            "num_of_attacks": self.num_of_attacks,
            "min_num_of_attacks_reconfig": self.min_num_of_attacks_reconfig,
            "max_session_length": self.max_session_length,
            "save_logs": self.save_logs,
            "system_prompt": self.system_prompt,
            "reconfig_method": self.reconfig_method
        }
