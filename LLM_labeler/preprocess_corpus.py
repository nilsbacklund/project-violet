from dotenv import load_dotenv
from pathlib import Path
import os
import pandas as pd
import re
import json

load_dotenv()
OPENAI_API_KEY= os.getenv("OPENAI_API_KEY")

BASE_DIR = Path(__file__).resolve().parent

data_path = BASE_DIR.parent / "LLM_labeler" / "data"

def divide_statements(session, add_special_token=False, special_token="[STAT]"):
    """Divide a session into statements.
    This function splits a session into statements using specified separators. Optionally,
    it adds a special token at the beginning of each statement.
    Args:
        session (str): The session to be divided into statements.
        add_special_token (bool): Whether to add a special token to each statement.
        special_token (str, optional): The special token to be added. Defaults to "[STAT]".
    Returns:
        list of str: A list of statements.
    """
    statements = re.split(r"(; |\|\|? |&& )", session + " ")
    # concatenate with separators
    if len(statements) != 1:
        statements = [
            "".join(statements[i : i + 2]).strip()
            for i in range(0, len(statements) - 1, 2)
        ]
    else:  # cases in which there is only 1 statement > must end with " ;"
        statements = [statements[0].strip() + " ;"]
    if add_special_token:
        # Add separator
        statements = [f"{special_token} " + el for el in statements]
    return statements

def expand_labels(labels):
    """Expand abbreviated labels to statement labels.
    This function expands abbreviated labels to 1 label per statement based on the provided input.
    Args:
        labels (str): The labels separated by '--' with index information.
    Returns:
        list of str: A list of expanded labels.
    """
    labels = labels.split(" -- ")
    statement_labels = []
    prev_index = 0
    for label in labels:
        label, index = label.split(" - ")
        index = int(index)
        for _ in range(index - prev_index + 1):
            statement_labels.append(label.strip())
        prev_index = index + 1
    return statement_labels

def main():
    columns = ["session", "labels"]

    for name in ("train", "test"):
        df  = pd.read_parquet(data_path / f"sample_{name}_corpus.parquet",  columns=columns)
        data = []
        for i in range(51,len(df)):
            session = df["session"].loc[i]
            labels = df["labels"].loc[i]
            commands_split = divide_statements(session, False)
            labels_split = expand_labels(labels)
            assert len(commands_split) == len(labels_split)
            data.append({
                "session": session,
                "labels": labels,
                "full_session": [
                    { "command" : command, "label" : label} for command, label in zip(commands_split, labels_split)
                ]
            })

            with open(data_path / f"sample_{name}_corpus_expanded.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()