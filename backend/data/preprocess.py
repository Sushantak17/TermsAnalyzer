"""Preprocess TOS_Dataset for model training.

Maps raw labels to numeric IDs, balances classes via stratified sampling,
and creates train/val/test splits saved as JSON.
"""

import json
import random
from pathlib import Path
from collections import Counter

DATA_DIR = Path(__file__).parent
RAW_DIR = DATA_DIR / "raw" / "tos_dataset"
PROCESSED_DIR = DATA_DIR / "processed"

# label mapping — adapt based on actual dataset labels
LABEL_MAP = {
    "clearly_fair": 0,
    "potentially_unfair": 1,
    "clearly_unfair": 2,
    # fallbacks for alternative label formats
    "fair": 0,
    "unfair": 2,
}

LABEL_NAMES = {0: "fair", 1: "potentially_unfair", 2: "unfair"}


def load_raw_data():
    """Load all raw JSON splits and combine."""
    records = []
    for path in sorted(RAW_DIR.glob("*.json")):
        with open(path) as f:
            data = json.load(f)
        print(f"  Loaded {len(data)} records from {path.name}")
        records.extend(data)
    return records


def detect_columns(records):
    """Figure out which columns hold the text and label."""
    sample = records[0]
    cols = list(sample.keys())
    print(f"  Columns found: {cols}")

    # find text column
    text_col = None
    for candidate in ["sentence", "text", "clause", "content", "input"]:
        if candidate in cols:
            text_col = candidate
            break
    if not text_col:
        # pick the longest string field
        text_col = max(cols, key=lambda c: len(str(sample.get(c, ""))))

    # find label column
    label_col = None
    for candidate in ["unfairness_level", "label", "labels", "class", "classification", "fairness"]:
        if candidate in cols:
            label_col = candidate
            break
    if not label_col:
        label_col = [c for c in cols if c != text_col][0]

    print(f"  Using text_col='{text_col}', label_col='{label_col}'")
    return text_col, label_col


def normalize_label(raw_label):
    """Convert raw label string to numeric ID."""
    if isinstance(raw_label, int):
        if raw_label in LABEL_NAMES:
            return raw_label
        return None

    label_str = str(raw_label).lower().strip().replace(" ", "_")
    return LABEL_MAP.get(label_str, None)


def preprocess(records, text_col, label_col):
    """Clean text and map labels to numeric IDs."""
    processed = []
    skipped = 0

    for rec in records:
        text = str(rec.get(text_col, "")).strip()
        raw_label = rec.get(label_col)
        label = normalize_label(raw_label)

        # skip empty or unmappable
        if not text or len(text) < 10 or label is None:
            skipped += 1
            continue

        processed.append({"text": text, "label": label})

    print(f"  Processed: {len(processed)}, Skipped: {skipped}")
    return processed


def stratified_split(data, train_ratio=0.8, val_ratio=0.1, seed=42):
    """Split data into train/val/test preserving class distribution."""
    random.seed(seed)

    # group by label
    groups = {}
    for item in data:
        groups.setdefault(item["label"], []).append(item)

    train, val, test = [], [], []

    for label, items in groups.items():
        random.shuffle(items)
        n = len(items)
        n_train = int(n * train_ratio)
        n_val = int(n * val_ratio)

        train.extend(items[:n_train])
        val.extend(items[n_train:n_train + n_val])
        test.extend(items[n_train + n_val:])

    # shuffle each split
    random.shuffle(train)
    random.shuffle(val)
    random.shuffle(test)

    return train, val, test


def print_stats(name, data):
    """Print class distribution for a split."""
    counts = Counter(d["label"] for d in data)
    total = len(data)
    print(f"  {name}: {total} samples")
    for label_id in sorted(counts):
        pct = counts[label_id] / total * 100
        print(f"    {LABEL_NAMES[label_id]}: {counts[label_id]} ({pct:.1f}%)")


if __name__ == "__main__":
    print("Loading raw data...")
    records = load_raw_data()

    print("\nDetecting schema...")
    text_col, label_col = detect_columns(records)

    # peek at label distribution before mapping
    raw_labels = [r.get(label_col) for r in records]
    print(f"  Raw label values: {Counter(raw_labels).most_common(10)}")

    print("\nPreprocessing...")
    processed = preprocess(records, text_col, label_col)

    print("\nSplitting (80/10/10)...")
    train, val, test = stratified_split(processed)

    print("\nClass distributions:")
    print_stats("Train", train)
    print_stats("Val", val)
    print_stats("Test", test)

    # save splits
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    for name, split in [("train", train), ("val", val), ("test", test)]:
        path = PROCESSED_DIR / f"{name}.json"
        with open(path, "w") as f:
            json.dump(split, f, indent=2)
        print(f"\nSaved {name} → {path}")

    print("\nPreprocessing complete!")
