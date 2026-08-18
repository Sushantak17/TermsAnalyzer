"""Ablation study — compare Legal-BERT vs DistilBERT vs vanilla BERT.

Trains all three on the same data, compares macro F1 to show
the benefit of domain-specific pretraining.
"""

import json
import time
import torch
import numpy as np
from pathlib import Path
from collections import Counter
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments,
)
from sklearn.metrics import f1_score, precision_score, recall_score

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from model.train import ClauseDataset, compute_class_weights, NUM_LABELS, MAX_LENGTH


DATA_DIR = Path(__file__).parent.parent / "data" / "processed"
OUTPUT_DIR = Path(__file__).parent / "results"

# models to compare
MODELS = {
    "Legal-BERT": "nlpaueb/legal-bert-base-uncased",
    "BERT-base": "bert-base-uncased",
    "DistilBERT": "distilbert-base-uncased",
}


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    return {
        "f1": f1_score(labels, preds, average="macro"),
        "precision": precision_score(labels, preds, average="macro", zero_division=0),
        "recall": recall_score(labels, preds, average="macro", zero_division=0),
    }


def train_and_eval(model_name, train_data, val_data, test_data, run_name):
    """Train a model and return metrics."""
    print(f"\n{'=' * 60}")
    print(f"Training: {run_name} ({model_name})")
    print(f"{'=' * 60}")

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name, num_labels=NUM_LABELS
    )

    train_ds = ClauseDataset(train_data, tokenizer)
    val_ds = ClauseDataset(val_data, tokenizer)
    test_ds = ClauseDataset(test_data, tokenizer)

    device = "mps" if torch.backends.mps.is_available() else "cpu"

    output_dir = OUTPUT_DIR / "ablation" / run_name.lower().replace(" ", "_")
    training_args = TrainingArguments(
        output_dir=str(output_dir),
        num_train_epochs=3,  # fewer epochs for ablation
        per_device_train_batch_size=16,
        per_device_eval_batch_size=32,
        learning_rate=2e-5,
        warmup_ratio=0.1,
        eval_strategy="epoch",
        save_strategy="no",
        logging_steps=50,
        fp16=False,
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        compute_metrics=compute_metrics,
    )

    # train
    start = time.time()
    trainer.train()
    train_time = time.time() - start

    # evaluate on test set
    test_results = trainer.evaluate(test_ds)

    return {
        "model": run_name,
        "f1": round(test_results["eval_f1"], 4),
        "precision": round(test_results["eval_precision"], 4),
        "recall": round(test_results["eval_recall"], 4),
        "train_time_min": round(train_time / 60, 1),
    }


def run_ablation():
    """Run full ablation study."""
    # load data
    with open(DATA_DIR / "train.json") as f:
        train_data = json.load(f)
    with open(DATA_DIR / "val.json") as f:
        val_data = json.load(f)
    with open(DATA_DIR / "test.json") as f:
        test_data = json.load(f)

    print(f"Train: {len(train_data)}, Val: {len(val_data)}, Test: {len(test_data)}")

    # run each model
    results = []
    for name, model_id in MODELS.items():
        result = train_and_eval(model_id, train_data, val_data, test_data, name)
        results.append(result)
        print(f"\n{name}: F1={result['f1']}, Time={result['train_time_min']}min")

    # comparison table
    print(f"\n{'=' * 60}")
    print("ABLATION RESULTS")
    print(f"{'=' * 60}")
    print(f"{'Model':<15} {'F1':>8} {'Precision':>10} {'Recall':>8} {'Time (min)':>10}")
    print("-" * 55)
    for r in results:
        print(f"{r['model']:<15} {r['f1']:>8.4f} {r['precision']:>10.4f} {r['recall']:>8.4f} {r['train_time_min']:>10.1f}")

    # save
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_DIR / "ablation_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {OUTPUT_DIR / 'ablation_results.json'}")

    return results


if __name__ == "__main__":
    run_ablation()
