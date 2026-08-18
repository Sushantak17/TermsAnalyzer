"""RAG explainer — retrieves similar previously-flagged clauses from ToS;DR.

When the classifier flags a clause, this module finds the most similar
clauses from the ToS;DR knowledge base and returns their explanations.
"""

import json
import numpy as np
import faiss
from pathlib import Path
from sentence_transformers import SentenceTransformer


DEFAULT_INDEX = Path(__file__).parent.parent / "data" / "rag_index" / "faiss.index"
DEFAULT_META = Path(__file__).parent.parent / "data" / "rag_index" / "metadata.json"


class RAGExplainer:
    """Retrieves similar flagged clauses from ToS;DR knowledge base."""

    def __init__(self, index_path=None, metadata_path=None):
        index_path = index_path or DEFAULT_INDEX
        metadata_path = metadata_path or DEFAULT_META

        self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
        self.index = faiss.read_index(str(index_path))

        with open(metadata_path) as f:
            self.metadata = json.load(f)

    def explain(self, clause, top_k=3):
        """Find the most similar previously-flagged clauses."""
        # encode and normalize (index uses inner product)
        embedding = self.encoder.encode([clause]).astype("float32")
        faiss.normalize_L2(embedding)

        scores, indices = self.index.search(embedding, top_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue

            entry = self.metadata[idx]
            results.append({
                "similar_clause": entry.get("clause_text", ""),
                "company": entry.get("company", "Unknown"),
                "classification": entry.get("classification", "unknown"),
                "category": entry.get("category", "General"),
                "explanation": entry.get("explanation", ""),
                "similarity": round(float(score), 3),
            })

        return results
