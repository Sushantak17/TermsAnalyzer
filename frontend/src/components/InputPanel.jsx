import { useState, useRef } from "react";
import { Type, Globe, FileUp, ArrowRight } from "lucide-react";

const TABS = [
  { id: "text", label: "Paste Text", icon: Type },
  { id: "url", label: "Enter URL", icon: Globe },
  { id: "pdf", label: "Upload PDF", icon: FileUp },
];

export default function InputPanel({ onAnalyze, loading }) {
  const [activeTab, setActiveTab] = useState("text");
  const [text, setText] = useState("");
  const [url, setUrl] = useState("");
  const [pdfFile, setPdfFile] = useState(null);
  const fileRef = useRef(null);

  const handleSubmit = () => {
    if (loading) return;
    if (activeTab === "text" && text.trim()) onAnalyze("text", text);
    else if (activeTab === "url" && url.trim()) onAnalyze("url", url);
    else if (activeTab === "pdf" && pdfFile) onAnalyze("pdf", pdfFile);
  };

  const canSubmit =
    (activeTab === "text" && text.trim()) ||
    (activeTab === "url" && url.trim()) ||
    (activeTab === "pdf" && pdfFile);

  return (
    <div className="card fade-up">
      <div className="section-title">
        <span className="section-icon"><ScanIcon /></span>
        Analyze a Document
      </div>

      <div className="input-tabs">
        {TABS.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              className={`input-tab ${activeTab === tab.id ? "active" : ""}`}
              onClick={() => setActiveTab(tab.id)}
            >
              <Icon size={15} />
              {tab.label}
            </button>
          );
        })}
      </div>

      <div className="input-body">
        {activeTab === "text" && (
          <textarea
            className="input-textarea"
            rows={8}
            placeholder="Paste Terms of Service or Privacy Policy text here..."
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
        )}
        {activeTab === "url" && (
          <input
            className="input-field"
            type="url"
            placeholder="https://example.com/terms-of-service"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
          />
        )}
        {activeTab === "pdf" && (
          <div
            className={`input-dropzone ${pdfFile ? "has-file" : ""}`}
            onClick={() => fileRef.current?.click()}
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              const f = e.dataTransfer.files[0];
              if (f?.type === "application/pdf") setPdfFile(f);
            }}
          >
            <FileUp size={32} className="dropzone-icon" />
            {pdfFile ? (
              <span className="dropzone-filename">{pdfFile.name}</span>
            ) : (
              <span className="dropzone-text">
                Drop a PDF here or click to browse
              </span>
            )}
            <input
              ref={fileRef}
              type="file"
              accept=".pdf"
              hidden
              onChange={(e) => setPdfFile(e.target.files[0] || null)}
            />
          </div>
        )}

        <button
          className={`btn-primary ${!canSubmit || loading ? "disabled" : ""}`}
          onClick={handleSubmit}
          disabled={!canSubmit || loading}
        >
          {loading ? "Analyzing..." : "Analyze Document"}
          {!loading && <ArrowRight size={18} />}
        </button>
      </div>
    </div>
  );
}

function ScanIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 7V5a2 2 0 0 1 2-2h2" /><path d="M17 3h2a2 2 0 0 1 2 2v2" />
      <path d="M21 17v2a2 2 0 0 1-2 2h-2" /><path d="M7 21H5a2 2 0 0 1-2-2v-2" />
      <line x1="7" x2="17" y1="12" y2="12" />
    </svg>
  );
}
