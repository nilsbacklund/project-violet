import json
import random
from pathlib import Path
import openai
import os
import numpy as np
from sentence_transformers import SentenceTransformer
import yaml
import jsonschema
import sys
import time
import fcntl
from config import llm_model_config
from Utils.jsun import load_json

# Add parent directory to sys.path to allow imports from project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Blue.attack_pattern_check import attack_methods_checker
from Blue.utils import extract_json, cosine_similarity, clean_and_finalize_config

# Load environment variables (for OpenAI API key)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Set up base directory and important paths
BASE_DIR = Path(__file__).resolve().parent

vulns_db_path = BASE_DIR.parent / 'Blue' / 'RagData' / 'vulnsDB_cleaned.json'
vulns_embeddings_path = BASE_DIR.parent / 'Blue' / 'RagData' / 'vulns_cleaned_embeddings_bge_m3.npy'
schema_path = BASE_DIR.parent / 'Blue' / 'RagData' / 'services_schema.json'

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

def get_honeypot_config(id="00", path=""):
    """
    Load a honeypot config by its ID or path from dir.
    """
    if not path:
        path = BASE_DIR.parent / 'Blue_Lagoon' / 'DefaultConfigs' / f'config_{id}.json'
    
    return load_json(path)

def set_honeypot_config(config):
    """
    Save each service from the honeypot config as a separate YAML file in the Honeypot/configurations/services directory.
    Each file is named using the config ID and the service name.
    Before saving, clear the directory to avoid leftover files from previous runs.
    Uses file locking to prevent concurrent access issues.
    """
    target_dir = BASE_DIR.parent / "Blue_Lagoon" / "configurations" / "services"
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a lock file for synchronization
    lock_file_path = target_dir / ".config_lock"
    
    with open(lock_file_path, "w") as lock_file:
        try:
            if sys.platform == "linux":
                import fcntl
                # Acquire exclusive lock
                fcntl.lockf(lock_file.fileno(), fcntl.LOCK_EX)
            
            # Remove old service files to avoid stale configs
            for file in target_dir.iterdir():
                if file.is_file() and file.name != ".config_lock":
                    file.unlink()
            
            services = config.get('services', [])
            config_id = config.get('id', 'unknown')
            
            for service in services:
                service_name = service.get('protocol', 'unnamed_service')
                filename = f"service_{service_name}_{config_id}_{str(time.time())[12:]}.yaml"
                target_path = target_dir / filename
                with open(target_path, "w", encoding="utf8") as f:
                    yaml.dump(service, f)
                print(f"Service config written to {target_path}")
                
        finally:
            # Lock is automatically released when the file is closed
            pass

# Pipeline Functions

def sample_previous_configs(config_dir, sample_size=5):
    """
    Randomly sample up to sample_size previous honeypot config files from the given directory.
    Extract relevant information for each sampled config for use in LLM prompting.
    """
    config_dir = Path(config_dir)

    config_files = []
    for hp_config_dir in config_dir.glob("hp_config_*"):
        config_file = hp_config_dir / "honeypot_config.json"
        if config_file.exists():
            config_files.append((hp_config_dir, config_file))

    if len(config_files) == 0:
        raise ValueError("No config files found in the directory.")
    if len(config_files) <= sample_size:
        sampled_files = config_files
    else:
        sampled_files = random.sample(config_files, sample_size)
    
    sampled_configs_with_sessions = []
    for hp_config_dir, config_file in sampled_files:
        try:
            with open(config_file, "r", encoding="utf8") as f:
                config_data = json.load(f)
            
            sessions_file = hp_config_dir / "sessions.json"
            session_data = None
            if sessions_file.exists():
                try:
                    with open(sessions_file, "r", encoding="utf8") as f:
                        session_data = json.load(f)
                except Exception as e:
                    print(f"Error loading session data from {sessions_file}: {e}")
                    session_data = None
            else:
                print(f"No sessions.json found in {hp_config_dir}")
            
            sampled_configs_with_sessions.append({
                "config": config_data,
                "sessions": session_data,
                "config_path": str(config_file),
                "sessions_path": str(sessions_file) if sessions_file.exists() else None
            })
            
        except Exception as e:
            print(f"Error loading config from {config_file}: {e}")
            continue
    
    return sampled_configs_with_sessions

def build_llm_prompt(sampled_configs):
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
    for i, entry in enumerate(sampled_configs, 1):
            config = entry["config"]
            sessions = entry["sessions"]
            
            llm_prompt += f"=== Previous Configuration {i} ===\n"
            llm_prompt += "HONEYPOT CONFIG:\n"
            llm_prompt += json.dumps(config, indent=2)
            llm_prompt += "\n\n"
            
            if sessions:
                llm_prompt += "ATTACK SESSIONS THIS CONFIG ATTRACTED:\n"
                if isinstance(sessions, list):
                    for j, session in enumerate(sessions):
                        llm_prompt += f"Session {j+1}:\n"
                        llm_prompt += json.dumps(session, indent=2)
                        llm_prompt += "\n"
                else:
                    llm_prompt += json.dumps(sessions, indent=2)
                llm_prompt += "\n"
            else:
                llm_prompt += "ATTACK SESSIONS: No session data available for this config.\n\n"
            
            llm_prompt += "=" * 50 + "\n\n"

    llm_prompt += "Now generate a specific user query that will retrieve exactly 5 novel and diverse vulnerabilities:\nUser query: "
    return llm_prompt

