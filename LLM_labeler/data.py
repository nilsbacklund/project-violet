from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent

data_path = BASE_DIR.parent / "LLM_labeler" / "data"

with open(data_path / "sample_test_corpus_expanded.json", "r", encoding="utf8") as f:
    true_data = json.load(f)
    
with open(data_path / "sample_test_corpus_predictions.json", "r", encoding="utf8") as f:
    pred_data = json.load(f)

num_preds = 0
corrects = 0
for true_row, pred_row in zip(true_data, pred_data):
    if len(true_row["full_session"]) != len(pred_row["full_session"]):
        print("shit")
        print(true_row["full_session"])
        print(pred_row["full_session"])
        continue
    num_preds += len(true_row["full_session"])
    corrects += sum([true["label"] == pred["label"] for true, pred in zip(true_row["full_session"], pred_row["full_session"])])

print(corrects)
print(num_preds)
print(corrects / num_preds)