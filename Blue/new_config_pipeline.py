import json
import random
from pathlib import Path
import openai
import os
import numpy as np
from sentence_transformers import SentenceTransformer
import yaml
from datetime import datetime, timezone
import yaml
import re
import uuid

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Paths to data files
data_dir = Path(__file__).parent / 'data'
service_configs_path = data_dir / 'service_configs.json'
attack_patterns_path = data_dir / 'attack_patterns.json'
vulns_db_path = data_dir / 'vulns_DB.json'
schema_path = data_dir / 'services_schema.json'

def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)

def get_attack_patterns_for_config(config_id, attack_patterns):
    for session in attack_patterns:
        if session.get('config_id') == config_id:
            return session.get('patterns', [])
    return []

def query_openai(prompt: str, model: str = "gpt-4o-mini", temperature: float = 0.7) -> str:
    openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
    response = openai_client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        stream=False,
    )
    # The first choice always contains the assistant reply:
    return response.choices[0].message.content.strip()

def embed_text(text, model="text-embedding-3-small"):
    response = openai.embeddings.create(
        input=[text],
        model=model
    )
    return response.data[0].embedding

def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def extract_json(text):
    match = re.search(r'({[\s\S]+})', text)
    return match.group(1) if match else text.strip()

def main():
    # Load DBs
    service_configs = load_json(service_configs_path)
    attack_patterns = load_json(attack_patterns_path)
    vulns_db = load_json(vulns_db_path)

    # 1. Randomly select up to 5 previous configs
    if len(service_configs) <= 5:
        sampled_configs = service_configs
    else:
        sampled_configs = random.sample(service_configs, 5)

    # 2. For each config, get associated attack patterns
    config_attack_info = []
    for config in sampled_configs:
        config_id = config['id']
        attacks = get_attack_patterns_for_config(config_id, attack_patterns)
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

    # 3. Prepare the LLM prompt
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
        llm_prompt += f"Config ID: {entry['config_id']}\nDescription: {entry['description']}\nServices: {[s['description'] for s in entry['services']]}\nAttacks: {[a['technique'] for a in entry['attacks']]}\n\n"

    llm_prompt += "Now generate a specific user query that will retrieve exactly 5 novel and diverse vulnerabilities:\nUser query: "
   
    # 4. Print or return the prompt (for LLM use)
    print(llm_prompt)

    # 5. Query OpenAI LLM
    user_query = query_openai(llm_prompt)
    print(user_query)

    # 6. RAG retrieval: Embed the user query and retrieve top 5 vulnerabilities using e5-large-v2
    MODEL_NAME = 'intfloat/e5-large-v2'
    model = SentenceTransformer(MODEL_NAME)
    
    # Load vulnerability embeddings
    vulns_embeddings = np.load(data_dir / 'vulns_embeddings_e5.npy')

    # Embed the user query using e5-large-v2
    query_embedding = model.encode([user_query])[0]

    # Compute cosine similarities
    similarities = [cosine_similarity(query_embedding, emb) for emb in vulns_embeddings]
    top5_idx = np.argsort(similarities)[-5:][::-1]

    if isinstance(vulns_db, dict) and "CVE_Items" in vulns_db:
        vulns_db_list = vulns_db["CVE_Items"]
    else:
        vulns_db_list = vulns_db
            
    top5_vulns = [vulns_db_list[i] for i in top5_idx]

    print("\nTop 5 vulnerabilities for new config:")
    for vuln in top5_vulns:
        cve_id = None
        description = None
        if 'cve' in vuln:
            cve_id = vuln['cve'].get('CVE_data_meta', {}).get('ID', 'N/A')
            desc_data = vuln['cve'].get('description', {}).get('description_data', [])
            if desc_data and isinstance(desc_data, list):
                description = desc_data[0].get('value', 'No description')
        # Fallbacks
        if not cve_id:
            cve_id = vuln.get('id', 'N/A')
        if not description:
            description = vuln.get('description', 'No description')
        print(f"- {cve_id}: {description}")

    # 5. Generate new config using the 5 vulnerabilities
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
    for v in top5_vulns:
        cve_id = v.get("cve", {}).get("CVE_data_meta", {}).get("ID", "N/A")
        descs = v.get("cve", {}).get("description", {}).get("description_data", [])
        description = " ".join(d.get("value", "") for d in descs)
        config_prompt += f"- {cve_id}: {description}\n"

    print("\nPrompt sent to LLM for config generation:\n")
    print(config_prompt[:1000], "...")

    openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": config_prompt}],
        temperature=0.7,
    )
    llm_output = response.choices[0].message.content

    json_str = extract_json(llm_output)

    try:
        config = json.loads(json_str)
    except Exception:
        config = yaml.safe_load(json_str)

    # Clean top-level
    config.pop("$schema", None)
    config.pop("title", None)
    config["id"] = str(uuid.uuid4())
    config["timestamp"] = datetime.now(timezone.utc).isoformat()

    # Clean each service
    for service in config.get("services", []):
        service.pop("id", None)
        if service.get("protocol") in ["http", "ssh"]:
            if "plugin" not in service:
                service["plugin"] = None
        else:
            service.pop("plugin", None)

    
    # Save config (append mode)
    config_file = "beelzebub_config.json"
    configs = []

    # If file exists and is not empty, load existing configs
    if os.path.exists(config_file) and os.path.getsize(config_file) > 0:
        with open(config_file, "r", encoding="utf-8") as f:
            try:
                configs = json.load(f)
                if not isinstance(configs, list):
                    configs = [configs]
            except Exception:
                configs = []

    # Append the new config
    configs.append(config)

    # Save the updated list
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(configs, f, indent=2)

    print("\nConfig appended to 'beelzebub_config.json'")

if __name__ == "__main__":
    main()
