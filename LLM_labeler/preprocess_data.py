import os
from dotenv import load_dotenv
import os
import pandas as pd
from pathlib import Path

load_dotenv()
OPENAI_API_KEY= os.getenv("OPENAI_API_KEY")

BASE_DIR = Path(__file__).resolve().parent

data_path = BASE_DIR.parent / "LLM_labeler" / "data"

def split_session_into_commands(text):
    # Normalize separators to semicolons and split into fragments
    commands = [c.strip() for c in text.replace(" | ", " ; ")
                .replace(" || ", " ; ")
                .replace(" && ", " ; ")
                .replace(';', " ; ")
                .split(" ; ")]

    return " <sep> ".join(commands)

def expand_counts(s: str) -> str:
    segments = s.split("--")
    results = []
    first_segment = True
    previous_index = 0
    for segment in segments:
        tactic, index = segment.split("-")
        tactic = tactic.strip()
        index = int(index.strip())
        length = index - previous_index
        if first_segment:
            length += 1
            first_segment = False
        previous_index = index
        results.extend([tactic] * length)
    results = " - ".join(results)
    return results

def main():
    columns = ["session", "labels"]
    df_train = pd.read_parquet(data_path / "sample_train_corpus.parquet", columns=columns)
    df_test  = pd.read_parquet(data_path / "sample_test_corpus.parquet",  columns=columns)

    for df in (df_train, df_test):
        df['session_expanded'] = df['session'].apply(split_session_into_commands)
        df['labels_expanded']  = df['labels'].apply(expand_counts)

    df_train.to_parquet(data_path / "sample_train_corpus_expanded.parquet", index=False)
    df_test .to_parquet(data_path / "sample_test_corpus_expanded.parquet",  index=False)

    with pd.option_context(
        'display.max_rows', None,
        'display.max_columns', None,
        'display.width', None,
    ):
        print("Training samples:\n", df_train)
        print("Test samples:\n", df_test)

if __name__ == "__main__":
    main()