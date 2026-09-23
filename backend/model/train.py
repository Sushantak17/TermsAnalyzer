"""Fine-tune Legal-BERT for clause fairness classification.

Trains on the preprocessed TOS_Dataset with weighted loss
to handle class imbalance. Uses MPS on Apple Silicon.
"""

import json
import torch
import numpy as np
from pathlib import Path
from collections import Counter
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments,
    EarlyStoppingCallback,
)
from sklearn.metrics import f1_score, precision_score, recall_score
from torch.utils.data import Dataset


DATA_DIR = Path(__file__).parent.parent / "data" / "processed"
CHECKPOINT_DIR = Path(__file__).parent / "checkpoints" / "best"
MODEL_NAME = "nlpaueb/legal-bert-base-uncased"
NUM_LABELS = 3
MAX_LENGTH = 256


class ClauseDataset(Dataset):
    """Simple dataset for clause classification."""

    def __init__(self, records, tokenizer):
        self.records = records
        self.tokenizer = tokenizer

    def __len__(self):
        return len(self.records)

    def __getitem__(self, idx):
        rec = self.records[idx]
        encoding = self.tokenizer(
            rec["text"],
            truncation=True,
            max_length=MAX_LENGTH,
            padding="max_length",
            return_tensors="pt",
        )
        return {
            "input_ids": encoding["input_ids"].squeeze(),
            "attention_mask": encoding["attention_mask"].squeeze(),
            "labels": torch.tensor(rec["label"], dtype=torch.long),
        }


def get_device():
    """Pick the best available device."""
    if torch.backends.mps.is_available():
        print("Using MPS (Apple Silicon GPU)")
        return "mps"
    elif torch.cuda.is_available():
        print("Using CUDA")
        return "cuda"
    print("Using CPU")
    return "cpu"


def compute_class_weights(records):
    """Calculate inverse-frequency weights for imbalanced classes."""
    counts = Counter(r["label"] for r in records)
    total = sum(counts.values())
    weights = {label: total / count for label, count in counts.items()}

    # normalize so average weight = 1
    avg = sum(weights.values()) / len(weights)
    weights = {k: v / avg for k, v in weights.items()}

    print(f"Class weights: {weights}")
    return torch.tensor([weights[i] for i in range(NUM_LABELS)], dtype=torch.float32)


def compute_metrics(eval_pred):
    """Calculate macro P/R/F1 for evaluation."""
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    return {
        "f1": f1_score(labels, preds, average="macro"),
        "precision": precision_score(labels, preds, average="macro", zero_division=0),
        "recall": recall_score(labels, preds, average="macro", zero_division=0),
    }


class WeightedTrainer(Trainer):
    """Trainer with weighted cross-entropy for class imbalance."""

    def __init__(self, class_weights=None, **kwargs):
        super().__init__(**kwargs)
        self.class_weights = class_weights

    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        labels = inputs.pop("labels")
        outputs = model(**inputs)
        logits = outputs.logits

        if self.class_weights is not None:
            weight = self.class_weights.to(logits.device)
            loss = torch.nn.functional.cross_entropy(logits, labels, weight=weight)
        else:
            loss = torch.nn.functional.cross_entropy(logits, labels)

        return (loss, outputs) if return_outputs else loss


def train():
    """Main training loop."""
    device = get_device()

    # load preprocessed data
    print("Loading data...")
    with open(DATA_DIR / "train.json") as f:
        train_data = json.load(f)
    with open(DATA_DIR / "val.json") as f:
        val_data = json.load(f)

    print(f"Train: {len(train_data)}, Val: {len(val_data)}")

    # tokenizer and model
    print(f"Loading {MODEL_NAME}...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME, num_labels=NUM_LABELS
    )

    # datasets
    train_ds = ClauseDataset(train_data, tokenizer)
    val_ds = ClauseDataset(val_data, tokenizer)

    # class weights for imbalanced data
    class_weights = compute_class_weights(train_data)

    # MPS doesn't support fp16, so we use fp32
    use_fp16 = device == "cuda"

    training_args = TrainingArguments(
        output_dir=str(Path(__file__).parent / "checkpoints"),
        num_train_epochs=5,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=32,
        learning_rate=2e-5,
        warmup_ratio=0.1,
        weight_decay=0.01,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        greater_is_better=True,
        logging_steps=20,
        fp16=use_fp16,
        save_total_limit=2,
        report_to="none",
    )

    trainer = WeightedTrainer(
        class_weights=class_weights,
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        compute_metrics=compute_metrics,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=2)],
    )

    # train
    print("\nStarting training...")
    trainer.train()

    # save best model
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(CHECKPOINT_DIR))
    tokenizer.save_pretrained(str(CHECKPOINT_DIR))
    print(f"\nBest model saved to {CHECKPOINT_DIR}")

    # quick eval on validation set
    results = trainer.evaluate()
    print(f"\nValidation results: {results}")

    return results


if __name__ == "__main__":
    train()
