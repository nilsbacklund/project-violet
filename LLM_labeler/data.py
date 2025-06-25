import os
import os
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

data_path = BASE_DIR.parent / "LLM_labeler" / "data"

columns = ["session", "labels", "session_extended", "labels_extended", "labels_predicted"]
df_test  = pd.read_parquet(data_path / "sample_test_corpus_predictions.parquet", columns=columns)

with pd.option_context(
    'display.max_rows', None,
    'display.max_columns', None,
    'display.width', None,
):
    print("Test samples:\n", df_test)