"use client";
import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { feedbackAPI } from "@/lib/api";
import toast from "react-hot-toast";
import { Upload, FileText, CheckCircle, AlertCircle, Loader } from "lucide-react";
import { cn } from "@/lib/utils";

interface UploadResult {
  total_rows: number; imported: number;
  duplicates_skipped: number; errors: number; message: string;
}

export default function UploadPage() {
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<UploadResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback(async (files: File[]) => {
    const file = files[0];
    if (!file) return;
    setUploading(true); setResult(null); setError(null);
    try {
      const res = await feedbackAPI.upload(file, true);
      setResult(res.data);
      toast.success(`Imported ${res.data.imported} feedback records!`);
    } catch (e: any) {
      const msg = e?.response?.data?.detail || "Upload failed";
      setError(msg); toast.error(msg);
    } finally { setUploading(false); }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop, accept: { "text/csv": [".csv"], "application/json": [".json"],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"] },
    maxFiles: 1, disabled: uploading,
  });

  return (
    <div className="p-8 max-w-3xl">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Upload Feedback</h1>
        <p className="text-slate-500 mt-1">Upload CSV, XLSX, or JSON files. AI analysis runs automatically.</p>
      </div>

      <div className="card mb-6">
        <h2 className="font-semibold text-slate-800 mb-2">Expected Columns</h2>
        <div className="grid grid-cols-2 gap-2">
          {[["feedback_id","Optional unique ID"],["customer_id","Optional customer ID"],
            ["feedback_text","Required — the review text"],["rating","Optional 1-5 score"],
            ["date","Optional feedback date"]].map(([col, desc]) => (
            <div key={col} className="bg-slate-50 rounded-lg p-3">
              <code className="text-xs font-mono text-blue-700 font-bold">{col}</code>
              <p className="text-xs text-slate-500 mt-0.5">{desc}</p>
            </div>
          ))}
        </div>
        <p className="text-xs text-slate-400 mt-3">Also accepts: <code>text</code>, <code>comment</code>, <code>review</code>, <code>score</code>, <code>stars</code></p>
      </div>

      <div {...getRootProps()} className={cn(
        "border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all",
        isDragActive ? "border-blue-500 bg-blue-50" : "border-slate-200 hover:border-blue-400 hover:bg-slate-50",
        uploading && "opacity-50 cursor-not-allowed"
      )}>
        <input {...getInputProps()} />
        {uploading ? (
          <div className="flex flex-col items-center gap-3">
            <Loader className="w-12 h-12 text-blue-500 animate-spin" />
            <p className="font-semibold text-slate-700">Uploading & analyzing...</p>
            <p className="text-sm text-slate-400">AI is running sentiment, complaint, and feature analysis</p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            <Upload className={cn("w-12 h-12", isDragActive ? "text-blue-500" : "text-slate-300")} />
            <p className="font-semibold text-slate-700">
              {isDragActive ? "Drop your file here" : "Drag & drop or click to upload"}
            </p>
            <p className="text-sm text-slate-400">CSV, XLSX, or JSON — max 50MB</p>
          </div>
        )}
      </div>

      {result && (
        <div className="mt-6 card border-green-100 bg-green-50">
          <div className="flex items-center gap-2 mb-4">
            <CheckCircle className="w-5 h-5 text-green-600" />
            <h3 className="font-semibold text-green-800">Upload Successful</h3>
          </div>
          <div className="grid grid-cols-2 gap-3">
            {[["Total Rows", result.total_rows], ["Imported", result.imported],
              ["Duplicates Skipped", result.duplicates_skipped], ["Errors", result.errors]].map(([label, val]) => (
              <div key={label} className="bg-white rounded-lg p-3">
                <p className="text-xs text-slate-500">{label}</p>
                <p className="text-xl font-bold text-slate-900">{val}</p>
              </div>
            ))}
          </div>
          <p className="text-sm text-green-700 mt-3">{result.message}</p>
          <p className="text-xs text-green-600 mt-1">🤖 NLP analysis is running in the background. Check the dashboard in a moment.</p>
        </div>
      )}

      {error && (
        <div className="mt-6 card border-red-100 bg-red-50">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-red-500" />
            <p className="text-red-700 font-medium">{error}</p>
          </div>
        </div>
      )}
    </div>
  );
}
