import { AlertTriangle } from "lucide-react";

const LABELS = {
  fair: "Fair",
  potentially_unfair: "Potentially Unfair",
  unfair: "Clearly Unfair",
};

export default function KeyFindings({ clauses }) {
  const risky = clauses
    .filter((c) => c.label !== "fair")
    .sort((a, b) => b.risk_score - a.risk_score || b.confidence - a.confidence)
    .slice(0, 3);

  if (risky.length === 0) return null;

  return (
    <div className="card key-findings fade-up">
      <div className="section-title">
        <span className="section-icon"><AlertTriangle size={16} /></span>
        Key Findings
      </div>
      {risky.map((r, i) => (
        <div className="kf-card slide-right" key={i} style={{ animationDelay: `${i * 0.1}s` }}>
          <div className="kf-tag">
            #{i + 1} {LABELS[r.label] || r.label}
            {r.category !== "General" && ` · ${r.category}`}
            {" — "}{(r.confidence * 100).toFixed(0)}% confidence
          </div>
          <div className="kf-text">{r.clause}</div>
        </div>
      ))}
    </div>
  );
}
