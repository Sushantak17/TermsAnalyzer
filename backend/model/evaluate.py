"""Evaluate trained model with per-class metrics and confusion matrix."""

import json
import torch
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from sklearn.metrics import classification_report, confusion_matrix
from transformers import AutoTokenizer, AutoModelForSequenceClassification


MODEL_DIR = Path(__file__).parent / "checkpoints" / "best"
DATA_DIR = Path(__file__).parent.parent / "data" / "processed"
OUTPUT_DIR = Path(__file__).parent / "results"

LABEL_NAMES = ["fair", "potentially_unfair", "unfair"]
MAX_LENGTH = 256


def get_device():
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def predict_batch(model, tokenizer, texts, device, batch_size=32):
    """Run inference on a list of texts."""
    all_preds = []
    all_probs = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        inputs = tokenizer(
            batch, return_tensors="pt", truncation=True,
            max_length=MAX_LENGTH, padding=True
        )
        inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = model(**inputs)

        probs = torch.softmax(outputs.logits, dim=-1).cpu().numpy()
        preds = np.argmax(probs, axis=-1)

        all_preds.extend(preds.tolist())
        all_probs.extend(probs.tolist())

    return all_preds, all_probs


def plot_confusion_matrix(y_true, y_pred, output_path):
    """Save confusion matrix as a nice heatmap."""
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(8, 6))
    sns.heatmap(
        cm, annot=True, fmt="d", cmap="Blues",
        xticklabels=LABEL_NAMES, yticklabels=LABEL_NAMES
    )
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.title("Confusion Matrix — TermsAnalyzer")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Confusion matrix saved to {output_path}")


def evaluate():
    """Run full evaluation on test set."""
    device = get_device()

    # load model
    print(f"Loading model from {MODEL_DIR}...")
    tokenizer = AutoTokenizer.from_pretrained(str(MODEL_DIR))
    model = AutoModelForSequenceClassification.from_pretrained(str(MODEL_DIR))
    model.to(device)
    model.eval()

    # load test data
    with open(DATA_DIR / "test.json") as f:
        test_data = json.load(f)
    print(f"Test set: {len(test_data)} samples")

    texts = [d["text"] for d in test_data]
    true_labels = [d["label"] for d in test_data]

    # predict
    print("Running inference...")
    pred_labels, pred_probs = predict_batch(model, tokenizer, texts, device)

    # classification report
    report = classification_report(
        true_labels, pred_labels,
        target_names=LABEL_NAMES, digits=4
    )
    print("\n" + "=" * 60)
    print("CLASSIFICATION REPORT")
    print("=" * 60)
    print(report)

    # save report
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_DIR / "classification_report.txt", "w") as f:
        f.write(report)

    # confusion matrix
    plot_confusion_matrix(true_labels, pred_labels, OUTPUT_DIR / "confusion_matrix.png")

    # save detailed predictions for analysis
    results = []
    for i, d in enumerate(test_data):
        results.append({
            "text": d["text"],
            "true_label": LABEL_NAMES[d["label"]],
            "pred_label": LABEL_NAMES[pred_labels[i]],
            "confidence": round(max(pred_probs[i]), 4),
            "correct": d["label"] == pred_labels[i],
        })

    with open(OUTPUT_DIR / "predictions.json", "w") as f:
        json.dump(results, f, indent=2)

    # print summary
    accuracy = sum(1 for r in results if r["correct"]) / len(results)
    print(f"\nOverall accuracy: {accuracy:.4f}")
    print(f"Results saved to {OUTPUT_DIR}/")

    return report


if __name__ == "__main__":
    evaluate()
