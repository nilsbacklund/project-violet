import os
import json
import re
import openai
from pathlib import Path

# Set up base directory and important paths
BASE_DIR = Path(__file__).resolve().parent
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
LOGS_PATH = BASE_DIR.parent / "logs"

# Query the OpenAI LLM with a prompt and return the response as a string
def query_openai(prompt: str, model: str = "gpt-4o-mini", temperature: float = 0.7) -> str:
    try:
        openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
        response = openai_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            stream=False,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"OpenAI API call failed: {e}")
        return ""

# Query the LLM for an ordered sequence of MITRE tactics and techniques for a given config
def query_attack_patterns(config, model="gpt-4o-mini"):
    prompt = (
        "Given the following honeypot configuration, predict a likely sequence of MITRE ATT&CK tactics and techniques "
        "that an attacker would use against this setup. "
        "Output only a JSON array, in order, where each element is an object with 'tactic' and 'technique'.\n\n"
        f"CONFIGURATION:\n{json.dumps(config, indent=2)}"
    )
    llm_output = query_openai(prompt, model=model)
    # Extract the first JSON array from the LLM output
    match = re.search(r'(\[.*\])', llm_output, re.DOTALL)
    if match:
        llm_output = match.group(1)
    try:
        patterns = json.loads(llm_output)
    except Exception as e:
        print("Failed to parse LLM attack pattern output:", e)
        return []
    return patterns

# Extract the ordered sequence of (tactic, technique) pairs from LLM output
def extract_ordered_tactic_technique_sequence(patterns):
    try:
        return tuple((p['tactic'], p['technique']) for p in patterns if p.get('tactic') and p.get('technique'))
    except Exception as e:
        print(f"Failed to extract tactic/technique sequence: {e}")
        return tuple()

# Load all previous ordered sequences of (tactic, technique) pairs from log files
def load_all_previous_sequences(logs_path=LOGS_PATH):
    all_sequences = set()
    for log_file in Path(logs_path).glob("full_logs_*.json"):
        try:
            with open(log_file, "r", encoding="utf8") as f:
                sessions = json.load(f)
        except Exception as e:
            print(f"Failed to load or parse {log_file}: {e}")
            continue
        for session in sessions:
            sequence = []
            for entry in session:
                try:
                    mitre = entry.get("mitre_attack_method", {})
                    tactic = mitre.get("tactic_used")
                    technique = mitre.get("technique_used")
                    if tactic and technique:
                        sequence.append((tactic, technique))
                except Exception as e:
                    print(f"Failed to extract entry in {log_file}: {e}")
            if sequence:
                all_sequences.add(tuple(sequence))
    return all_sequences

# Main checker: compares the new config's predicted attack sequence to all previous ones
def attack_methods_checker(config, logs_path=LOGS_PATH):
    print("[1] Querying LLM for MITRE attack patterns...")
    new_patterns = query_attack_patterns(config)
    print("Predicted attack patterns:", new_patterns)
    new_sequence = extract_ordered_tactic_technique_sequence(new_patterns)
    previous_sequences = load_all_previous_sequences(logs_path)
    if new_sequence in previous_sequences:
        print("Exact attack sequence already observed. Please regenerate.")
        return False
    print("Attack sequence is novel. Proceeding.")
    return True