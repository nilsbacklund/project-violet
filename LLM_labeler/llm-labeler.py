from dotenv import load_dotenv
from pathlib import Path
import os
import openai
import pandas as pd
import json
import re

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

BASE_DIR = Path(__file__).resolve().parent

data_path = BASE_DIR.parent / "LLM_labeler" / "data"

def query_openai(prompt: str, model: str = "o1-mini", temperature: float = 0.7, max_tokens=65536):
    openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
    response = openai_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=1,
        max_completion_tokens=max_tokens,
        stream=False,
    )
    message = response.choices[0].message.content.strip()
    usage = response.usage
    return message, usage

def extract_labels(text: str) -> str | None:
    """
    Extracts and returns the content inside the *last* <labels>...</labels> from the given text.
    If no such tags are found, raises ValueError.
    """
    # findall returns a list of all the captured groups
    pattern = re.compile(r"<output>\s*(.*?)\s*</output>", re.DOTALL)
    all_matches = pattern.findall(text)
    if not all_matches:
        raise ValueError("No output <labels>...</labels> found!")
    
    last_content = all_matches[-1]
    return last_content

def main():
    with open(data_path / "sample_train_corpus_expanded.json", "r", encoding="utf8") as f:
        train_data = json.load(f)
        
    with open(data_path / "sample_test_corpus_expanded.json", "r", encoding="utf8") as f:
        test_data = json.load(f)

    clean_train_data = [{"session": row["session"], "full_session": row["full_session"]} for row in train_data]
    clean_test_data = []

    for i, row in enumerate(test_data):
        clean_test_data.append({
            "session": row["session"],
            "full_session": [
                {
                    "command": statement["command"],
                    "label": None,
                }
                for statement in row["full_session"]
            ]
        })

    prompt = f"""
You are a cybersecurity analyst specialized in identifying attacker behavior from shell commands.
Your task: Analyze sessions and classify it by MITRE ATT&CK tactics.
There are seven tactics: Execution, Persistence, Discovery, Impact, Defense Evasion, Harmless and Other.

You will predict the labels of the sessions enclosed in the tags <sessions></sessions>.
You must do some text based analysis before your final prediction.

Training examples:
{json.dumps(clean_train_data[:70], indent=2, ensure_ascii=False)}
"""
#     prompt = """
# You are a cybersecurity analyst specialized in identifying attacker behavior from shell commands.
# Your task: Analyze sessions and classify it by MITRE ATT&CK tactics.
# There are seven tactics: Execution, Persistence, Discovery, Impact, Defense Evasion, Harmless and Other.

# You will predict the labels of the sessions enclosed in the tags <sessions></sessions>.
# You must do some text based analysis before your final prediction.

# Example sessions:
# [
#     {
#         "session": "<HERE THERE WILL BE SOME BASH COMMANDS>",
#         "labels": "Discovery - 1",
#         "full_session": [
#             {
#                 "command": "<HERE THERE WILL BE SOME BASH COMMANDS>",
#                 "label": "Discovery"
#             },
#             {
#                 "command": "<HERE THERE WILL BE SOME BASH COMMANDS>",
#                 "label": "Discovery"
#             }
#         ]
#     },
#     {
#         "session": "<HERE THERE WILL BE SOME BASH COMMANDS>",
#         "labels": "Discovery - 2",
#         "full_session": [
#             {
#                 "command": "<HERE THERE WILL BE SOME BASH COMMANDS>",
#                 "label": "Discovery"
#             },
#             {
#                 "command": "<HERE THERE WILL BE SOME BASH COMMANDS>",
#                 "label": "Discovery"
#             },
#             {
#                 "command": "<HERE THERE WILL BE SOME BASH COMMANDS>",
#                 "label": "Discovery"
#             }
#         ]
#     }
# ]
# """
    rows_prompt = prompt + f"""
You will predict the labels of the sessions enclosed in the tags <sessions></sessions>.

<sessions>
{json.dumps(clean_test_data, indent=2, ensure_ascii=False)}
</sessions>

You must do some text based analysis before your final prediction.
You will output the same JSON file as in the sessions-tags, but enclosed in <output></output> tags with your predicted labels.
Make sure you don't forget any session command and that every command has an associated label!
"""

    message, usage = query_openai(rows_prompt)
    predicted_labels = extract_labels(message)
    
    print(f"\tPrompt tokens:     {usage.prompt_tokens}")
    print(f"\tCompletion tokens: {usage.completion_tokens}")
    print(f"\tTotal tokens:      {usage.total_tokens}")
    input_token_cost = usage.prompt_tokens / 1_000_000 * 1.1
    output_token_cost = usage.completion_tokens / 1_000_000 * 4.4
    print(f"\tCost: ${input_token_cost + output_token_cost}")

    test_prediction_data = json.loads(predicted_labels)

    output_file = data_path / "sample_test_corpus_predictions.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(test_prediction_data, f, ensure_ascii=False, indent=2)
        print(f"Saved predictions to {output_file}")

if __name__ == "__main__":
    main()