def retrieve_top_vulns(user_query, vulns_db, embeddings_path, top_n=5):
    """
    Given a user query, embed it and compute cosine similarity to all vulnerability embeddings.
    Return the top_n most similar vulnerabilities from the database.
    """
    MODEL_NAME = "BAAI/bge-m3"
    model = SentenceTransformer(MODEL_NAME, device="cpu")
    vulns_embeddings = np.load(embeddings_path)
    query_embedding = model.encode([user_query])[0]
    similarities = [cosine_similarity(query_embedding, emb) for emb in vulns_embeddings]
    top_idx = np.argsort(similarities)[-top_n:][::-1]

    cve_ids = list(vulns_db.keys())  
    
    top_vulns = []
    for i in top_idx:
        cve_id = cve_ids[i]
        cve_data = vulns_db[cve_id]
        cve_data["cve_id"] = cve_id 
        top_vulns.append(cve_data)
    
    return top_vulns

def build_config_prompt(schema_path, top_vulns, prev_config=None):
    """
    Build a prompt for the LLM to generate a new honeypot config, including the schema and selected vulnerabilities.
    """
    with open(schema_path, "r", encoding="utf8") as f:
        schema_text = f.read()
    config_prompt = (
        "You are an AI assistant tasked with generating a new Beelzebub honeypot configuration "
        "used for cybersecurity research.\n\n"
        "**Strategic Goals:**\n"
        "- **Maximize Session Length**: Design services that encourage prolonged attacker engagement\n"
        "- **Promote Attack Pattern Novelty**: Create configurations that attract diverse and uncommon attack techniques\n\n"
        "Requirements:\n"
        "1. Use **2 different services**, including one `http` and one `ssh` protocol.\n"
        "2. Each service must:\n"
        "   - Include a **relevant and unique CVE** (avoid duplicate CVEs across services).\n"
        "   - Provide a meaningful `cve_description` and valid `cve_tags`.\n"
        "   - Fully follow the JSON schema provided below.\n"
        "   - Include the `plugin` field explicitly: set it to `null` if not using an LLM.\n"
        "3. All **services** should use an LLM plugin (gpt-4o-mini, OpenAI).\n"
        "4. Make each service’s behavior **distinct** — e.g., vary the port, interaction style, or vulnerability.\n\n"
        "Return ONLY a complete JSON object that matches the schema structure.\n"
        "DO NOT include markdown or explanations.\n"
        "Begin output with an opening `{` and end with a closing `}`.\n"
    )
    config_prompt += f"\nSchema:\n{schema_text}\n\nVulnerabilities:\n"

    for vuln_data in top_vulns:
        cve_id = vuln_data.get("cve_id", "N/A")
        description = vuln_data.get("description", "No description provided.")
        config_prompt += f"- {cve_id}: {description}\n"

    if prev_config:
        config_prompt += f"Here is the previously generated configuration file that you should improve upon and update to use the provided vulnerabilities.\n"
        config_prompt += prev_config + "\n"

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

def save_config_as_file(config, path):
    """
    Save the generated config as a JSON file in the Blue_Lagoon/DefaultConfigs directory, named by its ID.
    """
    output_dir = BASE_DIR.parent / 'Blue_Lagoon' / 'DefaultConfigs'
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    config_id = config.get('id', 'unknown')
    filename = f"config_{config_id}.json"
    filepath = output_dir / filename
    with open(filepath, "w", encoding="utf8") as f:
        json.dump(config, f, indent=2)
    print(f"Config saved to {filepath}")

# Main Pipeline
def generate_new_honeypot_config(experiment_base_path=None, prev_config_path=None):
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
    print("Starting Reconfigurations with: " + str(experiment_base_path))

    vulns_db = load_json(vulns_db_path)
    config_attack_info = sample_previous_configs(experiment_base_path)
    llm_prompt = build_llm_prompt(config_attack_info)
    #print(llm_prompt)
    user_query = query_openai(llm_prompt)
    #print(user_query)
    top5_vulns = retrieve_top_vulns(user_query, vulns_db, vulns_embeddings_path)
    #print("\nTop 5 vulnerabilities for new config:")
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

    prev_config = None if prev_config_path is None else load_json(prev_config_path)
    config_prompt = build_config_prompt(schema_path, top5_vulns, prev_config)
    # print("\nPrompt sent to LLM for config generation:\n")
    # print(config_prompt[:1000], "...")
    
    for attempts in range(3):
        try:
            config = generate_config_with_llm(config_prompt)
            config = clean_and_finalize_config(config)
            if not validate_config(config, schema_path):
                print("Config is invalid. Not saving.")
                continue
    
            is_novel = attack_methods_checker(config, experiment_base_path)
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
    config_id, config = generate_new_honeypot_config()