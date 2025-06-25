# Attacker Session Labeler

This project provides an automated Python tool (`labeler.py`) for analyzing and labeling shell command sessions, especially those related to potential cyber attacks. It combines static rule-based analysis with LLM (Large Language Model) assistance to provide detailed, structured annotations for each session.

## Features

- **Command Parsing:** Breaks down each shell command in a session, identifying base commands, parameters, and arguments.
- **MITRE ATT&CK Mapping:** Maps commands and behaviors to MITRE ATT&CK tactics and techniques (with TIDs) using a static dictionary and pattern matching.
- **Obfuscation Detection:** Detects common obfuscation patterns (e.g., base64, eval, piping) and attempts to deobfuscate base64-encoded payloads.
- **LLM-Assisted Labeling:** Sends the session to an LLM (e.g., OpenAI GPT) with a structured prompt and example outputs, requesting:
  - Tactics and techniques (with TIDs)
  - Rationale for the classification
  - Obfuscation detection and type
  - A `human_review` flag if the LLM is uncertain
- **Output:** Writes results as JSONL, including both static and LLM-based analysis for each session.
- **Error Handling:** Logs errors and skipped sessions to a separate file for review.
- **Example Analysis:** Includes an example session for demonstration and validation.

## Usage

1. Place your input data as `data/full_supervised_corpus.json`.
2. Ensure your OpenAI API key is set in your environment or `.env` file.
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Run the script:
   ```
   python labeler.py
   ```
5. Results are saved to `data/labeled_output.jsonl`. Errors are logged to `data/labeling_errors.log`.
6. To evaluate the labeling performance, run:
   ```
   python evaluate_labels.py
   ```
7. Evaluation results are saved to `data/eval_output.json`, including precision, recall, and F1 scores for tactics and techniques.
8. For a human-readable summary, see `data/eval_summary.txt`.
   - The evaluation output JSON also includes per-tactic metrics, exact match rate, and a list of the top missed tactics (those with the lowest recall).

## Understanding the Evaluation Metrics

After running `evaluate_labels.py`, you will see precision, recall, and F1 scores for both tactics and techniques. These metrics compare the LLM's predictions to the human (trusted/gold) labels for each session.

- **Micro metrics**: Treat every label equally, so results are dominated by the most common tactics. High micro scores mean the model is good at predicting frequent classes.
- **Macro metrics**: Treat every tactic equally, so rare tactics matter more. Low macro scores indicate the model struggles with less common tactics.
- **Per-tactic metrics**: Show precision, recall, and F1 for each individual tactic, helping you identify which tactics are missed or predicted well.
- **Exact match rate**: The percentage of sessions where all tactics are predicted exactly as in the ground truth. This is a strict measure of session-level accuracy.
- **Top missed tactics**: The tactics with the lowest recall, i.e., those most often missed by the model. These are listed in the evaluation output for targeted improvement.

**Example:**
- If micro F1 is high but macro F1 is low, the model is only good at the most common tactics.
- If per-tactic recall is 0.00 for a tactic, the model never predicts it correctly.
- A low exact match rate means the model rarely gets all tactics correct for a session.

## Improving Model Performance

- Add more prompt examples and data for rare tactics.
- Balance your dataset to avoid overfitting to common tactics.
- Use the `top_missed_tactics` field in `eval_output.json` to focus on the tactics your model struggles with most.
- Review `data/eval_summary.txt` for a quick overview and actionable insights.

## Output Review

- The file `data/eval_output.json` contains:
  - Overall precision, recall, and F1 for tactics and techniques.
  - A list of all sessions, showing both human and LLM labels, and whether they match, for easy review and explanation to colleagues.

## Requirements

- Python 3.7+
- `openai`, `tqdm`, `python-dotenv`

## File Structure

- `labeler.py` — Main script for labeling and analysis
- `llm_labeler.py` — (Optional) Additional LLM labeling utilities
- `requirements.txt` — Python dependencies
- `data/` — Input and output data files

## License

This project is for research and educational use. See LICENSE for details.
