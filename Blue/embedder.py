from sentence_transformers import SentenceTransformer
import numpy as np
import json

def generate_and_save_embeddings(data_path, output_path, text_fn):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    with open(data_path) as f:
        data = json.load(f)
        # If NVD format, extract the list of vulnerabilities
        if isinstance(data, dict) and "CVE_Items" in data:
            data = data["CVE_Items"]
    texts = [text_fn(entry) for entry in data]
    embeddings = model.encode(texts)
    np.save(output_path, embeddings)

def vuln_text(entry):
    # Description: concatenate all description values
    descs = entry.get("cve", {}).get("description", {}).get("description_data", [])
    desc = " ".join(d.get("value", "") for d in descs)

    # Problem types: concatenate all problemtype values
    pt_data = entry.get("cve", {}).get("problemtype", {}).get("problemtype_data", [])
    problemtypes = []
    for pt in pt_data:
        for d in pt.get("description", []):
            val = d.get("value", "")
            if val:
                problemtypes.append(val)

    # Impact: extract baseScore, baseSeverity, vectorString, etc.
    impact = entry.get("impact", {}).get("baseMetricV3", {}).get("cvssV3", {})
    impact_fields = []
    for key in ["baseScore", "baseSeverity", "vectorString", "attackVector", "attackComplexity", "privilegesRequired", "userInteraction", "scope", "confidentialityImpact", "integrityImpact", "availabilityImpact"]:
        val = impact.get(key, "")
        if val:
            impact_fields.append(str(val))

    return f"{desc} {' '.join(problemtypes)} {' '.join(impact_fields)}"


if __name__ == "__main__":
    # Attacks
    generate_and_save_embeddings(
        "data/attacks.json",
        "data/attacks_embeddings.npy",
        lambda entry: entry["summary"] + " " + " ".join([a["command"] for a in entry["actions"]])
    )
    # Configs
    generate_and_save_embeddings(
        "data/configs.json",
        "data/configs_embeddings.npy",
        lambda entry: json.dumps(entry)
    )
    # Vulns
    generate_and_save_embeddings(
        "data/vulns_DB.json",
        "data/vulns_embeddings.npy",
        vuln_text
    )