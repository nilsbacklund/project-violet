# %%
from Red.model import LLMModel

llm_model = LLMModel.GPT_4O_MINI
simulate_command_line = True
save_logs = True
save_configuration = True
print_output = True

attacks_per_configuration = 10

# %%
if simulate_command_line:
    save_logs = False
    