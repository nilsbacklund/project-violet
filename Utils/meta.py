import config
import Red.sangria_config as sangria_config
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
        n_configurations=config.n_configurations,
        attacks_per_configuration=config.attacks_per_configuration,
        max_session_length=config.max_session_length,
        save_logs=config.save_logs,
        honeypot=config.honeypot,
        system_prompt=sangria_config.attacker_prompt,
    )

    return md
    

class MetaDataObject:
    def __init__(self, llm_model_sangria, llm_model_honeypot, n_configurations, attacks_per_configuration, max_session_length, save_logs, honeypot, system_prompt):
        self.llm_model_sangria = llm_model_sangria
        self.llm_model_honeypot = llm_model_honeypot
        self.n_configurations = n_configurations
        self.attacks_per_configuration = attacks_per_configuration
        self.max_session_length = max_session_length
        self.save_logs = save_logs
        self.honeypot = honeypot
        self.system_prompt = system_prompt

    def to_dict(self):
        return {
            "llm_model_sangria": self.llm_model_sangria,
            "llm_model_honeypot": self.llm_model_honeypot,
            "n_configurations": self.n_configurations,
            "attacks_per_configuration": self.attacks_per_configuration,
            "max_session_length": self.max_session_length,
            "save_logs": self.save_logs,
            "honeypot": self.honeypot,
            "system_prompt": self.system_prompt
        }
