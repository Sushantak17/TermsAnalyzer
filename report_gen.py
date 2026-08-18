"""PDF report generator for FinePrint AI analysis results.

Creates a styled PDF report with summary, risk breakdown, readability,
key findings, and all clause details.
"""

from fpdf import FPDF
from datetime import datetime


def _sanitize(text):
    if not isinstance(text, str):
        return str(text)
    replacements = {
        "\u2013": "-", "\u2014": "-", "\u2018": "'", "\u2019": "'",
        "\u201c": '"', "\u201d": '"', "\u2026": "...", "\u2022": "*",
        "\u00a0": " ", "\u200b": "", "\u2011": "-", "\u2010": "-",
        "\u00b7": "*", "\u2032": "'", "\u2033": '"', "\u00ab": '"',
        "\u00bb": '"', "\u2039": "<", "\u203a": ">",
    }
    for uchar, achar in replacements.items():
        text = text.replace(uchar, achar)
    return text.encode("latin-1", errors="replace").decode("latin-1")


LABELS = {
    "fair": "Fair",
    "potentially_unfair": "Potentially Unfair",
    "unfair": "Clearly Unfair",
}

COLORS = {
    "fair": (34, 197, 94),
    "potentially_unfair": (234, 179, 8),
    "unfair": (239, 68, 68),
}


class ReportPDF(FPDF):
    """Custom PDF with header/footer."""

    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(100, 116, 139)
        self.cell(0, 8, "FinePrint AI Analysis Report", align="L")
        self.cell(0, 8, datetime.now().strftime("%B %d, %Y"), align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(226, 232, 240)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")


def generate_pdf(results, summary, readability, summary_text):
    """Generate a styled PDF report and return bytes."""
    pdf = ReportPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # -- title --
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 14, "FinePrint AI", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 7, "Terms of Service & Privacy Policy Analysis", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)

    # -- executive summary --
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 10, "Executive Summary", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(51, 65, 85)
    pdf.multi_cell(0, 6, _sanitize(summary_text))
    pdf.ln(6)

    # -- risk overview box --
    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(226, 232, 240)
    y_start = pdf.get_y()
    pdf.rect(10, y_start, 190, 36, style="DF")

    pdf.set_xy(15, y_start + 5)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(60, 7, f"Overall Risk: {summary['overall_risk']}")
    pdf.cell(60, 7, f"Risk Score: {summary['average_risk_score']}/5")
    pdf.cell(60, 7, f"Total Clauses: {summary['total_clauses']}")

    bd = summary["breakdown"]
    pdf.set_xy(15, y_start + 18)
    pdf.set_font("Helvetica", "", 9)

    pdf.set_text_color(*COLORS["fair"])
    pdf.cell(60, 7, f"Fair: {bd.get('fair', 0)}")
    pdf.set_text_color(*COLORS["potentially_unfair"])
    pdf.cell(60, 7, f"Potentially Unfair: {bd.get('potentially_unfair', 0)}")
    pdf.set_text_color(*COLORS["unfair"])
    pdf.cell(60, 7, f"Clearly Unfair: {bd.get('unfair', 0)}")

    pdf.set_y(y_start + 42)


    # -- readability --
    if readability:
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(30, 41, 59)
        pdf.cell(0, 10, "Readability Analysis", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(51, 65, 85)
        pdf.cell(0, 6, _sanitize(f"Grade Level: {readability['grade_level']} ({readability['level']} - {readability['description']})"), new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, _sanitize(f"Flesch Reading Ease: {readability['reading_ease']}/100"), new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, _sanitize(f"Word Count: {readability['word_count']}  |  Sentences: {readability['sentence_count']}"), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(6)

    # -- key findings --
    risky = sorted(
        [r for r in results if r.label != "fair"],
        key=lambda x: (x.risk_score, x.confidence), reverse=True
    )[:5]

    if risky:
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(30, 41, 59)
        pdf.cell(0, 10, "Key Findings", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

        for i, r in enumerate(risky, 1):
            label_name = LABELS.get(r.label, r.label)
            color = COLORS.get(r.label, (100, 100, 100))

            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(*color)
            pdf.cell(0, 6, _sanitize(f"#{i}  {label_name} | {r.category} | {r.confidence:.0%} confidence"), new_x="LMARGIN", new_y="NEXT")

            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(51, 65, 85)
            pdf.multi_cell(0, 5, _sanitize(r.clause))
            pdf.ln(3)

    # -- all clauses --
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 10, "All Clauses", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    # sort: unfair first
    order = {"unfair": 0, "potentially_unfair": 1, "fair": 2}
    sorted_results = sorted(results, key=lambda r: (order.get(r.label, 9), -r.confidence))

    for i, r in enumerate(sorted_results, 1):
        label_name = LABELS.get(r.label, r.label)
        color = COLORS.get(r.label, (100, 100, 100))

        # check page space
        if pdf.get_y() > 260:
            pdf.add_page()

        # clause header
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*color)
        header = f"#{i}  {label_name}"
        if r.category != "General":
            header += f" | {r.category}"
        header += f" | {r.confidence:.0%}"
        pdf.cell(0, 6, _sanitize(header), new_x="LMARGIN", new_y="NEXT")

        # clause text
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(71, 85, 105)
        pdf.multi_cell(0, 5, _sanitize(r.clause))
        pdf.ln(2)

    return bytes(pdf.output())
