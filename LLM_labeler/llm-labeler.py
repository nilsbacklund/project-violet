import os
import openai
from dotenv import load_dotenv
from pathlib import Path
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
    # convert from Python-literal string to actual object
    return ast.literal_eval(last_content)

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

You will predict the labels of the sessions enclosed in the tags <sessions></sessions>.
You must do some text based analysis before your final prediction.
Your predicted labels at the end must be enclosed in the tags <labels></labels>.

Training examples:
{json.dumps(train_list, indent=2, ensure_ascii=False)}
"""
    batch_size = 8
    number_of_batches = math.ceil(len(test_list) / batch_size)
    for i in range(number_of_batches):
        print(f"Processing test batch: {i + 1} / {number_of_batches}")
        rows = test_list[i*batch_size:(i+1)*batch_size]
        sessions = list(map(lambda row: { "session" : row["session_expanded"] }, rows))
        rows_prompt = prompt + f"""

You will predict the labels of the session enclosed in the tags <session></session>.

<sessions>
{json.dumps(sessions, indent=4)}
</sessions>

You must do some text based analysis before your final prediction.
Your predicted labels at the end should be output as a single Python list that must be enclosed in the tags <labels></labels>.
Example output:
<labels>["Execution - Execution - Discovery - Discovery - Discovery, "Other - Other", "Persistence - Persistence - Execution"]</labels>
"""
        message, usage = query_openai(rows_prompt)
        print(message)
        predicted_labels = extract_labels(message)

        print(f"\tPrompt tokens:     {usage.prompt_tokens}")
        print(f"\tCompletion tokens: {usage.completion_tokens}")
        print(f"\tTotal tokens:      {usage.total_tokens}\n")
        input_token_cost = usage.prompt_tokens / 1_000_000 * 0.4
        output_token_cost = usage.completion_tokens / 1_000_000 * 1.6
        print(f"\tCost: ${input_token_cost + output_token_cost}")
        
        test_predicted_labels.extend(predicted_labels)
        print(len(predicted_labels))
        print(len(test_predicted_labels))

    print(test_predicted_labels)
    print(type(test_predicted_labels))
    print(len(test_predicted_labels))
    df_test_predictions = df_test.copy()
    df_test_predictions["labels_predicted"] = test_predicted_labels

    print(df_test_predictions)

    # Save the updated test set as a parquet file
    output_file = data_path / "sample_test_corpus_predictions.parquet"
    df_test_predictions.to_parquet(output_file, index=False)
    print(f"Saved predictions to {output_file}")

if __name__ == "__main__":
    main()