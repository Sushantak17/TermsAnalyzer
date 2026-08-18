import "./App.css";
import Hero from "./components/Hero";
import InputPanel from "./components/InputPanel";
import LoadingOverlay from "./components/LoadingOverlay";
import AnalysisResults from "./components/AnalysisResults";
import Footer from "./components/Footer";
import { useAnalyze } from "./hooks/useAnalyze";

export default function App() {
  const { data, loading, error, step, runAnalysis } = useAnalyze();

  return (
    <div className="app">
      <Hero />
      <main className="main">
        <InputPanel onAnalyze={runAnalysis} loading={loading} />
        {loading && <LoadingOverlay step={step} />}
        {error && (
          <div className="error-banner fade-in">
            <strong>Error:</strong> {error}
          </div>
        )}
        {data && !loading && <AnalysisResults data={data} />}
      </main>
      <Footer />
    </div>
  );
}
