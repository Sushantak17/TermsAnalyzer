"""Inference module — loads trained model and classifies clauses."""

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from pathlib import Path


LABEL_MAP = {0: "fair", 1: "potentially_unfair", 2: "unfair"}
RISK_SCORES = {0: 1, 1: 3, 2: 5}
MAX_LENGTH = 256


class ClauseClassifier:
    """Wraps the fine-tuned Legal-BERT for single/batch inference."""

    def __init__(self, model_path=None):
        if model_path is None:
            model_path = Path(__file__).parent / "checkpoints" / "best"

        self.device = self._get_device()
        self.tokenizer = AutoTokenizer.from_pretrained(str(model_path))
        self.model = AutoModelForSequenceClassification.from_pretrained(str(model_path))
        self.model.to(self.device)
        self.model.eval()

    def _get_device(self):
        if torch.backends.mps.is_available():
            return torch.device("mps")
        elif torch.cuda.is_available():
            return torch.device("cuda")
        return torch.device("cpu")

    def predict(self, clauses):
        """Classify a list of clause strings. Returns list of dicts."""
        results = []
        for clause in clauses:
            inputs = self.tokenizer(
                clause, return_tensors="pt",
                truncation=True, max_length=MAX_LENGTH, padding=True
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.model(**inputs)

            probs = torch.softmax(outputs.logits, dim=-1)
            pred_idx = probs.argmax().item()
            confidence = probs[0][pred_idx].item()

            results.append({
                "clause": clause,
                "label": LABEL_MAP[pred_idx],
                "confidence": round(confidence, 3),
                "risk_score": RISK_SCORES[pred_idx],
            })

        return results
