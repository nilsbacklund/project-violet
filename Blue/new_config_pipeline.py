import json
import random
from pathlib import Path
import openai
import os
import numpy as np
from sentence_transformers import SentenceTransformer
import yaml
from datetime import datetime, timezone
import re
import jsonschema
import uuid
from dotenv import load_dotenv
import sys
import time
# Add parent directory to sys.path to allow imports from project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import print_output, llm_model_config
from Blue.attack_pattern_check import attack_methods_checker


# Load environment variables (for OpenAI API key)
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Set up base directory and important paths
BASE_DIR = Path(__file__).resolve().parent

service_configs_path = BASE_DIR.parent / 'BeelzebubServices'
attack_patterns_path = BASE_DIR.parent / 'logs'
vulns_db_path = BASE_DIR.parent / 'Blue' / 'RagData' / 'vulns_DB.json'
vulns_embeddings_path = BASE_DIR.parent / 'Blue' / 'RagData' / 'vulns_embeddings_e5.npy'
schema_path = BASE_DIR.parent / 'Blue' / 'RagData' / 'services_schema.json'

# Handle print output based on config setting
_builtin_print = print

def silent_print(*args, **kwargs):
    pass

# Override print globally
if not print_output:
    print = silent_print
else:
    print = _builtin_print

def load_json(path):
    """
    Load a JSON file from the given path and return its contents as a Python object.
    """
    # check if file exists
    if not path.exists():
        raise FileNotFoundError(f"Path {path} does not exist.")

    # check if file is json
    if not path.suffix == '.json':
        raise ValueError(f"Path {path} is not a JSON file.")

    with open(path, 'r') as f:
        return json.load(f)

def get_attack_patterns_for_config(config_id, attack_patterns):
    """
    Retrieve attack patterns associated with a specific config ID from the attack patterns list.
    """
    for session in attack_patterns:
        if session.get('config_id') == config_id:
            return session.get('patterns', [])
    
    return []

def extract_attack_patterns_from_labels(session_id):
    """
    Extract attack patterns (tactics and techniques) from labeled command logs.
    
    Args:
        session_id: The session ID to look for in the labels directory
        
    Returns:
        dict: Attack patterns with session info, or None if file doesn't exist
    """
    labels_file = attack_patterns_path /'labels'/ f'labels_{session_id}.json'
    
    # Check if the labels file exists
    if not labels_file.exists():
        print(f"Labels file {labels_file} does not exist. Skipping attack pattern extraction for session {session_id}.")
        return None
    
    try:
        with open(labels_file, 'r') as f:
            labeled_commands = json.load(f)
        
        # Extract unique attack patterns
        attack_patterns = []
        
        for command_data in labeled_commands:
            tactic = command_data.get('tactic')
            technique = command_data.get('technique')
            
            # Skip if tactic or technique is missing or "Unknown"
            if not tactic or not technique or tactic == "Unknown" or technique == "Unknown":
                continue
            
            attack_patterns.append({
                    'tactic': tactic,
                    'technique': technique 
                    })
         
        return attack_patterns
    
    except Exception as e:
        print(f"Error extracting attack patterns from {labels_file}: {e}")
        return None


def query_openai(prompt: str, model: str = None, temperature: float = 0.7) -> str:
    """
    Query the OpenAI LLM with a prompt and return the generated response as a string.
    Uses the model specified in config.py unless overridden.
    """
    if model is None:
        model = llm_model_config
    openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
    response = openai_client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        stream=False,
    )
    return response.choices[0].message.content.strip()

def cosine_similarity(a, b):
    """
    Compute the cosine similarity between two vectors a and b.
    """
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def extract_json(text):
    """
    Extract a JSON object from a string using regex. Returns the JSON string or the original text if not found.
    """
    match = re.search(r'({[\s\S]+})', text)
    return match.group(1) if match else text.strip()

def get_honeypot_config(id):
    """
    Load a honeypot config by its ID from the BeelzebubServices directory.
    """
    base_config_path = BASE_DIR.parent / 'BeelzebubServices' / f'config_{id}.json'
    return load_json(base_config_path)

def set_honeypot_config(config):
    """
    Save each service from the honeypot config as a separate YAML file in the Honeypot/configurations/services directory.
    Each file is named using the config ID and the service name.
    Before saving, clear the directory to avoid leftover files from previous runs.
    """
    target_dir = BASE_DIR.parent / "Blue_Lagoon" / "configurations" / "services"
    target_dir.mkdir(parents=True, exist_ok=True)
    # Remove old service files to avoid stale configs
    for file in target_dir.iterdir():
        if file.is_file():
            file.unlink()
    services = config.get('services', [])
    config_id = config.get('id', 'unknown')
    for service in services:
        service_name = service.get('protocol', 'unnamed_service')
        filename = f"service_{service_name}_{config_id}_{str(time.time())[12:]}.yaml"
        target_path = target_dir / filename
        with open(target_path, "w") as f:
            yaml.dump(service, f)
        print(f"Service config written to {target_path}")

