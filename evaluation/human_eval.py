"""Human evaluation — 50-clause agreement study.

Presents random clauses for manual labeling, then compares
your labels against the model's predictions. Reports Cohen's Kappa
and a disagreement analysis.
"""

import json
import random
import sys
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent.parent))

from sklearn.metrics import cohen_kappa_score, classification_report


DATA_DIR = Path(__file__).parent.parent / "data" / "processed"
OUTPUT_DIR = Path(__file__).parent / "results"
LABELS = ["fair", "potentially_unfair", "unfair"]
LABEL_MAP = {"f": "fair", "p": "potentially_unfair", "u": "unfair"}
N_SAMPLES = 50


def load_samples():
    """Pick 50 random clauses from the test set."""
    with open(DATA_DIR / "test.json") as f:
        data = json.load(f)

    random.seed(42)
    samples = random.sample(data, min(N_SAMPLES, len(data)))
    return samples


def interactive_labeling(samples):
    """Present clauses one by one for manual labeling."""
    print("=" * 60)
    print("HUMAN EVALUATION — Label each clause")
    print("Options: [f]air, [p]otentially unfair, [u]nfair, [s]kip")
    print("=" * 60)

    human_labels = []

    for i, sample in enumerate(samples):
        print(f"\n--- Clause {i + 1}/{len(samples)} ---")
        print(f"Text: {sample['text'][:300]}")
        print()

        while True:
            choice = input("Your label (f/p/u/s): ").strip().lower()
            if choice in LABEL_MAP:
                human_labels.append(LABEL_MAP[choice])
                break
            elif choice == "s":
                human_labels.append(None)
                break
            print("Invalid input. Use f, p, u, or s.")

    return human_labels


def analyze_agreement(samples, human_labels, model_labels):
    """Calculate agreement metrics and find disagreements."""
    # filter out skipped
    valid = [(h, m, s) for h, m, s in zip(human_labels, model_labels, samples) if h is not None]
    if not valid:
        print("No valid labels to compare.")
        return

    h_labels = [v[0] for v in valid]
    m_labels = [v[1] for v in valid]
    texts = [v[2]["text"] for v in valid]

    # Cohen's Kappa
    kappa = cohen_kappa_score(h_labels, m_labels)
    print(f"\n{'=' * 60}")
    print(f"Cohen's Kappa: {kappa:.4f}")
    if kappa > 0.8:
        print("Interpretation: Almost perfect agreement")
    elif kappa > 0.6:
        print("Interpretation: Substantial agreement")
    elif kappa > 0.4:
        print("Interpretation: Moderate agreement")
    else:
        print("Interpretation: Fair/poor agreement")

    # classification report (treating human as ground truth)
    print(f"\n{'=' * 60}")
    print("Classification Report (human = ground truth)")
    print(classification_report(h_labels, m_labels, zero_division=0))

    # disagreements
    disagreements = []
    for h, m, text in zip(h_labels, m_labels, texts):
        if h != m:
            disagreements.append({
                "text": text[:200],
                "human_label": h,
                "model_label": m,
            })

    print(f"\nDisagreements: {len(disagreements)}/{len(valid)}")
    for d in disagreements:
        print(f"\n  Text: {d['text']}")
        print(f"  Human: {d['human_label']} | Model: {d['model_label']}")

    # save results
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results = {
        "cohens_kappa": kappa,
        "total_labeled": len(valid),
        "agreements": len(valid) - len(disagreements),
        "disagreements": disagreements,
    }
    with open(OUTPUT_DIR / "human_eval_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {OUTPUT_DIR / 'human_eval_results.json'}")


if __name__ == "__main__":
    # import here to avoid loading model unnecessarily
    from model.predict import ClauseClassifier, LABEL_MAP as MODEL_LABEL_MAP

    print("Loading model...")
    classifier = ClauseClassifier()

    print("Selecting samples...")
    samples = load_samples()

    # get model predictions first
    texts = [s["text"] for s in samples]
    model_preds = classifier.predict(texts)
    model_labels = [p["label"] for p in model_preds]

    # interactive labeling
    human_labels = interactive_labeling(samples)

    # analyze
    analyze_agreement(samples, human_labels, model_labels)
