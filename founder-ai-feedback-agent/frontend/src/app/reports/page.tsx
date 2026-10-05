"use client";
import { useState } from "react";
import { reportsAPI, insightsAPI } from "@/lib/api";
import toast from "react-hot-toast";
import { FileText, Download, Brain, Loader, Sparkles } from "lucide-react";

const REPORT_TYPES = [
  { value: "full", label: "Full Report", desc: "Complete analysis: sentiment, complaints, features, insights" },
  { value: "executive", label: "Executive Summary", desc: "High-level business overview for stakeholders" },
  { value: "complaint", label: "Complaint Report", desc: "Deep-dive into all detected complaints" },
  { value: "feature_request", label: "Feature Request Report", desc: "All feature requests ranked by priority" },
];

const INSIGHT_TYPES = [
  { value: "executive_summary", label: "Executive Summary" },
  { value: "root_cause", label: "Root Cause Analysis" },
  { value: "recommendation", label: "Product Recommendations" },
];

export default function ReportsPage() {
  const [reportType, setReportType] = useState("full");
  const [format, setFormat] = useState<"pdf" | "json">("pdf");
  const [generating, setGenerating] = useState(false);
  const [insightType, setInsightType] = useState("executive_summary");
  const [insightLoading, setInsightLoading] = useState(false);
  const [generatedInsight, setGeneratedInsight] = useState<string | null>(null);

  const handleReport = async () => {
    setGenerating(true);
    try {
      const res = await reportsAPI.generate({ report_type: reportType, format });
      if (format === "pdf" && res.data.id) {
        const blob = await reportsAPI.download(res.data.id);
        const url = URL.createObjectURL(new Blob([blob.data]));
        const a = document.createElement("a"); a.href = url;
        a.download = `feedback-report-${reportType}.pdf`; a.click();
        URL.revokeObjectURL(url);
        toast.success("PDF report downloaded!");
      } else {
        const blob = new Blob([JSON.stringify(res.data.payload, null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a"); a.href = url;
        a.download = `feedback-report-${reportType}.json`; a.click();
        URL.revokeObjectURL(url);
        toast.success("JSON report downloaded!");
      }
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Report generation failed");
    } finally { setGenerating(false); }
  };

  const handleInsight = async () => {
    setInsightLoading(true); setGeneratedInsight(null);
    try {
      const res = await insightsAPI.generate(insightType);
      setGeneratedInsight(res.data.content);
      toast.success("Insight generated!");
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Failed to generate insight");
    } finally { setInsightLoading(false); }
  };

  return (
    <div className="p-8 max-w-4xl space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Reports & Insights</h1>
        <p className="text-slate-500 mt-1">Generate AI-powered reports and business insights</p>
      </div>

      {/* Report Generator */}
      <div className="card">
        <div className="flex items-center gap-2 mb-6">
          <FileText className="w-5 h-5 text-blue-600" />
          <h2 className="font-semibold text-slate-800 text-lg">Generate Report</h2>
        </div>
        <div className="grid grid-cols-2 gap-3 mb-6">
          {REPORT_TYPES.map(rt => (
            <button key={rt.value} onClick={() => setReportType(rt.value)}
              className={`p-4 rounded-xl border-2 text-left transition-all ${reportType === rt.value ? "border-blue-500 bg-blue-50" : "border-slate-100 hover:border-slate-200"}`}>
              <p className="font-semibold text-slate-800 text-sm">{rt.label}</p>
              <p className="text-xs text-slate-500 mt-1">{rt.desc}</p>
            </button>
          ))}
        </div>
        <div className="flex items-center gap-4 mb-6">
          <span className="text-sm font-medium text-slate-700">Format:</span>
          {(["pdf", "json"] as const).map(f => (
            <label key={f} className="flex items-center gap-2 cursor-pointer">
              <input type="radio" name="format" value={f} checked={format === f}
                onChange={() => setFormat(f)} className="text-blue-600" />
              <span className="text-sm font-medium text-slate-700 uppercase">{f}</span>
            </label>
          ))}
        </div>
        <button onClick={handleReport} disabled={generating} className="btn-primary flex items-center gap-2">
          {generating ? <Loader className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
          {generating ? "Generating..." : `Download ${format.toUpperCase()} Report`}
        </button>
      </div>

      {/* AI Insight Generator */}
      <div className="card">
        <div className="flex items-center gap-2 mb-6">
          <Brain className="w-5 h-5 text-purple-600" />
          <h2 className="font-semibold text-slate-800 text-lg">AI Insight Generator</h2>
          <span className="badge badge-blue ml-2">Powered by {process.env.NEXT_PUBLIC_LLM_PROVIDER || "Groq Llama 3.3"}</span>
        </div>
        <div className="flex flex-wrap gap-3 mb-6">
          {INSIGHT_TYPES.map(it => (
            <button key={it.value} onClick={() => setInsightType(it.value)}
              className={`px-4 py-2 rounded-lg text-sm font-medium border-2 transition-all ${insightType === it.value ? "border-purple-500 bg-purple-50 text-purple-700" : "border-slate-100 text-slate-600 hover:border-slate-200"}`}>
              {it.label}
            </button>
          ))}
        </div>
        <button onClick={handleInsight} disabled={insightLoading} className="bg-purple-600 hover:bg-purple-700 text-white font-semibold px-4 py-2 rounded-lg transition-colors flex items-center gap-2 disabled:opacity-50">
          {insightLoading ? <Loader className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
          {insightLoading ? "Generating insight..." : "Generate Insight"}
        </button>

        {generatedInsight && (
          <div className="mt-6 bg-purple-50 border border-purple-100 rounded-xl p-5">
            <div className="flex items-center gap-2 mb-3">
              <Sparkles className="w-4 h-4 text-purple-600" />
              <span className="text-sm font-semibold text-purple-700">AI Generated Insight</span>
            </div>
            <p className="text-sm text-slate-700 whitespace-pre-wrap leading-relaxed">{generatedInsight}</p>
          </div>
        )}
      </div>
    </div>
  );
}
