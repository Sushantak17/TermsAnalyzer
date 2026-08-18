"""Build FAISS index from ToS;DR cases for RAG explanations.

Embeds each case using sentence-transformers, stores in a FAISS index
with metadata for fast similarity search at inference time.
"""

import json
import numpy as np
import faiss
from pathlib import Path
from sentence_transformers import SentenceTransformer

DATA_DIR = Path(__file__).parent
RAW_DIR = DATA_DIR / "raw"
INDEX_DIR = DATA_DIR / "rag_index"

EMBED_MODEL = "all-MiniLM-L6-v2"  # small, fast, works great on M4


def build_index():
    """Create FAISS index from ToS;DR cases."""
    # load cases
    cases_path = RAW_DIR / "tosdr_cases.json"
    with open(cases_path) as f:
        cases = json.load(f)
    print(f"Loaded {len(cases)} cases from {cases_path}")

    # filter out entries with very short text
    cases = [c for c in cases if len(c.get("clause_text", "")) > 15]
    print(f"After filtering: {len(cases)} cases")

    # build text to embed — combine clause text with title for richer embeddings
    texts = []
    for c in cases:
        text = c["clause_text"]
        if c.get("title") and c["title"] != text:
            text = f"{c['title']}. {text}"
        texts.append(text)

    # embed
    print(f"Embedding with {EMBED_MODEL}...")
    encoder = SentenceTransformer(EMBED_MODEL)
    embeddings = encoder.encode(texts, show_progress_bar=True, batch_size=64)
    embeddings = np.array(embeddings, dtype="float32")

    # normalize for cosine similarity (use inner product index)
    faiss.normalize_L2(embeddings)
    dim = embeddings.shape[1]

    # build index
    index = faiss.IndexFlatIP(dim)  # inner product = cosine sim after normalization
    index.add(embeddings)
    print(f"FAISS index built: {index.ntotal} vectors, dim={dim}")

    # save index and metadata
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    faiss.write_index(index, str(INDEX_DIR / "faiss.index"))

    # save metadata (everything except the embedding)
    with open(INDEX_DIR / "metadata.json", "w") as f:
        json.dump(cases, f, indent=2)

    print(f"Saved index and metadata to {INDEX_DIR}/")
    return index, cases


if __name__ == "__main__":
    build_index()
