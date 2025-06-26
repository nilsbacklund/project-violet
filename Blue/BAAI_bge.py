from sentence_transformers import SentenceTransformer
import json
import numpy as np
import os

# Set Hugging Face token
os.environ["HF_TOKEN"] = "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"

# Load your vulnerabilities database
with open("Blue/RagData/vulns_DB.json", "r", encoding="utf-8") as f:
    vulns = json.load(f)

print(f"Loaded {len(vulns)} vulnerabilities.")

# Convert each vulnerability entry to a string (adjust as needed)
texts = [json.dumps(v) for v in vulns]
print(f"Prepared {len(texts)} texts for embedding.")

# Load the model
model = SentenceTransformer("BAAI/bge-m3")

# Generate embeddings
embeddings = model.encode(texts, show_progress_bar=True)
print(f"Generated embeddings shape: {embeddings.shape}")

# Save embeddings for later use
np.save("Blue/RagData/vulns_embeddings_bge_m3.npy", embeddings)
print("Embeddings saved.")

#retrieval function
def load_vulns_db():
    with open("Blue/RagData/vulns_DB.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        # Return the list of CVE items
        return data["CVE_Items"]

def load_embeddings():
    return np.load("Blue/RagData/vulns_embeddings_bge_m3.npy")

def retrieve_vulns(query, top_k=5):
    vulns_db = load_vulns_db()
    embeddings = load_embeddings()
    query_emb = model.encode([query])
    scores = np.dot(embeddings, query_emb.T).squeeze()
    top_indices = np.argsort(scores)[::-1][:top_k]
    return [vulns_db[i] for i in top_indices]