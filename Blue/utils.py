import re
import numpy as np
import uuid
from datetime import datetime, timezone

def extract_json(text):
    """
    Extract a JSON object from a string using regex. Returns the JSON string or the original text if not found.
    """
    match = re.search(r'({[\s\S]+})', text)
    return match.group(1) if match else text.strip()

def cosine_similarity(a, b):
    """
    Compute the cosine similarity between two vectors a and b.
    """
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

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