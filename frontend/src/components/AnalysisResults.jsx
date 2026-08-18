import { useState, useRef, useEffect } from "react";
import { BarChart3, FileText, List, Download, Eye } from "lucide-react";
import RiskBanner from "./RiskBanner";
import StatGrid from "./StatGrid";
import DonutChart from "./DonutChart";
import DistributionBars from "./DistributionBars";
import ReadabilityGauge from "./ReadabilityGauge";
import SummaryText from "./SummaryText";
import HighlightedDoc from "./HighlightedDoc";
import KeyFindings from "./KeyFindings";
import ClauseList from "./ClauseList";
import ExportButtons from "./ExportButtons";

const TABS = [
  { id: "overview", label: "Overview", Icon: BarChart3 },
  { id: "document", label: "Document", Icon: Eye },
  { id: "clauses", label: "Clauses", Icon: List },
  { id: "export", label: "Export", Icon: Download },
];

export default function AnalysisResults({ data }) {
  const [activeTab, setActiveTab] = useState("overview");
  const ref = useRef(null);

  useEffect(() => {
    if (ref.current) {
      ref.current.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [data]);

  return (
    <div ref={ref} className="results fade-up">
      <div className="results-tabs">
        {TABS.map((tab) => {
          const Icon = tab.Icon;
          if (tab.id === "document" && !data.raw_text) return null;
          return (
            <button
              key={tab.id}
              className={`results-tab ${activeTab === tab.id ? "active" : ""}`}
              onClick={() => setActiveTab(tab.id)}
            >
              <Icon size={15} />
              {tab.label}
            </button>
          );
        })}
      </div>

      <div className="results-panel">
        {activeTab === "overview" && (
          <>
            <div className="card fade-in">
              <div className="section-title">
                <span className="section-icon"><BarChart3 size={16} /></span>
                Analysis Results
              </div>
              <RiskBanner risk={data.summary.overall_risk} />
              <StatGrid summary={data.summary} />
              <div className="chart-row">
                <DonutChart summary={data.summary} />
                <DistributionBars summary={data.summary} />
              </div>
              <ReadabilityGauge readability={data.readability} />
              <SummaryText text={data.summary_text} />
            </div>
            <KeyFindings clauses={data.clauses} />
          </>
        )}

        {activeTab === "document" && data.raw_text && (
          <HighlightedDoc rawText={data.raw_text} clauses={data.clauses} />
        )}

        {activeTab === "clauses" && (
          <ClauseList clauses={data.clauses} />
        )}

        {activeTab === "export" && (
          <div className="card fade-in">
            <div className="section-title">
              <span className="section-icon"><Download size={16} /></span>
              Export Report
            </div>
            <p style={{ color: "var(--text-secondary)", marginBottom: "1.2rem", fontSize: "0.9rem" }}>
              Download a professionally formatted PDF report of the complete analysis.
            </p>
            <ExportButtons data={data} />
          </div>
        )}
      </div>
    </div>
  );
}
