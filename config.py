# %%
from Red.model import LLMModel

# Configuration for model selection and behavior
# 
# Model Recommendations:
# - O3_MINI: Best for reasoning-heavy tasks (attack planning, config generation)
# - O4_MINI: Optimized for speed and cost efficiency  
# - GPT_4_1_MINI: Reliable fallback option, good balance of cost and performance
#
# Model Behavior Notes:
# - o-series models: More step-by-step reasoning, longer response times
# - GPT-4.1 series: Faster responses, good for iterative testing
# - All models support function calling and tool use

experiment_name = ""

# Primary model for attack simulation (reasoning-heavy)
# Switch between these options as needed:
llm_model_sangria = LLMModel.O4_MINI        # Current: Advanced reasoning
# llm_model_sangria = LLMModel.GPT_4_1_MINI   # Alternative: Faster, reliable

# Model for configuration generation (structured output)
llm_model_config = LLMModel.O4_MINI         # Current: Advanced reasoning
# llm_model_config = LLMModel.GPT_4_1_MINI    # Alternative: Faster, reliable

simulate_command_line = True
save_logs = True
save_configuration = True
print_output = True
n_configurations = 1
attacks_per_configuration = 25
max_session_length = 5

honeypot = "beelzebub" # beelzebub / cowrie

# %%
