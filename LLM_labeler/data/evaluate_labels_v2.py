import json
import os
from sklearn.metrics import precision_recall_fscore_support

def normalize_labels(labels):
    norm = set()
    for l in labels:
        l = l.lower().strip()
        if '(' in l and ')' in l:
            l = l[:l.index('(')].strip()
        norm.add(l)
    return norm

# Load ground-truth tactics from full_supervised_corpus_fixed.json (support JSONL or JSON array)
gt_path = os.path.join("data", "full_supervised_corpus_fixed.json")
gt_sessions = []
try:
    with open(gt_path, 'r', encoding='utf-8') as f:
        first_char = f.read(1)
        f.seek(0)
        if first_char == '[':
            gt_sessions = json.load(f)
        else:
            gt_sessions = [json.loads(line) for line in f if line.strip()]
except Exception as e:
    print(f"Error loading ground-truth file: {e}")
    gt_sessions = []
gt_tactics_list = [normalize_labels(entry.get('tactics', [])) for entry in gt_sessions]

# Determine the minimum number of sessions to compare
input_path = "data/labeled_output.jsonl"
eval_output_path = os.path.join("data", "eval_output.json")
eval_output_jsonl = os.path.join("data", "eval_output.jsonl")
num_sessions = min(len(gt_tactics_list), sum(1 for _ in open(input_path, 'r', encoding='utf-8')))

# Read LLM predictions (support both JSONL and JSON array)
llm_sessions = []
try:
    with open(input_path, 'r', encoding='utf-8') as f:
        first_char = f.read(1)
        f.seek(0)
        if first_char == '[':
            llm_sessions = json.load(f)
        else:
            llm_sessions = [json.loads(line) for line in f if line.strip()]
except Exception as e:
    print(f"Error loading LLM predictions: {e}")
    llm_sessions = []

llm_tactics = []
session_comparisons = []
for i in range(num_sessions):
    d = llm_sessions[i]
    llm = d.get('llm_labels', {})
    llm_tac = normalize_labels(llm.get('tactics', []))
    llm_tactics.append(llm_tac)
    human_tac = gt_tactics_list[i]
    # Always use session text from ground-truth file for comparison
    session_text = gt_sessions[i].get('session', gt_sessions[i].get('commands', ''))
    session_comparisons.append({
        "session_index": i+1,
        "session": session_text,
        "human_tactics": list(human_tac),
        "llm_tactics": list(llm_tac),
        "tactics_match": human_tac == llm_tac
    })

print(f"Loaded {len(gt_sessions)} ground-truth sessions from {gt_path}")
print(f"Loaded {len(llm_tactics)} LLM-predicted sessions from {input_path}")
if len(gt_sessions) != len(llm_tactics):
    print(f"Warning: Number of ground-truth sessions ({len(gt_sessions)}) does not match number of LLM sessions ({len(llm_tactics)}). Comparing only first {num_sessions} sessions.")
if not gt_tactics_list or not llm_tactics:
    print("Warning: No tactics found in ground-truth or LLM predictions. Output files may be empty.")

def compute_metrics(gold, pred):
    y_true = []
    y_pred = []
    all_labels = set()
    
    for g, p in zip(gold, pred):
        all_labels.update(g)
        all_labels.update(p)
    
    all_labels = sorted(list(all_labels))
    if not all_labels:
        print("No labels found in either gold or predicted data. Cannot compute metrics.")
        return {}, [], all_labels

    for g, p in zip(gold, pred):
        for label in all_labels:
            y_true.append(1 if label in g else 0)
            y_pred.append(1 if label in p else 0)

    # Compute multiple types of scores
    try:
        metrics = {}
        metrics["micro"] = precision_recall_fscore_support(y_true, y_pred, average='micro', zero_division=0)
        metrics["macro"] = precision_recall_fscore_support(y_true, y_pred, average='macro', zero_division=0)
        metrics["none"]  = precision_recall_fscore_support(y_true, y_pred, average=None, zero_division=0, labels=all_labels)
    except Exception as e:
        print(f"Error computing metrics: {e}")
        return {}, [], all_labels

    return metrics, all_labels

# Run the updated compute_metrics
metrics, tac_labels = compute_metrics(gt_tactics_list[:num_sessions], llm_tactics)

# Display results
print("=== Tactics Evaluation ===")
for avg_type in ["micro", "macro"]:
    if avg_type in metrics:
        p, r, f1, *_ = metrics[avg_type]
        print(f"[{avg_type.capitalize()}] Precision: {p:.3f}  Recall: {r:.3f}  F1: {f1:.3f}")

# Per-label breakdown
if "none" in metrics:
    print("\n--- Per-Tactic Metrics ---")
    p_list, r_list, f1_list, _ = metrics["none"]
    for label, p, r, f1 in zip(tac_labels, p_list, r_list, f1_list):
        print(f"{label:20s}  Precision: {p:.2f}  Recall: {r:.2f}  F1: {f1:.2f}")

