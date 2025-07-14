# %%
from Red.model import LLMModel, ReconfigMethod
from Red.attacker_prompts import AttackerPrompts

experiment_name = ""

llm_model_sangria = LLMModel.GPT_4_1_MINI
llm_model_config = LLMModel.GPT_4_1_MINI
attacker_prompt: str = AttackerPrompts.GENERAL
reconfig_method: str = ReconfigMethod.NEW_TECHNIQUES # Not implemented yet

simulate_command_line = False
save_logs = True
save_configuration = True
print_output = True
num_of_attacks = 100
min_num_of_attacks_reconfig = 2
max_session_length = 100

honeypot = "beelzebub" # beelzebub / cowrie

ISO_FORMAT = "%Y-%m-%dT%H_%M_%S"

# %%
