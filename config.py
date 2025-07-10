# %%
from Red.model import LLMModel

experiment_name = ""

llm_model_sangria = LLMModel.GPT_4_1_MINI
llm_model_config = LLMModel.GPT_4_1_MINI
simulate_command_line = False
save_logs = True
save_configuration = True
print_output = True
num_of_attacks = 100
min_num_of_attacks_reconfig = 10
max_session_length = 100

honeypot = "beelzebub" # beelzebub / cowrie

ISO_FORMAT = "%Y-%m-%dT%H_%M_%S"

# %%
