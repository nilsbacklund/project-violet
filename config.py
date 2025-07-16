# %%
from Red.model import LLMModel, ReconfigMethod
from Red.attacker_prompts import AttackerPrompts

experiment_name = ""

# Experiment settings
llm_model_sangria = LLMModel.O4_MINI
llm_model_config = LLMModel.GPT_4_1_MINI
reconfig_method: str = ReconfigMethod.NEW_TECHNIQUES

# Reconfiguration settings
n_attacks = 20 # only relevant for EVERY_N_ATTACKS
n_config_window_size = 5 # only relevant for NEW_TECHNIQUES
saturation_limit = 0.5 # only relevant for NEW_TECHNIQUES

# Ending configs for NO_RECONFIG
end_window_size = 20
end_saturation_limit = 0.06

# General settings
simulate_command_line = False
save_logs = True
save_configuration = True
print_output = True

# Session settings
num_of_attacks = 100
min_num_of_attacks_reconfig = 2
max_session_length = 100

# Other
ISO_FORMAT = "%Y-%m-%dT%H_%M_%S"

# %%
