# %% Retrive all unique techniques from enterprise-attack.json

import json
from pathlib import Path

def retrieve_unique_techniques():
    mitre_attack_path = Path(__file__).resolve().parent / "enterprise-attack.json"
    with open(mitre_attack_path, 'r') as file:
        mitre_attack_data = json.load(file)

    unique_techniques = []
    for tactic in mitre_attack_data['objects']:
        if tactic['type'] == 'attack-pattern':
            unique_techniques.append({'id': tactic['external_references'][0]['external_id'], 'name': tactic['name']})

    return unique_techniques

def retrieve_unique_tactics():
    mitre_attack_path = Path(__file__).resolve().parent / "enterprise-attack.json"
    with open(mitre_attack_path, 'r') as file:
        mitre_attack_data = json.load(file)

    unique_tactics = []
    for tactic in mitre_attack_data['objects']:
        if tactic['type'] == 'x-mitre-tactic':
            unique_tactics.append({'id': tactic['external_references'][0]['external_id'], 'name': tactic['name']})

    return unique_tactics

if __name__ == "__main__":
    techniques = retrieve_unique_techniques()
    print(f"Retrieved {len(techniques)} unique techniques from enterprise-attack.json")
    print(json.dumps(techniques, indent=2))

    tactics = retrieve_unique_tactics()
    print(f"Retrieved {len(tactics)} unique tactics from enterprise-attack.json")
    print(json.dumps(tactics, indent=2))

# %%
