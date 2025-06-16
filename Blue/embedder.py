import json
import numpy as np
from transformers import AutoTokenizer, AutoModel
import torch
import torch.nn.functional as F

MODEL_NAME = 'intfloat/e5-large-v2'
BATCH_SIZE = 32 # Increase?
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu' # if cuda available ?

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME).to(DEVICE)
model.eval()

# Pools output of transformer to single vector per doc, ignore padding tokens with attention mask
def average_pool(last_hidden_states, attention_mask):
    last_hidden = last_hidden_states.masked_fill(~attention_mask[..., None].bool(), 0.0)
    return last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]

# run batch of tokenized text through transformer, pool output to single vector per doc, normalie
def create_embedding(batch_dict):
    with torch.no_grad():
        outputs = model(**batch_dict)
        embeddings = average_pool(outputs.last_hidden_state, batch_dict['attention_mask'])
        embeddings = F.normalize(embeddings, p=2, dim=1)
    return embeddings


def embed_db(json_path, npy_path, text_fn):
    # Load and flatten the JSON
    with open(json_path, encoding="utf8") as f:
        data = json.load(f)
        # If NVD format, extract the list of vulnerabilities
        if isinstance(data, dict) and "CVE_Items" in data:
            data = data["CVE_Items"]
        elif isinstance(data, dict):
            data = list(data.values())

    texts = [text_fn(entry) for entry in data]
    all_embeddings = []

    # for each text entry process in batches: tokenize and create embeddings for each batch
    for i in range(0, len(texts), BATCH_SIZE):
        batch_texts = texts[i:i+BATCH_SIZE]
        batch_dict = tokenizer(batch_texts, padding=True, truncation=True, max_length=512, return_tensors='pt')
        batch_dict = {k: v.to(DEVICE) for k, v in batch_dict.items()}
        embeddings = create_embedding(batch_dict)
        all_embeddings.append(embeddings.cpu().numpy())
        print(f"Embedded {i + len(batch_texts)} / {len(texts)}")
    all_embeddings = np.vstack(all_embeddings)
    np.save(npy_path, all_embeddings)
    print(f"Saved embeddings to {npy_path}")

# Entry for each vulnerability
def vuln_text(entry):
    # Extract and concatenate relevant fields
    descs = entry.get("cve", {}).get("description", {}).get("description_data", [])
    desc = " ".join(d.get("value", "") for d in descs)
    pt_data = entry.get("cve", {}).get("problemtype", {}).get("problemtype_data", [])
    problemtypes = []
    for pt in pt_data:
        for d in pt.get("description", []):
            val = d.get("value", "")
            if val:
                problemtypes.append(val)
    impact = entry.get("impact", {}).get("baseMetricV3", {}).get("cvssV3", {})
    impact_fields = []
    for key in [
        "baseScore", "baseSeverity", "vectorString", "attackVector", "attackComplexity",
        "privilegesRequired", "userInteraction", "scope", "confidentialityImpact",
        "integrityImpact", "availabilityImpact"
    ]:
        val = impact.get(key, "")
        if val:
            impact_fields.append(str(val))
    return f"{desc} {' '.join(problemtypes)} {' '.join(impact_fields)}"

def main():
    embed_db("RagData/vulns_DB.json", "RagData/vulns_embeddings_e5.npy", vuln_text) 

if __name__ == "__main__":
    main()