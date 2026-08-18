import { useEffect, useState } from "react";

const COLORS = ["#34D399", "#FBBF24", "#F87171"];
const LABELS = ["Fair", "Pot. Unfair", "Clearly Unfair"];

export default function DonutChart({ summary }) {
  const [animated, setAnimated] = useState(false);
  const bd = summary.breakdown || {};
  const values = [bd.fair || 0, bd.potentially_unfair || 0, bd.unfair || 0];
  const total = values.reduce((a, b) => a + b, 0);

  useEffect(() => {
    const t = setTimeout(() => setAnimated(true), 100);
    return () => clearTimeout(t);
  }, []);

  if (total === 0) return null;

  const radius = 52;
  const circumference = 2 * Math.PI * radius;
  let offset = 0;

  const segments = values.map((val, i) => {
    const pct = val / total;
    const dashLen = pct * circumference;
    const seg = { pct, dashLen, offset, color: COLORS[i], label: LABELS[i], count: val };
    offset += dashLen;
    return seg;
  });

  return (
    <div className="donut-chart fade-in">
      <svg viewBox="0 0 140 140" width="180" height="180">
        <circle cx="70" cy="70" r={radius} fill="none" stroke="rgba(148,163,184,0.08)" strokeWidth="14" />
        {segments.map((seg, i) =>
          seg.count > 0 ? (
            <circle
              key={i}
              cx="70" cy="70" r={radius}
              fill="none"
              stroke={seg.color}
              strokeWidth="14"
              strokeDasharray={`${animated ? seg.dashLen : 0} ${circumference}`}
              strokeDashoffset={-seg.offset}
              strokeLinecap="round"
              style={{
                transition: "stroke-dasharray 1s cubic-bezier(0.4,0,0.2,1)",
                transform: "rotate(-90deg)",
                transformOrigin: "70px 70px",
              }}
            />
          ) : null
        )}
        <text x="70" y="66" textAnchor="middle" className="donut-score">
          {summary.average_risk_score}/5
        </text>
        <text x="70" y="82" textAnchor="middle" className="donut-label">
          RISK SCORE
        </text>
      </svg>
      <div className="donut-legend">
        {segments.map((seg, i) =>
          seg.count > 0 ? (
            <div key={i} className="donut-legend-item">
              <span className="donut-dot" style={{ background: seg.color }} />
              {seg.label} ({seg.count})
            </div>
          ) : null
        )}
      </div>
    </div>
  );
}
