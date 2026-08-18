import { useEffect, useState } from "react";
import { BookOpen } from "lucide-react";

export default function ReadabilityGauge({ readability }) {
  const [animated, setAnimated] = useState(false);
  const grade = readability.grade_level || 0;
  const maxGrade = 20;
  const pct = Math.min(grade / maxGrade, 1.0);
  const circumference = 2 * Math.PI * 28;
  const dashLen = pct * circumference;
  const barPct = Math.min(readability.reading_ease || 0, 100);

  useEffect(() => {
    const t = setTimeout(() => setAnimated(true), 300);
    return () => clearTimeout(t);
  }, []);

  return (
    <div className="readability slide-right">
      <div className="read-gauge">
        <svg width="72" height="72" viewBox="0 0 72 72">
          <defs>
            <linearGradient id="gaugeGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#06B6D4" />
              <stop offset="100%" stopColor="#14B8A6" />
            </linearGradient>
          </defs>
          <circle cx="36" cy="36" r="28" fill="none" stroke="rgba(148,163,184,0.1)" strokeWidth="5" />
          <circle
            cx="36" cy="36" r="28" fill="none"
            stroke="url(#gaugeGrad)" strokeWidth="5" strokeLinecap="round"
            strokeDasharray={`${animated ? dashLen : 0} ${circumference}`}
            style={{
              transform: "rotate(-90deg)",
              transformOrigin: "36px 36px",
              transition: "stroke-dasharray 1.2s cubic-bezier(0.4,0,0.2,1)",
            }}
          />
        </svg>
        <div className="read-gauge-text">{grade}</div>
      </div>
      <div className="read-info">
        <div className="read-level">
          <BookOpen size={16} />
          {readability.level} Reading Level
        </div>
        <div className="read-desc">{readability.description}</div>
        <div className="read-bar-wrap">
          <div
            className="read-bar"
            style={{
              width: animated ? `${barPct}%` : "0%",
              transition: "width 1s cubic-bezier(0.4,0,0.2,1)",
            }}
          />
        </div>
        <div className="read-meta">
          <span>{readability.word_count} words</span>
          <span>{readability.sentence_count} sentences</span>
          <span>Flesch ease: {readability.reading_ease}/100</span>
        </div>
      </div>
    </div>
  );
}
