# TermsAnalyzer

**AI-powered Terms of Service & Privacy Policy Analyzer**

TermsAnalyzer automatically reads ToS/Privacy Policy documents, identifies potentially unfair or risky clauses, and explains *why* they're problematic using real-world examples from the [ToS;DR](https://tosdr.org) project.

![Python 3.13](https://img.shields.io/badge/Python-3.13-blue)
![Legal-BERT](https://img.shields.io/badge/Model-Legal--BERT-green)
![React](https://img.shields.io/badge/Frontend-React-61DAFB)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688)

---

## How It Works

```
Input (URL / Text / PDF)
    ↓
Text Extraction (trafilatura / PyPDF2)
    ↓
Clause Segmentation (spaCy)
    ↓
Risk Classification (Fine-tuned Legal-BERT)
    ↓
RAG Explanations (FAISS + ToS;DR knowledge base)
    ↓
Color-Coded Results + Export
```

### Key Components

1. **Clause Segmentation** — spaCy-based sentence splitting with a merging heuristic that combines short fragments into meaningful clauses
2. **Risk Classification** — Legal-BERT (`nlpaueb/legal-bert-base-uncased`) fine-tuned on the [TOS_Dataset](https://huggingface.co/datasets/CodeHima/TOS_Dataset) for 3-class fairness classification
3. **RAG Explanations** — When a clause is flagged, we retrieve the most similar previously-annotated clause from the ToS;DR knowledge base and show its explanation. This uses sentence-transformers + FAISS for fast similarity search.

---

## Setup

```bash
# clone and enter project
git clone https://github.com/yourusername/termsanalyzer.git
cd termsanalyzer

# create virtual environment
python3 -m venv venv
source venv/bin/activate

# install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

## Training the Model

```bash
# step 1: download datasets
python backend/data/download_data.py

# step 2: preprocess (clean, split, balance)
python backend/data/preprocess.py

# step 3: fine-tune Legal-BERT (~15-25 min on Apple Silicon)
python backend/model/train.py

# step 4: evaluate
python backend/model/evaluate.py

# step 5: build RAG index
python backend/data/build_rag_index.py
```

## Running the App

```bash
# option 1: use the run script (starts both backend + frontend)
./run.sh

# option 2: start manually
# terminal 1 — backend
uvicorn server:app --reload --port 8000

# terminal 2 — frontend
cd frontend && npm run dev
```

Open `http://localhost:5173` — paste a ToS URL, upload a PDF, or paste text directly.

## Browser Extension

Analyze any ToS/Privacy Policy page directly in Chrome:

1. Start the backend: `uvicorn server:app --port 8000`
2. Go to `chrome://extensions` → enable **Developer mode**
3. Click **Load unpacked** → select the `extension/` folder
4. Navigate to any ToS page and click the TermsAnalyzer icon
5. Click **"Analyze This Page"** in the side panel

Features: risk classification, RAG explanations, clause filtering, and in-page highlighting of flagged clauses.

---

## Evaluation

### Model Comparison (3-epoch, validation set)
### Model Comparison (3-epoch, validation set)

| Metric | Legal-BERT | BERT-base | DistilBERT |
|--------|-----------|-----------|------------|
| Macro F1 | **0.8153** | 0.8213 | 0.8313 |
| Precision | **0.8265** | 0.8244 | 0.8370 |
| Recall | **0.8096** | 0.8184 | 0.8265 |
| Training Time | **45.8 min** | 108.6 min | 25.7 min |

> **Note:** Models were compared using **validation set** metrics for model selection (test set reserved for final unbiased evaluation). DistilBERT achieves the highest validation F1 (0.831) while being 2× faster than Legal-BERT and 4× faster than BERT-base. The production model uses Legal-BERT (fine-tuned for 5 epochs) for its domain robustness on complex legal text.

### Production Model (Legal-BERT, 5 epochs)

| Class | Precision | Recall | F1-Score | Support |
|-------|-----------|--------|----------|---------|
| Fair | 0.893 | 0.901 | 0.897 | 493 |
| Potentially Unfair | 0.737 | 0.826 | 0.779 | 247 |
| Unfair | 0.854 | 0.733 | 0.789 | 240 |
| **Macro Avg** | **0.828** | **0.820** | **0.822** | **980** |

**Overall Accuracy:** 84.1% on 980 held-out test samples.

---

## Datasets

| Dataset | Purpose | Source |
|---------|---------|--------|
| TOS_Dataset | Model training (clause fairness) | [HuggingFace](https://huggingface.co/datasets/CodeHima/TOS_Dataset) |
| ToS;DR Cases | RAG knowledge base | [tosdr.org](https://tosdr.org) |
| CUAD | Benchmark comparison | [Atticus Project](https://www.atticusprojectai.org/cuad) |

---

## Project Structure

```
TermsAnalyzer/
├── run.sh                  # Launch script (backend + frontend)
├── requirements.txt        # Python dependencies
├── backend/                # Python backend
│   ├── server.py           # FastAPI REST API
│   ├── pipeline.py         # End-to-end analysis orchestration
│   ├── segmentation.py     # Clause segmentation (spaCy)
│   ├── report_gen.py       # PDF report generator
│   ├── model/
│   │   ├── train.py        # Legal-BERT fine-tuning
│   │   ├── evaluate.py     # Per-class metrics + confusion matrix
│   │   └── predict.py      # Inference module
│   ├── rag/
│   │   └── explainer.py    # RAG retrieval for explanations
│   ├── data/
│   │   ├── download_data.py    # Dataset fetching
│   │   ├── preprocess.py       # Data cleaning and splitting
│   │   └── build_rag_index.py  # FAISS index construction
│   └── evaluation/
│       ├── human_eval.py   # 50-clause agreement study
│       └── ablation.py     # Model comparison study
├── frontend/               # React + Vite UI
│   ├── src/
│   │   ├── App.jsx         # Main app component
│   │   ├── components/     # UI components
│   │   └── api/            # API client
│   └── package.json
└── extension/              # Chrome Extension (Manifest V3)
    ├── manifest.json       # Extension config
    ├── service-worker.js   # Background script
    ├── content-script.js   # In-page highlighting logic
    └── sidepanel/          # Side panel UI
```

---

## Tech Stack

- **Model**: Legal-BERT (fine-tuned) — domain-specific transformer pretrained on legal text
- **RAG**: sentence-transformers (`all-MiniLM-L6-v2`) + FAISS for similarity search
- **NLP**: spaCy for clause segmentation
- **Backend**: FastAPI with uvicorn
- **Frontend**: React + Vite
- **Training**: HuggingFace Transformers + Trainer API, MPS acceleration on Apple Silicon

---

## Limitations

- Trained on English ToS/Privacy Policies only
- Clause segmentation uses heuristics — complex legal formatting may cause splitting errors
- RAG explanations are limited to the ToS;DR knowledge base coverage
- Model confidence scores should not be interpreted as legal advice

## Future Work

- Support for CUAD-style commercial contract analysis
- Multi-language support
- Fine-grained subcategory classification (data-sharing, arbitration, tracking, etc.)

---

## License

MIT

## Acknowledgments

- [ToS;DR Project](https://tosdr.org) for their crowdsourced annotations
- [LEGAL-BERT](https://huggingface.co/nlpaueb/legal-bert-base-uncased) by NLP@AUEB
- [TOS_Dataset](https://huggingface.co/datasets/CodeHima/TOS_Dataset) on HuggingFace
