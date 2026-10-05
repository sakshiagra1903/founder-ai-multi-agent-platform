"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";
import ProtectedLayout from "@/components/ProtectedLayout";
import ResumeDropzone from "@/components/ResumeDropzone";
import SkillsInput from "@/components/SkillsInput";
import { hiringApi } from "@/services/api";
import { Loader2, Sparkles } from "lucide-react";

export default function UploadPage() {
  const router = useRouter();
  const [files, setFiles] = useState<File[]>([]);
  const [jobDescription, setJobDescription] = useState("");
  const [minExperience, setMinExperience] = useState<string>("");
  const [requiredSkills, setRequiredSkills] = useState<string[]>([]);
  const [uploading, setUploading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);

  const handleAnalyze = async () => {
    if (files.length === 0) return toast.error("Please upload at least one resume");
    if (!jobDescription.trim()) return toast.error("Please provide a job description");

    try {
      // Step 1: Upload
      setUploading(true);
      const uploadRes = await hiringApi.uploadResumes(files);
      const { resume_ids } = uploadRes.data;
      toast.success(`${resume_ids.length} resume(s) uploaded!`);
      setUploading(false);

      // Step 2: Analyze
      setAnalyzing(true);
      const analyzeRes = await hiringApi.analyze({
        resume_ids,
        job_description: jobDescription,
        filters: {
          min_experience: minExperience ? parseFloat(minExperience) : undefined,
          required_skills: requiredSkills.length > 0 ? requiredSkills : undefined,
        },
      });

      // Store results in sessionStorage and redirect
      sessionStorage.setItem("candidates", JSON.stringify(analyzeRes.data));
      toast.success(`Analysis complete! ${analyzeRes.data.filtered_count} candidates ranked.`);
      router.push("/results");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Something went wrong");
    } finally {
      setUploading(false);
      setAnalyzing(false);
    }
  };

  const busy = uploading || analyzing;

  return (
    <ProtectedLayout>
      <div className="max-w-3xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Upload & Analyze</h1>
          <p className="text-gray-500 mt-1">Upload resumes and let AI rank your candidates</p>
        </div>

        <div className="space-y-6">
          {/* Step 1 */}
          <div className="card">
            <h2 className="font-semibold text-gray-900 mb-1">Step 1 — Upload Resumes</h2>
            <p className="text-sm text-gray-500 mb-4">PDF files only, up to 10 MB each</p>
            <ResumeDropzone files={files} onChange={setFiles} />
          </div>

          {/* Step 2 */}
          <div className="card">
            <h2 className="font-semibold text-gray-900 mb-1">Step 2 — Job Description</h2>
            <p className="text-sm text-gray-500 mb-4">The AI will evaluate candidates against this description</p>
            <textarea
              className="input resize-none h-36"
              placeholder="e.g. We're looking for a Senior ML Engineer with 3+ years of experience in Python, PyTorch, and deploying models to production…"
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
            />
          </div>

          {/* Step 3 */}
          <div className="card">
            <h2 className="font-semibold text-gray-900 mb-1">Step 3 — Filters (Optional)</h2>
            <p className="text-sm text-gray-500 mb-4">Narrow down candidates before ranking</p>
            <div className="grid sm:grid-cols-2 gap-4">
              <div>
                <label className="label">Minimum Experience (years)</label>
                <input
                  type="number"
                  min="0"
                  step="0.5"
                  className="input"
                  placeholder="e.g. 2"
                  value={minExperience}
                  onChange={(e) => setMinExperience(e.target.value)}
                />
              </div>
              <div>
                <label className="label">Required Skills</label>
                <SkillsInput value={requiredSkills} onChange={setRequiredSkills} />
              </div>
            </div>
          </div>

          {/* CTA */}
          <button
            className="btn-primary w-full py-3 text-base"
            onClick={handleAnalyze}
            disabled={busy}
          >
            {busy ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                {uploading ? "Uploading resumes…" : "AI is evaluating candidates…"}
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5" />
                Analyze Candidates with AI
              </>
            )}
          </button>
        </div>
      </div>
    </ProtectedLayout>
  );
}
