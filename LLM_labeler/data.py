import os
import os
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

data_path = BASE_DIR.parent / "LLM_labeler" / "data"

df = pd.read_json(data_path / "sample_test_corpus_predictions.json", orient="records")

predicted_labels = df["labels_predicted"]
true_labels = df["labels_expanded"]
N = len(predicted_labels)

num_labels = 0

for predicted_label, true_label in zip(predicted_labels, true_labels):
    predicted_list = predicted_label.split(" - ")
    true_list = true_label.split(" - ")
    if len(true_list) != len(predicted_list):
        print(f"Number of true labels did not match number of predicted labels! {len(predicted_list), len(true_list)}")
    num_labels += len(true_list)


binary_fidelity = (true_labels == predicted_labels).sum() / N
print(binary_fidelity)