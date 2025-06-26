import pandas as pd
from pathlib import Path
from typing import Tuple

BASE_DIR = Path(__file__).resolve().parent

data_path = BASE_DIR.parent / "LLM_labeler" / "data"

def read_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    columns = ["session", "labels"]
    df_train = pd.read_parquet(data_path / "sample_train_corpus.parquet", columns=columns)
    df_test = pd.read_parquet(data_path / "sample_test_corpus.parquet", columns=columns)

    return df_train, df_test