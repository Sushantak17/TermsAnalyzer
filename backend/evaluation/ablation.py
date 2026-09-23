"""Model comparison — compare Legal-BERT vs DistilBERT vs vanilla BERT.

Trains all three on the same data, compares macro F1 on the
**validation set** for model selection, then evaluates the
winning model on the held-out test set for unbiased reporting.
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


def train_and_eval(model_name, train_data, val_data, run_name):
    """Train a model and return validation metrics (NOT test metrics)."""
    print(f"\n{'=' * 60}")
    print(f"Training: {run_name} ({model_name})")
    print(f"{'=' * 60}")

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name, num_labels=NUM_LABELS
    )

    train_ds = ClauseDataset(train_data, tokenizer)
    val_ds = ClauseDataset(val_data, tokenizer)

    device = "mps" if torch.backends.mps.is_available() else "cpu"

    output_dir = OUTPUT_DIR / "model_comparison" / run_name.lower().replace(" ", "_")
    training_args = TrainingArguments(
        output_dir=str(output_dir),
        num_train_epochs=3,
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

    # evaluate on VALIDATION set for model selection
    val_results = trainer.evaluate(val_ds)

    return {
        "model": run_name,
        "val_f1": round(val_results["eval_f1"], 4),
        "val_precision": round(val_results["eval_precision"], 4),
        "val_recall": round(val_results["eval_recall"], 4),
        "train_time_min": round(train_time / 60, 1),
        "trainer": trainer,  # keep trainer for test evaluation of winner
    }


def run_comparison():
    """Run full model comparison study."""
    # load data
    with open(DATA_DIR / "train.json") as f:
        train_data = json.load(f)
    with open(DATA_DIR / "val.json") as f:
        val_data = json.load(f)
    with open(DATA_DIR / "test.json") as f:
        test_data = json.load(f)

    print(f"Train: {len(train_data)}, Val: {len(val_data)}, Test: {len(test_data)}")

    # --- Phase 1: Train all models, compare on VALIDATION set ---
    print("\n" + "=" * 60)
    print("PHASE 1: Model Selection (using validation set)")
    print("=" * 60)

    results = []
    trainers = {}
    for name, model_id in MODELS.items():
        result = train_and_eval(model_id, train_data, val_data, name)
        trainers[name] = result.pop("trainer")  # separate trainer from results
        results.append(result)
        print(f"\n{name}: Val F1={result['val_f1']}, Time={result['train_time_min']}min")

    # comparison table (validation metrics)
    print(f"\n{'=' * 60}")
    print("MODEL COMPARISON RESULTS (Validation Set)")
    print(f"{'=' * 60}")
    print(f"{'Model':<15} {'Val F1':>8} {'Precision':>10} {'Recall':>8} {'Time (min)':>10}")
    print("-" * 55)
    for r in results:
        print(f"{r['model']:<15} {r['val_f1']:>8.4f} {r['val_precision']:>10.4f} {r['val_recall']:>8.4f} {r['train_time_min']:>10.1f}")

    # --- Phase 2: Final test evaluation on the WINNING model only ---
    winner = max(results, key=lambda r: r["val_f1"])
    print(f"\n{'=' * 60}")
    print(f"PHASE 2: Final Test Evaluation — Winner: {winner['model']}")
    print(f"{'=' * 60}")

    winner_tokenizer = AutoTokenizer.from_pretrained(MODELS[winner["model"]])
    test_ds = ClauseDataset(test_data, winner_tokenizer)
    test_results = trainers[winner["model"]].evaluate(test_ds)

    winner["test_f1"] = round(test_results["eval_f1"], 4)
    winner["test_precision"] = round(test_results["eval_precision"], 4)
    winner["test_recall"] = round(test_results["eval_recall"], 4)

    print(f"\n{winner['model']} Test Set Results:")
    print(f"  F1:        {winner['test_f1']}")
    print(f"  Precision: {winner['test_precision']}")
    print(f"  Recall:    {winner['test_recall']}")

    # save
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    save_data = {
        "methodology": "Models compared on validation set. Test set evaluated only on the winning model.",
        "comparison_results": results,
        "winner": winner["model"],
        "test_results": {
            "model": winner["model"],
            "f1": winner["test_f1"],
            "precision": winner["test_precision"],
            "recall": winner["test_recall"],
        },
    }
    with open(OUTPUT_DIR / "model_comparison_results.json", "w") as f:
        json.dump(save_data, f, indent=2)
    print(f"\nResults saved to {OUTPUT_DIR / 'model_comparison_results.json'}")

    return results


if __name__ == "__main__":
    run_comparison()
