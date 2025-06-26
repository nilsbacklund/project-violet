from dotenv import load_dotenv
from pathlib import Path
import os
import openai
import pandas as pd
import json
import re
import ast
import math

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

BASE_DIR = Path(__file__).resolve().parent

data_path = BASE_DIR.parent / "LLM_labeler" / "data"

def query_openai(prompt: str, model: str = "gpt-4.1-mini", temperature: float = 0.7, max_tokens=32768):
    openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
    response = openai_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=temperature,
        max_tokens=max_tokens,
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
    pattern = re.compile(r"<labels>\s*(.*?)\s*</labels>", re.DOTALL)
    all_matches = pattern.findall(text)
    if not all_matches:
        raise ValueError("No output <labels>...</labels> found!")
    
    last_content = all_matches[-1]
    return last_content

def main():
    # Simple read (auto‐detects engine: 'pyarrow' or 'fastparquet')
    columns = ["session", "labels", "session_expanded", "labels_expanded"]
    df_train = pd.read_parquet(data_path / "sample_train_corpus_expanded.parquet", columns=columns)
    df_test = pd.read_parquet(data_path / "sample_test_corpus_expanded.parquet", columns=columns)

    train_list = df_train.to_dict(orient="records")
    test_list  = df_test.to_dict(orient="records")
    test_predicted_labels = []

    prompt = f"""
You are a cybersecurity analyst specialized in identifying attacker behavior from shell commands.
Your task: Analyze a session and classify it by MITRE ATT&CK tactics.
There are seven tactics: Execution, Persistence, Discovery, Impact, Defense Evasion, Harmless and Other.
These tactics are tied to sequences of individual commands which are separated by the token <sep>

You will predict the labels of the session enclosed in the tags <session></session>.
You must do some text based analysis before your final prediction.
Your predicted labels at the end must be enclosed in the tags <labels></labels>.

Training examples:
{json.dumps(train_list, indent=2, ensure_ascii=False)}
"""
    for i, row in enumerate(test_list):
        print(f"Processing test session: {i + 1} / {len(test_list)}")
        session = row["session_expanded"]
        true_labels = row["labels"]
        rows_prompt = prompt + f"""

You will predict the labels of the session enclosed in the tags <session></session>.

<session>
{session}
</session>

You must do some text based analysis before your final prediction.
Your predicted labels at the end should be output as a single string (with tactics separated by - ) that must be enclosed in the tags <labels></labels>.
Example output:
<labels>Execution - Execution - Discovery - Discovery - Discovery - Other - Other - Persistence - Persistence - Execution</labels>
"""
        message, usage = query_openai(rows_prompt)
        predicted_labels = extract_labels(message)

        # print("\t(Debug) Message:", message)
        print("\tPredicted labels:", predicted_labels)
        print("\tTrue labels:", true_labels)
        
        print(f"\tPrompt tokens:     {usage.prompt_tokens}")
        print(f"\tCompletion tokens: {usage.completion_tokens}")
        print(f"\tTotal tokens:      {usage.total_tokens}")
        input_token_cost = usage.prompt_tokens / 1_000_000 * 0.4
        output_token_cost = usage.completion_tokens / 1_000_000 * 1.6
        print(f"\tCost: ${input_token_cost + output_token_cost}")
        test_predicted_labels.append(predicted_labels)
        print(f"(Debug) Number of predicted labels: {len(test_predicted_labels)}")
        print()

    df_test_predictions = df_test.copy()
    df_test_predictions["labels_predicted"] = test_predicted_labels

    output_file = data_path / "sample_test_corpus_predictions.json"
    df_test_predictions.to_json(
        output_file,
        orient="records",    # list of dicts, one per row
        indent=4,            # pretty-print with 2-space indentation
        force_ascii=False    # allow Unicode if any
    )
    print(f"Saved predictions to {output_file}")

if __name__ == "__main__":
    main()