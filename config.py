# %%
from Red.model import LLMModel

experiment_name = ""

llm_model_sangria = LLMModel.GPT_4O_MINI
llm_model_config = LLMModel.GPT_4O_MINI
simulate_command_line = False
save_logs = True
save_configuration = True
print_output = True
n_configurations = 1
attacks_per_configuration = 25
max_session_length = 50

honeypot = "beelzebub" # beelzebub / cowrie

ISO_FORMAT = "%Y-%m-%dT%H_%M_%S"

# %%
