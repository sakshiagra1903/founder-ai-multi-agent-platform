"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import ProtectedLayout from "@/components/ProtectedLayout";
import { useAuth } from "@/hooks/useAuth";
import { hiringApi } from "@/services/api";
import type { Resume } from "@/types";
import { Upload, Users, FileText, ArrowRight, TrendingUp } from "lucide-react";

export default function DashboardPage() {
  const { user } = useAuth();
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    hiringApi.listResumes()
      .then((r) => setResumes(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const stats = [
    { label: "Resumes Uploaded", value: resumes.length, icon: FileText, color: "bg-blue-50 text-blue-600" },
    { label: "Analyses Run", value: "—", icon: TrendingUp, color: "bg-green-50 text-green-600" },
    { label: "Top Candidates", value: "—", icon: Users, color: "bg-purple-50 text-purple-600" },
  ];

  return (
    <ProtectedLayout>
      {/* Welcome */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          Welcome back, {user?.name?.split(" ")[0]} 👋
        </h1>
        <p className="text-gray-500 mt-1">Here's your hiring overview</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        {stats.map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="card flex items-center gap-4">
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${color}`}>
              <Icon className="w-6 h-6" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{loading ? "…" : value}</p>
              <p className="text-sm text-gray-500">{label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Quick actions */}
      <div className="grid sm:grid-cols-2 gap-4 mb-8">
        <Link href="/upload" className="card group hover:border-indigo-200 hover:shadow-md transition cursor-pointer border border-transparent">
          <div className="flex items-center justify-between">
            <div>
              <div className="w-10 h-10 bg-indigo-100 rounded-xl flex items-center justify-center mb-3">
                <Upload className="w-5 h-5 text-indigo-600" />
              </div>
              <h3 className="font-semibold text-gray-900">Upload & Analyze</h3>
              <p className="text-sm text-gray-500 mt-1">Upload resumes and run AI evaluation</p>
            </div>
            <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-indigo-500 transition" />
          </div>
        </Link>

        <Link href="/results" className="card group hover:border-indigo-200 hover:shadow-md transition cursor-pointer border border-transparent">
          <div className="flex items-center justify-between">
            <div>
              <div className="w-10 h-10 bg-purple-100 rounded-xl flex items-center justify-center mb-3">
                <Users className="w-5 h-5 text-purple-600" />
              </div>
              <h3 className="font-semibold text-gray-900">View Candidates</h3>
              <p className="text-sm text-gray-500 mt-1">Review scored and ranked candidates</p>
            </div>
            <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-indigo-500 transition" />
          </div>
        </Link>
      </div>

      {/* Recent resumes */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-gray-900">Recent Resumes</h2>
          <Link href="/upload" className="text-sm text-indigo-600 hover:underline">View all</Link>
        </div>
        {loading ? (
          <p className="text-sm text-gray-400">Loading…</p>
        ) : resumes.length === 0 ? (
          <div className="text-center py-8">
            <FileText className="w-10 h-10 text-gray-300 mx-auto mb-2" />
            <p className="text-gray-500 text-sm">No resumes uploaded yet</p>
            <Link href="/upload" className="btn-primary mt-4 inline-flex">Upload resumes</Link>
          </div>
        ) : (
          <ul className="divide-y divide-gray-100">
            {resumes.slice(0, 5).map((r) => (
              <li key={r.id} className="flex items-center justify-between py-3">
                <div className="flex items-center gap-2">
                  <FileText className="w-4 h-4 text-indigo-400" />
                  <span className="text-sm font-medium text-gray-700">{r.original_filename}</span>
                </div>
                <span className="text-xs text-gray-400">{new Date(r.uploaded_at).toLocaleDateString()}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </ProtectedLayout>
  );
}
