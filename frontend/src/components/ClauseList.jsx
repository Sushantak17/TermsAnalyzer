import { useState } from "react";
import { List, AlertTriangle, CheckCircle } from "lucide-react";
import ClauseCard from "./ClauseCard";

export default function ClauseList({ clauses }) {
  const [activeTab, setActiveTab] = useState("all");

  const sorted = [...clauses].sort((a, b) => {
    const order = { unfair: 0, potentially_unfair: 1, fair: 2 };
    return (order[a.label] ?? 9) - (order[b.label] ?? 9) || b.confidence - a.confidence;
  });

  const flagged = sorted.filter((c) => c.label !== "fair");
  const fair = sorted.filter((c) => c.label === "fair");

  const tabs = [
    { id: "all", label: `All (${clauses.length})`, Icon: List },
    { id: "flagged", label: `Flagged (${flagged.length})`, Icon: AlertTriangle },
    { id: "fair", label: `Fair (${fair.length})`, Icon: CheckCircle },
  ];

  const visible = activeTab === "all" ? sorted : activeTab === "flagged" ? flagged : fair;

  return (
    <div className="clause-list">
      <div className="section-title">
        <span className="section-icon"><List size={16} /></span>
        All Clauses
      </div>
      <div className="clause-tabs">
        {tabs.map((tab) => {
          const Icon = tab.Icon;
          return (
            <button
              key={tab.id}
              className={`clause-tab ${activeTab === tab.id ? "active" : ""}`}
              onClick={() => setActiveTab(tab.id)}
            >
              <Icon size={14} />
              {tab.label}
            </button>
          );
        })}
      </div>
      <div className="clause-list-body">
        {visible.length === 0 ? (
          <div className="clause-empty">
            {activeTab === "flagged" ? "No flagged clauses found." : "No fair clauses identified."}
          </div>
        ) : (
          visible.map((c, i) => <ClauseCard key={i} clause={c} index={i + 1} />)
        )}
      </div>
    </div>
  );
}
