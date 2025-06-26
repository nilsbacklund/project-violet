import os
import json

# Load MITRE technique data
MITRE_ATTACK_PATH = os.path.join(os.path.dirname(__file__), "RagData/mitre_attack_techniques.json")
with open(MITRE_ATTACK_PATH, "r", encoding="utf-8") as f:
    MITRE_TECHNIQUES = json.load(f)

def extract_mitre_labels(text):
    """
    Returns (technique_name, tactic_name) from MITRE based on text content.
    """
    technique_name = None
    tactic_name = None

    if not text:
        return None, None

    for technique in MITRE_TECHNIQUES:
        id_ = technique.get("id") or technique.get("ID")
        name = technique.get("name")
        if id_ and id_ in text:
            if id_.startswith("T") and not id_.startswith("TA"):
                technique_name = name
            elif id_.startswith("TA"):
                tactic_name = name
        if name and name.lower() in text.lower():
            if id_ and id_.startswith("T") and not id_.startswith("TA"):
                technique_name = name
            elif id_ and id_.startswith("TA"):
                tactic_name = name

    return technique_name, tactic_name
