from dotenv import load_dotenv
from pathlib import Path
import os
import pandas as pd
import json
from Utils.logprecis import expand_labels, divide_statements

load_dotenv()
OPENAI_API_KEY= os.getenv("OPENAI_API_KEY")

BASE_DIR = Path(__file__).resolve().parent

data_path = BASE_DIR.parent / "LLM_labeler" / "data"

def main():
    columns = ["session", "labels"]

    for name in ("train", "test"):
        df  = pd.read_parquet(data_path / f"sample_{name}_corpus.parquet",  columns=columns)
        data = []
        for i in range(len(df)):
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