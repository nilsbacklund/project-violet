import json
import re
import os
import openai

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

def query_openai(prompt: str, model: str = "gpt-4o-mini", temperature: float = 0.7) -> str:
    openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
    response = openai_client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        stream=False,
    )
    return response.choices[0].message.content.strip()

def query_attack_patterns(config, model="gpt-4o-mini"):
    """
    Given a honeypot config, ask the OpenAI LLM what MITRE ATT&CK Tactics and Techniques might be observed.
    """
    prompt = (
        "Given the following honeypot configuration, list the most likely MITRE ATT&CK Tactics and Techniques "
        "that attackers might use against it. "
        "Output only a JSON array of objects, each with 'tactic', 'technique', and 'technique_id'.\n\n"
        f"CONFIGURATION:\n{json.dumps(config, indent=2)}"
    )
    llm_output = query_openai(prompt, model=model)
    # Extract the first [...] block
    match = re.search(r'(\[.*\])', llm_output, re.DOTALL)
    if match:
        llm_output = match.group(1)
    try:
        patterns = json.loads(llm_output)
    except Exception as e:
        print("Failed to parse LLM attack pattern output:", e)
        return []
    return patterns

def load_previous_attack_patterns(path="data/attack_patterns.json"):
    """
    Loads previous attack patterns from a JSON file.
    Each entry should be a dict with 'tactic', 'technique', 'technique_id'.
    """
    try:
        with open(path, "r", encoding="utf8") as f:
            return json.load(f)
    except Exception:
        return []

def is_novel_attack_pattern(new_patterns, previous_patterns):
    """
    Returns True if any new tactic/technique is not in previous_patterns.
    """
    prev_set = {(p['tactic'], p['technique_id']) for p in previous_patterns}
    for p in new_patterns:
        if (p['tactic'], p['technique_id']) not in prev_set:
            return True
    return False

def check_attack_patterns(config, llm_query_func=query_attack_patterns, attack_patterns_path="data/attack_patterns.json"):
    new_patterns = query_attack_patterns(config, llm_query_func)
    previous_patterns = load_previous_attack_patterns(attack_patterns_path)
    if is_novel_attack_pattern(new_patterns, previous_patterns):
        print("Novel attack patterns detected! Proceeding with deployment.")
        # Optionally: append new patterns to your DB here
        return True
    else:
        print("All attack patterns have been seen before. Please regenerate the honeypot config.")
        return False

# Example usage:
# config = ... # your generated honeypot config as a dict
# check_attack_patterns(config)

if __name__ == "__main__":
    # Load the generated config mock data
    with open("data/generated_config_response.json", "r", encoding="utf8") as f:
        generated_config = json.load(f)

    # For this test, let's check each service config individually
        print(f"\n--- Checking service configs ---")
        
        previous_patterns = []
        for session in load_previous_attack_patterns():
            previous_patterns.extend(session.get("patterns", []))
        # Query the attack patterns (mocked)
        new_patterns = query_attack_patterns(generated_config)        
        print("Predicted attack patterns:", new_patterns)
        # Check for novelty
        if is_novel_attack_pattern(new_patterns, previous_patterns):
            print("Novel attack patterns detected! Proceeding with deployment.")
        else:
            print("All attack patterns have been seen before. Please regenerate the honeypot config.")
