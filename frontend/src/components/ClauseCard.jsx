import { useState } from "react";
import { ChevronDown, Building2, ArrowUpRight } from "lucide-react";

const LABELS = {
  fair: "Fair",
  potentially_unfair: "Potentially Unfair",
  unfair: "Clearly Unfair",
};

export default function ClauseCard({ clause, index }) {
  const hasRag = clause.explanations?.length > 0;
  const [expanded, setExpanded] = useState(hasRag && clause.label !== "fair");
  const confPct = (clause.confidence * 100).toFixed(0);

  return (
    <div
      className={`clause-card clause-${clause.label} fade-up`}
      style={{ animationDelay: `${index * 0.04}s` }}
    >
      <div className="clause-header">
        <span className="clause-idx">#{index}</span>
        <span className={`badge badge-${clause.label}`}>{LABELS[clause.label]}</span>
        {clause.category !== "General" && (
          <span className="cat-tag">{clause.category}</span>
        )}
        <div className="clause-conf">
          <div className="conf-bar">
            <div className="conf-fill" style={{ width: `${confPct}%` }} />
          </div>
          <span className="conf-text">{confPct}%</span>
        </div>
      </div>
      <div className="clause-body">{clause.clause}</div>

      {hasRag && (
        <div className="clause-rag">
          <button
            className="rag-toggle"
            onClick={() => setExpanded(!expanded)}
          >
            <Building2 size={14} />
            Similar clauses from known companies ({clause.explanations.length})
            <ChevronDown
              size={16}
              className={`rag-chevron ${expanded ? "open" : ""}`}
            />
          </button>
          {expanded && (
            <div className="rag-list fade-in">
              {clause.explanations.map((exp, i) => {
                const simPct = (exp.similarity * 100).toFixed(0);
                return (
                  <div className="rag-item" key={i}>
                    <div className="rag-header">
                      <span className="rag-company">{exp.company}</span>
                      <span className="rag-cat">{exp.category}</span>
                      <span className="rag-match">
                        <ArrowUpRight size={12} />
                        {simPct}% match
                      </span>
                    </div>
                    <div className="rag-text">{exp.explanation}</div>
                    <div className="rag-sim">
                      <div className="rag-sim-bar">
                        <div className="rag-sim-fill" style={{ width: `${simPct}%` }} />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