# Check exact match rate (must be after all variables are defined)
matches = [1 if set(h) == set(p) else 0 for h, p in zip(gt_tactics_list[:num_sessions], llm_tactics)]
exact_match_rate = sum(matches) / len(matches) if matches else 0.0
print(f"\nExact match sessions: {sum(matches)} / {len(matches)} ({exact_match_rate:.2%})")

# Save results
def save_results_to_file(metrics, session_comparisons):
    per_tactic = [
        {"tactic": label, "precision": p, "recall": r, "f1": f1}
        for label, p, r, f1 in zip(tac_labels, metrics["none"][0], metrics["none"][1], metrics["none"][2])
    ] if "none" in metrics else []
    # Find top missed tactics (lowest recall, but only those that appear in ground truth at least once)
    # Only include tactics with recall < 1.0 and recall > 0.0 (i.e., missed at least once, but present in ground truth)
    top_missed_tactics = sorted(
        [pt for pt in per_tactic if pt["recall"] < 1.0 and pt["recall"] > 0.0], key=lambda x: x["recall"]
    )[:5] if per_tactic else []
    # If all recalls are 0, show those as well
    if not top_missed_tactics:
        top_missed_tactics = sorted(
            [pt for pt in per_tactic if pt["recall"] == 0.0], key=lambda x: x["precision"]
        )[:5] if per_tactic else []
    results = {
        "tactics": {
            "micro": {
                "precision": metrics["micro"][0],
                "recall": metrics["micro"][1],
                "f1": metrics["micro"][2]
            },
            "macro": {
                "precision": metrics["macro"][0],
                "recall": metrics["macro"][1],
                "f1": metrics["macro"][2]
            }
        },
        "session_comparisons": session_comparisons,
        "exact_match_sessions": sum(matches),
        "total_sessions": len(matches),
        "exact_match_rate": exact_match_rate,
        "per_tactic_metrics": per_tactic,
        "top_missed_tactics": top_missed_tactics,
        "explanation": (
            "Micro metrics: Treat every label equally, dominated by common tactics. "
            "Macro metrics: Treat every tactic equally, so rare tactics matter more. "
            "Per-tactic: Shows which tactics are missed or predicted well. "
            "Exact match: Fraction of sessions where all tactics are predicted exactly. "
            "Top missed tactics: Tactics with the lowest recall, i.e., most often missed by the model."
        )
    }
    with open(eval_output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

# Save results only if metrics are available
if metrics and "micro" in metrics and "macro" in metrics:
    save_results_to_file(metrics, session_comparisons)
    with open(eval_output_jsonl, "w", encoding="utf-8") as f:
        for entry in session_comparisons:
            out = {
                "session_index": entry["session_index"],
                "session": entry["session"],
                "human_tactics": entry["human_tactics"],
                "llm_tactics": entry["llm_tactics"],
                "tactics_match": entry["tactics_match"]
            }
            f.write(json.dumps(out, separators=(",", ": ")) + "\n")
    print(f"Session-by-session comparison written to {eval_output_jsonl}")

    # Write a human-readable summary
    summary_path = os.path.join("data", "eval_summary.txt")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("=== MITRE ATT&CK Tactics Evaluation Summary ===\n\n")
        f.write(f"Micro Precision: {metrics['micro'][0]:.3f}\n")
        f.write(f"Micro Recall:    {metrics['micro'][1]:.3f}\n")
        f.write(f"Micro F1:       {metrics['micro'][2]:.3f}\n\n")
        f.write(f"Macro Precision: {metrics['macro'][0]:.3f}\n")
        f.write(f"Macro Recall:    {metrics['macro'][1]:.3f}\n")
        f.write(f"Macro F1:       {metrics['macro'][2]:.3f}\n\n")
        if "none" in metrics:
            f.write("Per-Tactic Metrics:\n")
            p_list, r_list, f1_list, _ = metrics["none"]
            for label, p, r, f1 in zip(tac_labels, p_list, r_list, f1_list):
                f.write(f"  {label:20s}  Precision: {p:.2f}  Recall: {r:.2f}  F1: {f1:.2f}\n")
            f.write("\n")
        f.write(f"Exact match sessions: {sum(matches)} / {len(matches)} ({exact_match_rate:.2%})\n\n")
        f.write("Explanation:\n")
        f.write("- Micro metrics: Treat every label equally, dominated by common tactics.\n")
        f.write("- Macro metrics: Treat every tactic equally, so rare tactics matter more.\n")
        f.write("- Per-tactic: Shows which tactics are missed or predicted well.\n")
        f.write("- Exact match: Fraction of sessions where all tactics are predicted exactly.\n")
    print(f"Human-readable summary written to {summary_path}")
else:
    print("No valid metrics to save. Please check your input files.")
