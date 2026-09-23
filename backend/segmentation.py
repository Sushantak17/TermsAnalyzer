"""Clause segmentation — splits raw text into clause-level chunks.

Uses spaCy for sentence splitting, then merges very short consecutive
sentences so we don't classify fragments.
"""

import re
import spacy

# load spacy once at import time
nlp = spacy.load("en_core_web_sm")

MIN_TOKENS = 8    # sentences shorter than this get merged
MAX_TOKENS = 200  # don't merge past this length


def segment(text):
    """Split raw text into clause-level chunks."""
    # clean up common formatting issues
    text = clean_text(text)
    if not text.strip():
        return []

    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]

    # merge very short sentences with neighbors
    clauses = merge_short(sentences)

    # drop anything too short to be a real clause
    clauses = [c for c in clauses if len(c.split()) >= 8]

    # drop headings and boilerplate (no verb / too short to be a clause)
    clauses = [c for c in clauses if not _is_heading(c)]

    return clauses


def _is_heading(text):
    """Heuristic: detect headings, dates, and boilerplate that aren't real clauses."""
    text_lower = text.lower().strip()

    boilerplate_markers = [
        "terms of use", "terms of service", "privacy policy",
        "thank you for", "welcome to", "table of contents",
        "last modified", "effective date", "previous version",
        "cookie policy", "acceptable use", "end user license",
    ]

    # Check the whole text
    if re.match(r"^(effective|last updated|updated|date)[:\s]", text_lower):
        return True

    # Check each line individually — merged clauses may have multiple heading lines
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if not lines:
        return True

    # If ALL lines are short boilerplate fragments, drop the whole clause
    non_heading_lines = 0
    for line in lines:
        line_lower = line.lower()
        line_words = len(line.split())

        is_boilerplate = (
            line_words < 10 and any(m in line_lower for m in boilerplate_markers)
        ) or (
            line_words < 5  # very short fragment like "Terms of Use"
        ) or (
            re.match(r"^(effective|last updated|updated|date)[:\s]", line_lower)
        )

        if not is_boilerplate:
            non_heading_lines += 1

    # If no substantive lines, it's all headings/boilerplate
    return non_heading_lines == 0


def clean_text(text):
    """Basic text cleanup for ToS/privacy policy documents."""
    # collapse multiple newlines into paragraph breaks
    text = re.sub(r"\n{3,}", "\n\n", text)
    # remove page numbers and headers like "Page 3 of 10"
    text = re.sub(r"Page \d+ of \d+", "", text)
    # normalize whitespace
    text = re.sub(r"[ \t]+", " ", text)
    # handle numbered lists (1. or (a) style)
    text = re.sub(r"(\n\s*\d+[\.\)]\s*)", r"\n", text)
    return text.strip()


def merge_short(sentences):
    """Combine short consecutive sentences into one clause."""
    if not sentences:
        return []

    clauses = []
    buffer = sentences[0]

    for sent in sentences[1:]:
        buffer_len = len(buffer.split())
        combined_len = buffer_len + len(sent.split())

        # merge if current buffer is short and combined isn't too long
        if buffer_len < MIN_TOKENS and combined_len <= MAX_TOKENS:
            buffer = buffer + " " + sent
        else:
            clauses.append(buffer)
            buffer = sent

    clauses.append(buffer)
    return clauses
