const STEP_LABELS = [
  "Segmenting clauses",
  "Classifying with Legal-BERT",
  "Retrieving RAG explanations",
  "Generating report",
];

export default function LoadingOverlay({ step = 0 }) {
  return (
    <div className="loading-overlay fade-in">
      <div className="loading-dots">
        <span className="loading-dot" />
        <span className="loading-dot" />
        <span className="loading-dot" />
      </div>
      <div className="loading-steps">
        {STEP_LABELS.map((label, i) => (
          <div
            key={i}
            className={`loading-step-bar ${
              i < step ? "done" : i === step ? "active" : "pending"
            }`}
          />
        ))}
      </div>
      <div className="loading-label">{STEP_LABELS[Math.min(step, 3)]}...</div>
    </div>
  );
}
