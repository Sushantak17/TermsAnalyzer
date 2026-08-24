import io
import json
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from pipeline import TermsAnalyzer
from report_gen import generate_pdf

app = FastAPI(title="TermsAnalyzer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_origin_regex=r"^chrome-extension://.*$",
    allow_methods=["*"],
    allow_headers=["*"],
)

analyzer = TermsAnalyzer()

LABELS = {"fair": "Fair", "potentially_unfair": "Potentially Unfair", "unfair": "Clearly Unfair"}


def build_response(results, raw_text=None):
    if not results:
        raise HTTPException(status_code=400, detail="No clauses could be extracted")

    summary = TermsAnalyzer.summarize(results)
    doc_text = raw_text or " ".join(r.clause for r in results)
    readability = TermsAnalyzer.readability(doc_text)
    summary_text = TermsAnalyzer.generate_summary_text(results, summary)
    clauses = TermsAnalyzer.to_dicts(results)

    return {
        "clauses": clauses,
        "summary": summary,
        "readability": readability,
        "summary_text": summary_text,
        "raw_text": doc_text,
    }


class TextInput(BaseModel):
    text: str

class UrlInput(BaseModel):
    url: str


@app.post("/api/analyze/text")
def analyze_text(body: TextInput):
    if not body.text.strip():
        raise HTTPException(status_code=400, detail="Text is empty")
    results = analyzer.analyze_text(body.text)
    return build_response(results, body.text)


@app.post("/api/analyze/url")
def analyze_url(body: UrlInput):
    if not body.url.strip():
        raise HTTPException(status_code=400, detail="URL is empty")
    try:
        import trafilatura
        downloaded = trafilatura.fetch_url(body.url)
        raw_text = trafilatura.extract(downloaded) if downloaded else None
        results = analyzer.analyze_url(body.url)
        return build_response(results, raw_text)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/analyze/pdf")
async def analyze_pdf(file: UploadFile = File(...)):
    pdf_bytes = await file.read()
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        raw_text = "".join(p.extract_text() or "" for p in reader.pages)
        results = analyzer.analyze_pdf(pdf_bytes)
        return build_response(results, raw_text)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


class ReportInput(BaseModel):
    clauses: list
    summary: dict
    readability: dict
    summary_text: str

@app.post("/api/report/pdf")
def generate_report(body: ReportInput):
    from dataclasses import dataclass, field

    @dataclass
    class Clause:
        clause: str
        label: str
        confidence: float
        risk_score: int
        category: str = "General"
        explanations: list = field(default_factory=list)

    results = [Clause(**c) for c in body.clauses]
    pdf_bytes = generate_pdf(results, body.summary, body.readability, body.summary_text)
    return Response(content=pdf_bytes, media_type="application/pdf",
                    headers={"Content-Disposition": "attachment; filename=termsanalyzer_report.pdf"})
