import json
from pathlib import Path

def calculate_experiment_price(log_path):
    """
    Calculate the price of the last experiment based on token usage and pricing.

    Pricing:
    - Input tokens: $0.10 per 1M tokens
    - Cached tokens: $0.025 per 1M tokens
    - Output tokens: $0.40 per 1M tokens

    Args:
        log_path (str): Path to the tokens_used.json file.

    Returns:
        float: Total price of the experiment.
    """
    with open(log_path, 'r', encoding='utf-8') as f:
        token_data = json.load(f)

    total_prompt_tokens = sum(entry["prompt_tokens"] for entry in token_data)
    total_completion_tokens = sum(entry["completion_tokens"] for entry in token_data)
    total_cached_tokens = sum(entry["cached_tokens"] for entry in token_data)

    input_cost = total_prompt_tokens / 1_000_000 * 0.4
    cached_cost = total_cached_tokens / 1_000_000 * 0.1
    output_cost = total_completion_tokens / 1_000_000 * 1.6

    total_cost = input_cost + cached_cost + output_cost
    return total_cost

# Example usage:
log_file_path = "/home/daniel/l/AISweden/project-violet/logs/experiment_2025-07-08T13_05_20/hp_config_1/tokens_used.json"
price = calculate_experiment_price(log_file_path)
print(f"Total price of the experiment: ${price:.2f}")