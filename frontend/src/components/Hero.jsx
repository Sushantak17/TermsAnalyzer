import { Sparkles, ScanSearch, BarChart3, FileDown } from "lucide-react";

export default function Hero() {
  return (
    <div className="hero">
      <div className="hero-glow" />
      <div className="hero-badge">
        <Sparkles size={14} />
        AI-Powered Legal Document Analysis
      </div>
      <h1 className="hero-title">
        Fine<span className="hero-grad">Print</span> AI
      </h1>
      <p className="hero-desc">
        Instantly analyze Terms of Service &amp; Privacy Policies.
        Our AI reads the fine print so you don't have to.
      </p>
      <div className="hero-chips">
        <span className="chip"><ScanSearch size={14} /> RAG Explanations</span>
        <span className="chip"><BarChart3 size={14} /> Readability Score</span>
        <span className="chip"><FileDown size={14} /> PDF Report</span>
      </div>
    </div>
  );
}
