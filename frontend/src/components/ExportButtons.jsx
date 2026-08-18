import { FileDown } from "lucide-react";

const API = "http://localhost:8000/api";

export default function ExportButtons({ data }) {
  async function downloadPdf() {
    const resp = await fetch(`${API}/report/pdf`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!resp.ok) return;
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "fineprint_report.pdf";
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="export-buttons">
      <button className="btn-primary" onClick={downloadPdf} style={{ flex: 1 }}>
        <FileDown size={18} />
        Download PDF Report
      </button>
    </div>
  );
}
