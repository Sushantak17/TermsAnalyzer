import { MessageSquareText } from "lucide-react";

export default function SummaryText({ text }) {
  return (
    <div className="summary-text slide-right">
      <div className="summary-label">
        <span className="summary-pulse" />
        <MessageSquareText size={14} />
        AI Summary
      </div>
      <p className="summary-body">{text}</p>
    </div>
  );
}
