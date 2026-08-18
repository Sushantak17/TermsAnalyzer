"""End-to-end analysis pipeline.

Orchestrates: text extraction -> clause segmentation -> classification -> RAG lookup.
Includes readability scoring and plain-English summary generation.
"""

import io
import trafilatura
import PyPDF2
import textstat
from dataclasses import dataclass, field, asdict
from typing import List

from segmentation import segment
from model.predict import ClauseClassifier
from rag.explainer import RAGExplainer


@dataclass
class AnalyzedClause:
    """Result for a single analyzed clause."""
    clause: str
    label: str
    confidence: float
    risk_score: int
    category: str = "General"
    explanations: list = field(default_factory=list)


class FinePrintAnalyzer:
    """Full analysis pipeline: raw text -> analyzed clauses with explanations."""

    def __init__(self, model_path=None, index_path=None, metadata_path=None):
        self.classifier = ClauseClassifier(model_path)
        self.explainer = RAGExplainer(index_path, metadata_path)

    def analyze_text(self, text):
        """Analyze raw text and return clause-level results."""
        clauses = segment(text)
        if not clauses:
            return []

        predictions = self.classifier.predict(clauses)

        # add RAG explanations and category for flagged clauses
        results = []
        for pred in predictions:
            explanations = []
            category = "General"

            if pred["label"] != "fair":
                explanations = self.explainer.explain(pred["clause"], top_k=3)
                # use top RAG match's category as clause category
                if explanations:
                    category = explanations[0].get("category", "General")

            results.append(AnalyzedClause(
                clause=pred["clause"],
                label=pred["label"],
                confidence=pred["confidence"],
                risk_score=pred["risk_score"],
                category=category,
                explanations=explanations,
            ))

        return results

    def analyze_url(self, url):
        """Fetch a URL and analyze its text content."""
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            raise ValueError(f"Could not fetch URL: {url}")

        text = trafilatura.extract(downloaded)
        if not text:
            raise ValueError(f"Could not extract text from: {url}")

        return self.analyze_text(text)

    def analyze_pdf(self, pdf_bytes):
        """Extract text from PDF bytes and analyze."""
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""

        if not text.strip():
            raise ValueError("Could not extract text from PDF")

        return self.analyze_text(text)

    @staticmethod
    def readability(text):
        """Compute readability metrics for the full document."""
        grade = textstat.flesch_kincaid_grade(text)
        ease = textstat.flesch_reading_ease(text)

        if grade <= 8:
            level = "Easy"
            desc = "Readable by most adults"
        elif grade <= 12:
            level = "Moderate"
            desc = "High school reading level"
        elif grade <= 16:
            level = "Difficult"
            desc = "College-level reading required"
        else:
            level = "Very Difficult"
            desc = "Graduate-level reading required"

        return {
            "grade_level": round(grade, 1),
            "reading_ease": round(ease, 1),
            "level": level,
            "description": desc,
            "word_count": textstat.lexicon_count(text),
            "sentence_count": textstat.sentence_count(text),
        }

    @staticmethod
    def generate_summary_text(results, summary):
        """Generate a plain-English summary of the analysis."""
        bd = summary["breakdown"]
        total = summary["total_clauses"]
        n_unfair = bd.get("unfair", 0)
        n_risky = bd.get("potentially_unfair", 0)
        n_fair = bd.get("fair", 0)

        # opening sentence
        if n_unfair == 0 and n_risky == 0:
            opening = f"This document contains {total} clauses, all of which appear fair and standard."
        elif n_unfair == 0:
            opening = f"This document contains {total} clauses. {n_risky} clause{'s' if n_risky != 1 else ''} may be potentially unfair to users."
        else:
            opening = f"This document contains {total} clauses. {n_unfair} {'are' if n_unfair != 1 else 'is'} clearly unfair and {n_risky} {'are' if n_risky != 1 else 'is'} potentially unfair."

        # key concerns from top risky clauses
        risky = sorted(
            [r for r in results if r.label != "fair"],
            key=lambda x: (x.risk_score, x.confidence), reverse=True
        )[:3]

        concerns = []
        for r in risky:
            cat = r.category if r.category != "General" else "policy terms"
            # create short description from the clause
            short = r.clause[:120].rstrip()
            if len(r.clause) > 120:
                short += "..."
            concerns.append(f"{cat.lower()} ({short})")

        if concerns:
            concern_text = "Key concerns include: " + "; ".join(concerns) + "."
        else:
            concern_text = "No significant concerns were identified."

        # risk verdict
        risk = summary["overall_risk"]
        verdict = f"Overall, this document is rated as {risk} with an average risk score of {summary['average_risk_score']}/5."

        return f"{opening} {concern_text} {verdict}"

    @staticmethod
    def summarize(results):
        """Generate overall risk summary from analyzed clauses."""
        if not results:
            return {
                "overall_risk": "N/A",
                "average_risk_score": 0,
                "total_clauses": 0,
                "breakdown": {},
            }

        total = len(results)
        breakdown = {"fair": 0, "potentially_unfair": 0, "unfair": 0}
        for r in results:
            breakdown[r.label] += 1

        avg_risk = sum(r.risk_score for r in results) / total

        # overall verdict
        if avg_risk <= 1.5:
            overall = "Low Risk"
        elif avg_risk <= 2.5:
            overall = "Medium Risk"
        elif avg_risk <= 3.5:
            overall = "High Risk"
        else:
            overall = "Very High Risk"

        return {
            "overall_risk": overall,
            "average_risk_score": round(avg_risk, 2),
            "total_clauses": total,
            "breakdown": breakdown,
        }

    @staticmethod
    def to_dicts(results):
        """Convert results to plain dicts (for JSON export)."""
        return [asdict(r) for r in results]
