import { useEffect, useState } from "react";

const BARS = [
  { key: "fair", label: "Fair", color: "#34D399", gradient: "linear-gradient(90deg, #34D399, #6EE7B7)" },
  { key: "potentially_unfair", label: "Pot. Unfair", color: "#FBBF24", gradient: "linear-gradient(90deg, #FBBF24, #FDE68A)" },
  { key: "unfair", label: "Unfair", color: "#F87171", gradient: "linear-gradient(90deg, #F87171, #FCA5A5)" },
];

export default function DistributionBars({ summary }) {
  const [animated, setAnimated] = useState(false);
  const bd = summary.breakdown || {};
  const total = Math.max(summary.total_clauses, 1);

  useEffect(() => {
    const t = setTimeout(() => setAnimated(true), 200);
    return () => clearTimeout(t);
  }, []);

  return (
    <div className="dist-bars">
      {BARS.map(({ key, label, color, gradient }, i) => {
        const count = bd[key] || 0;
        const pct = (count / total) * 100;
        return (
          <div className="dist-row slide-right" key={key} style={{ animationDelay: `${i * 0.1}s` }}>
            <span className="dist-label" style={{ color }}>{label}</span>
            <div className="dist-track">
              <div
                className="dist-fill"
                style={{
                  width: animated ? `${pct}%` : "0%",
                  background: gradient,
                  transition: "width 1s cubic-bezier(0.4,0,0.2,1)",
                }}
              />
            </div>
            <span className="dist-count" style={{ color }}>{count}</span>
          </div>
        );
      })}
    </div>
  );
}
