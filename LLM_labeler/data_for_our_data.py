from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent

new_path = BASE_DIR.parent / "logs" / "experiment_2025-07-12T15_56_53"

data_path = BASE_DIR.parent / "LLM_labeler" / "data"

with open(new_path / "sessions.json", "r", encoding="utf8") as f:
    true_data = json.load(f)
    
with open(data_path / "our_data_predictions.json", "r", encoding="utf8") as f:
    pred_data = json.load(f)

true_data = [session for session in true_data if session["session"] != ""]

num_preds = 0
corrects = 0
for i, (true_row, pred_row) in enumerate(zip(true_data, pred_data)):
    if len(true_row["full_session"]) != len(pred_row["full_session"]):
        print(len(true_row["full_session"]), len(pred_row["full_session"]))
        continue
        
    num_preds += len(true_row["full_session"])
    corrects += sum([true["tactic"] == pred["label"] for true, pred in zip(true_row["full_session"], pred_row["full_session"])])

print(corrects)
print(num_preds)
print(corrects / num_preds)