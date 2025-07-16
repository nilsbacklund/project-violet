# %%
from Red.model import LLMModel, ReconfigCriteria
from Red.attacker_prompts import AttackerPrompts

experiment_name = ""

# Experiment settings
llm_model_sangria = LLMModel.O4_MINI
llm_model_config = LLMModel.GPT_4_1_MINI
attacker_prompt: str = AttackerPrompts.GENERAL
reconfig_method: ReconfigCriteria = ReconfigCriteria.BASIC

# General settings
simulate_command_line = False
save_logs = True
save_configuration = True
print_output = True

# Session settings
num_of_attacks = 100
min_num_of_attacks_reconfig = 2
max_session_length = 100

# Reconfiguration settings 
reset_every_reconfig = True
## Basic reconfiguration
interval: int = 20
## Mean increase reconfiguration
fd_variable = "techniques"
fd_tolerance = 0.5
fd_window_size = 5
fd_reset_techniques = True
## Entropy reconfiguration
en_variable = "techniques"
en_tolerance = 1e-2

# Other
ISO_FORMAT = "%Y-%m-%dT%H_%M_%S"

# %%