# Pipeline Functions

def sample_previous_configs(services_dir, sample_size=5):
    """
    Randomly sample up to sample_size previous honeypot config files from the given directory.
    Extract relevant information for each sampled config for use in LLM prompting.
    """
    services_dir = Path(services_dir)
    json_files = list(services_dir.glob("config_*.json"))
    if len(json_files) == 0:
        raise ValueError("No config files found in the directory.")
    if len(json_files) <= sample_size:
        sampled_files = json_files
    else:
        sampled_files = random.sample(json_files, sample_size)
    sampled_configs = []
    for file in sampled_files:
        with open(file, "r") as f:
            sampled_configs.append(json.load(f))
    config_attack_info = []
    for config in sampled_configs:
        config_id = config['id']
        attacks = extract_attack_patterns_from_labels(config_id)
        cve_tags = [
            cve
            for svc in config.get('services', [])
            for cve in svc.get('cve_tags', [])
        ]
        config_attack_info.append({
            'config_id': config_id,
            'description': config.get('description'),
            'services': config.get('services'),
            'attacks': attacks,
            'vulnerabilities': cve_tags
        })
    return config_attack_info

def build_llm_prompt(config_attack_info):
    """
    Build a prompt for the LLM that summarizes previous honeypot configs and instructs it to generate a new user query for the RAG.
    """
    llm_prompt = """
    You are helping design the next iteration of honeypot configurations by generating a user query for a Retrieval-Augmented Generation (RAG) system. This system retrieves vulnerabilities from a database using semantic similarity, so your generated query must clearly direct it toward vulnerabilities that are different from those already explored.

    Instructions:
    - Based on the previous honeypot configs and the attacks they attracted (listed below), generate a user query that will retrieve 5 new and diverse vulnerabilities.
    - Your query should aim to explore *new attack surfaces*, *unrelated services*, and *alternative TTPs* not already represented.
    - Do NOT reference or include prior services, CVEs, or techniques. Instead, focus on techniques that are semantically distant.
    - Your goal is to create a query that steers retrieval *away* from the prior configurations.

    Below is the history of prior honeypot configurations:

    """
    for entry in config_attack_info:
        attacks_list = entry['attacks'] if entry['attacks'] is not None else []
        attack_patterns = [f"{a['tactic']} -> {a['technique']}" for a in attacks_list]
        llm_prompt += f"Config ID: {entry['config_id']}\nDescription: {entry['description']}\nServices: {[s['description'] for s in entry['services']]}\nAttacks: {attack_patterns}\n\n"
    llm_prompt += "Now generate a specific user query that will retrieve exactly 5 novel and diverse vulnerabilities:\nUser query: "
    return llm_prompt

def retrieve_top_vulns(user_query, vulns_db, embeddings_path, top_n=5):
    """
    Given a user query, embed it and compute cosine similarity to all vulnerability embeddings.
    Return the top_n most similar vulnerabilities from the database.
    """
    MODEL_NAME = 'intfloat/e5-large-v2'
    model = SentenceTransformer(MODEL_NAME)
    vulns_embeddings = np.load(embeddings_path)
    query_embedding = model.encode([user_query])[0]
    similarities = [cosine_similarity(query_embedding, emb) for emb in vulns_embeddings]
    top_idx = np.argsort(similarities)[-top_n:][::-1]
    if isinstance(vulns_db, dict) and "CVE_Items" in vulns_db:
        vulns_db_list = vulns_db["CVE_Items"]
    else:
        vulns_db_list = vulns_db
    top_vulns = [vulns_db_list[i] for i in top_idx]
    return top_vulns

def build_config_prompt(schema_path, top_vulns):
    """
    Build a prompt for the LLM to generate a new honeypot config, including the schema and selected vulnerabilities.
    """
    with open(schema_path, "r", encoding="utf8") as f:
        schema_text = f.read()
    config_prompt = (
        "You are an AI assistant tasked with generating a new Beelzebub honeypot configuration "
        "used for cybersecurity research.\n\n"
        "Requirements:\n"
        "1. Use at least **5 different services**, including a mix of `http`, `ssh`, and `tcp` protocols.\n"
        "2. Each service must:\n"
        "   - Include a **relevant and unique CVE** (avoid duplicate CVEs across services).\n"
        "   - Provide a meaningful `cve_description` and valid `cve_tags`.\n"
        "   - Fully follow the JSON schema provided below.\n"
        "   - Include the `plugin` field explicitly: set it to `null` if not using an LLM.\n"
        "3. At least **two services** should use an LLM plugin (gpt-4o-mini, OpenAI).\n"
        "4. Make each service’s behavior **distinct** — e.g., vary the port, interaction style, or vulnerability.\n\n"
        "Return ONLY a complete JSON object that matches the schema structure.\n"
        "DO NOT include markdown or explanations.\n"
        "Begin output with an opening `{` and end with a closing `}`.\n"
    )
    config_prompt += f"\nSchema:\n{schema_text}\n\nVulnerabilities:\n"
    for v in top_vulns:
        cve_id = v.get("cve", {}).get("CVE_data_meta", {}).get("ID", "N/A")
        descs = v.get("cve", {}).get("description", {}).get("description_data", [])
        description = " ".join(d.get("value", "") for d in descs)
        config_prompt += f"- {cve_id}: {description}\n"
    return config_prompt

