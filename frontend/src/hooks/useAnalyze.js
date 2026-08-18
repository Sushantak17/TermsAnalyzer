import { useState, useCallback } from "react";
import { analyzeText, analyzeUrl, analyzePdf } from "../api/analyze";

export function useAnalyze() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [step, setStep] = useState(0);

  const runAnalysis = useCallback(async (type, input) => {
    setLoading(true);
    setError(null);
    setData(null);
    setStep(0);

    const stepInterval = setInterval(() => {
      setStep((s) => Math.min(s + 1, 3));
    }, 800);

    try {
      let result;
      if (type === "text") result = await analyzeText(input);
      else if (type === "url") result = await analyzeUrl(input);
      else if (type === "pdf") result = await analyzePdf(input);
      setData(result);
    } catch (e) {
      setError(e.message);
    } finally {
      clearInterval(stepInterval);
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setLoading(false);
    setStep(0);
  }, []);

  return { data, loading, error, step, runAnalysis, reset };
}
