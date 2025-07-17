# %%
from Red.model import LLMModel, ReconfigCriteria
from Red.attacker_prompts import AttackerPrompts

experiment_name = ""

# Experiment settings
llm_model_sangria = LLMModel.O4_MINI
llm_model_config = LLMModel.GPT_4_1_MINI
attacker_prompt: str = AttackerPrompts.CYCLE
reconfig_method: ReconfigCriteria = ReconfigCriteria.BASIC

# General settings
simulate_command_line = False
save_logs = True
save_configuration = True
print_output = True

# Session settings
num_of_attacks = 100
min_num_of_attacks_reconfig = 0
max_session_length = 100

# Reconfiguration settings 
reset_every_reconfig = True
## Basic reconfiguration
interval: int = 1
## Mean increase reconfiguration
fd_variable: str = "techniques"
fd_tolerance: float = 0.5
fd_window_size: int = 5
fd_reset_techniques: bool = True
## Entropy reconfiguration
en_variable: str = "techniques"
en_tolerance: float = 1e-2

# Other
ISO_FORMAT = "%Y-%m-%dT%H_%M_%S"

# %%
