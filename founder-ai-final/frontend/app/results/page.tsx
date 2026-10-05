"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import ProtectedLayout from "@/components/ProtectedLayout";
import CandidateCard from "@/components/CandidateCard";
import type { AnalyzeResponse, Candidate } from "@/types";
import { Users, ArrowLeft, Trophy } from "lucide-react";

export default function ResultsPage() {
  const [data, setData] = useState<AnalyzeResponse | null>(null);

  useEffect(() => {
    const stored = sessionStorage.getItem("candidates");
    if (stored) setData(JSON.parse(stored));
  }, []);

  const topScore = data?.candidates[0]?.overall_score ?? 0;

  return (
    <ProtectedLayout>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Candidate Results</h1>
          {data && (
            <p className="text-gray-500 mt-1">
              {data.filtered_count} candidates ranked · {data.total} total analyzed
            </p>
          )}
        </div>
        <Link href="/upload" className="btn-secondary">
          <ArrowLeft className="w-4 h-4" />
          New Analysis
        </Link>
      </div>

      {!data ? (
        <div className="card text-center py-16">
          <Users className="w-16 h-16 text-gray-200 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-700 mb-2">No results yet</h2>
          <p className="text-gray-400 mb-6">Upload and analyze resumes to see ranked candidates here</p>
          <Link href="/upload" className="btn-primary">Start Analysis</Link>
        </div>
      ) : data.candidates.length === 0 ? (
        <div className="card text-center py-16">
          <h2 className="text-xl font-semibold text-gray-700 mb-2">No candidates passed filters</h2>
          <p className="text-gray-400 mb-6">Try loosening your filter criteria</p>
          <Link href="/upload" className="btn-primary">Try Again</Link>
        </div>
      ) : (
        <>
          {/* Summary bar */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="card flex items-center gap-3">
              <Trophy className="w-8 h-8 text-yellow-500" />
              <div>
                <p className="text-sm text-gray-500">Top Score</p>
                <p className="text-2xl font-bold text-gray-900">{Math.round(topScore)}</p>
              </div>
            </div>
            <div className="card text-center">
              <p className="text-2xl font-bold text-gray-900">{data.filtered_count}</p>
              <p className="text-sm text-gray-500">Qualified</p>
            </div>
            <div className="card text-center">
              <p className="text-2xl font-bold text-gray-900">{data.total}</p>
              <p className="text-sm text-gray-500">Total Analyzed</p>
            </div>
          </div>

          {/* Cards */}
          <div className="space-y-4">
            {data.candidates.map((c, i) => (
              <CandidateCard key={c.id} candidate={c} rank={i + 1} />
            ))}
          </div>
        </>
      )}
    </ProtectedLayout>
  );
}
