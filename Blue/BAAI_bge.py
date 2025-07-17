from sentence_transformers import SentenceTransformer
import json
import numpy as np
import os

# Set Hugging Face token
os.environ["HF_TOKEN"] = "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"

# Load your vulnerabilities database
with open("Blue/RagData/vulnsDB_cleaned.json", "r", encoding="utf-8") as f:
    vulns = json.load(f)

print(f"Loaded {len(vulns)} vulnerabilities.")

# Convert each vulnerability entry to a string (adjust as needed)
texts = [json.dumps(v) for v in vulns]
print(f"Prepared {len(texts)} texts for embedding.")

# Load the model
model = SentenceTransformer("BAAI/bge-m3", device="cpu")

# Generate embeddings
embeddings = model.encode(texts, show_progress_bar=True)
print(f"Generated embeddings shape: {embeddings.shape}")

# Save embeddings for later use
np.save("Blue/RagData/vulns_cleaned_embeddings_bge_m3.npy", embeddings)
print("Embeddings saved.")