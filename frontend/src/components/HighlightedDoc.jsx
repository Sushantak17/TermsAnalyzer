const LABELS = {
  fair: "Fair",
  potentially_unfair: "Potentially Unfair",
  unfair: "Clearly Unfair",
};

export default function HighlightedDoc({ rawText, clauses }) {
  if (!rawText) return null;

  const risky = clauses
    .filter((c) => c.label !== "fair")
    .sort((a, b) => b.clause.length - a.clause.length);

  let highlighted = rawText;
  for (const r of risky) {
    if (highlighted.includes(r.clause)) {
      highlighted = highlighted.replace(
        r.clause,
        `<mark class="hl-${r.label}" title="${LABELS[r.label] || r.label}">${r.clause}</mark>`
      );
    }
  }

  highlighted = highlighted.replace(/\n/g, "<br/>");

  return (
    <div className="card fade-up">
      <div className="section-title">
        <span className="section-icon"><HighlightIcon /></span>
        Document Highlighting
      </div>
      <div
        className="highlight-box"
        dangerouslySetInnerHTML={{ __html: highlighted }}
      />
    </div>
  );
}

function HighlightIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="m9 11-6 6v3h9l3-3" /><path d="m22 12-4.6 4.6a2 2 0 0 1-2.8 0l-5.2-5.2a2 2 0 0 1 0-2.8L14 4" />
    </svg>
  );
}