def generate_config_with_llm(config_prompt):
    """
    Use the query_openai function to generate a new honeypot config from the LLM, then parse the result as JSON or YAML.
    """
    llm_output = query_openai(config_prompt, model=llm_model_config)
    json_str = extract_json(llm_output)
    try:
        config = json.loads(json_str)
    except Exception:
        config = yaml.safe_load(json_str)
    return config

def clean_and_finalize_config(config):
    """
    Clean up and finalize the generated config: remove schema/title, assign a new UUID, timestamp, and fix service fields.
    """
    config.pop("$schema", None)
    config.pop("title", None)
    config["id"] = str(uuid.uuid4())
    config["timestamp"] = datetime.now(timezone.utc).isoformat()
    for service in config.get("services", []):
        service.pop("id", None)
        if service.get("protocol") in ["http", "ssh"]:
            if "plugin" not in service:
                service["plugin"] = None
        else:
            service.pop("plugin", None)
    return config

def validate_config(config, schema_path):
    """
    Validate the generated config against the provided JSON schema.
    """
    with open(schema_path, "r", encoding="utf8") as f:
        schema = json.load(f)
    try:
        jsonschema.validate(instance=config, schema=schema)
        print("Config is valid according to schema.")
        return True
    except jsonschema.ValidationError as e:
        print("Config validation error:", e)
        return False

def save_config_as_file(config):
    """
    Save the generated config as a JSON file in the BeelzebubServices directory, named by its ID.
    """
    output_dir = BASE_DIR.parent / 'BeelzebubServices'
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    config_id = config.get('id', 'unknown')
    filename = f"config_{config_id}.json"
    filepath = output_dir / filename
    with open(filepath, "w") as f:
        json.dump(config, f, indent=2)
    print(f"Config saved to {filepath}")

# Main Pipeline
def generate_new_honeypot_config():
    """
    Main pipeline to generate a new honeypot config:
    - Loads attack patterns and vulnerabilities
    - Samples previous configs
    - Builds LLM prompt and queries LLM for user query for RAG
    - Retrieves top vulnerabilities
    - Builds and queries LLM for new config
    - Cleans, validates, and saves the config
    Returns the config ID and config object.
    """
    vulns_db = load_json(vulns_db_path)
    config_attack_info = sample_previous_configs(service_configs_path)
    llm_prompt = build_llm_prompt(config_attack_info)
    print(llm_prompt)
    user_query = query_openai(llm_prompt)
    print(user_query)
    top5_vulns = retrieve_top_vulns(user_query, vulns_db, vulns_embeddings_path)
    print("\nTop 5 vulnerabilities for new config:")
    for vuln in top5_vulns:
        cve_id = None
        description = None
        if 'cve' in vuln:
            cve_id = vuln['cve'].get('CVE_data_meta', {}).get('ID', 'N/A')
            desc_data = vuln['cve'].get('description', {}).get('description_data', [])
            if desc_data and isinstance(desc_data, list):
                description = desc_data[0].get('value', 'No description')
        if not cve_id:
            cve_id = vuln.get('id', 'N/A')
        if not description:
            description = vuln.get('description', 'No description')
        print(f"- {cve_id}: {description}")
    config_prompt = build_config_prompt(schema_path, top5_vulns)
    print("\nPrompt sent to LLM for config generation:\n")
    print(config_prompt[:1000], "...")
    
    for attempts in range(3):
        try:
            config = generate_config_with_llm(config_prompt)
            config = clean_and_finalize_config(config)
            if not validate_config(config, schema_path):
                print("Config is invalid. Not saving.")
                continue
            
            is_novel = attack_methods_checker(config)
            if not is_novel:
                print("Config is too similar to previous attack patterns. Regenerating or aborting.")
                continue

            config_id = config.get('id', None)
            print("\nConfig Object saved with id:", config_id)
            return config_id, config

        except Exception as e:
            print(f"Error generating config: {e}")
            if attempts == 2:
                print("Failed to generate config after 3 attempts. Aborting.")
                return None, None
            
    print("Failed to generate config after 3 attempts. Aborting.")
    return None, None
            
if __name__ == "__main__":
    generate_new_honeypot_config()
