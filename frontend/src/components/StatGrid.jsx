import { useEffect, useRef } from "react";
import { Layers, CheckCircle, AlertTriangle, XCircle } from "lucide-react";

const STATS = [
  { key: "total", label: "Total", color: "#F1F5F9", Icon: Layers },
  { key: "fair", label: "Fair", color: "#34D399", Icon: CheckCircle },
  { key: "potentially_unfair", label: "Pot. Unfair", color: "#FBBF24", Icon: AlertTriangle },
  { key: "unfair", label: "Unfair", color: "#F87171", Icon: XCircle },
];

function AnimatedNumber({ value, color }) {
  const ref = useRef(null);

  useEffect(() => {
    const target = typeof value === "number" ? value : 0;
    const duration = 800;
    const startTime = performance.now();

    function tick(now) {
      const progress = Math.min((now - startTime) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      if (ref.current) ref.current.textContent = Math.round(eased * target);
      if (progress < 1) requestAnimationFrame(tick);
    }

    requestAnimationFrame(tick);
  }, [value]);

  return <span ref={ref} style={{ color }}>0</span>;
}

export default function StatGrid({ summary }) {
  const bd = summary.breakdown || {};
  const values = {
    total: summary.total_clauses || 0,
    fair: bd.fair || 0,
    potentially_unfair: bd.potentially_unfair || 0,
    unfair: bd.unfair || 0,
  };

  return (
    <div className="stat-grid">
      {STATS.map(({ key, label, color, Icon }, i) => (
        <div className="stat-card" key={key} style={{ animationDelay: `${i * 0.08}s` }}>
          <Icon size={18} color={color} className="stat-icon" />
          <div className="stat-num">
            <AnimatedNumber value={values[key]} color={color} />
          </div>
          <div className="stat-label">{label}</div>
        </div>
      ))}
    </div>
  );
}
