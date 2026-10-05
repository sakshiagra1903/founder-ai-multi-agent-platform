"use client";
import { useState } from "react";
import type { Candidate } from "@/types";
import ScoreBadge from "./ScoreBadge";
import ScoreBar from "./ScoreBar";
import HiringBadge from "./HiringBadge";
import AlertBox from "./AlertBox";
import {
  CheckCircle2, XCircle, Star, GraduationCap, Briefcase,
  ChevronDown, ChevronUp, Zap, Brain, AlertTriangle,
} from "lucide-react";
import clsx from "clsx";

interface Props {
  candidate: Candidate;
  rank: number;
  requiredSkills?: string[];
}

export default function CandidateCard({ candidate, rank, requiredSkills = [] }: Props) {
  const [expanded, setExpanded] = useState(rank === 1);
  const isTop = rank === 1;
  const c = candidate;

  return (
    <div className={clsx(
      "bg-white rounded-2xl border overflow-hidden shadow-card animate-slide-up transition-all",
      isTop ? "border-brand-300 shadow-glow ring-2 ring-brand-100" : "border-gray-100 hover:shadow-card-hover"
    )}>
      {/* Top candidate ribbon */}
      {isTop && (
        <div className="bg-gradient-to-r from-brand-600 to-brand-500 px-4 py-2.5 flex items-center gap-2">
          <Star className="w-4 h-4 text-white fill-white" />
          <span className="text-white text-xs font-bold tracking-wide">TOP CANDIDATE — Best Match</span>
        </div>
      )}

      <div className="p-6">
        {/* ── Header ──────────────────────────────────────────── */}
        <div className="flex items-start gap-4 mb-4">
          {/* Avatar */}
          <div className={clsx(
            "w-12 h-12 rounded-xl flex items-center justify-center text-sm font-bold flex-shrink-0",
            isTop ? "bg-brand-100 text-brand-700" : "bg-gray-100 text-gray-600"
          )}>
            {(c.name || "?").split(" ").map(n => n[0]).slice(0, 2).join("").toUpperCase()}
          </div>

          {/* Name + meta */}
          <div className="flex-1 min-w-0">
            <div className="flex flex-wrap items-center gap-2 mb-1.5">
              <span className="text-xs font-bold bg-gray-100 text-gray-600 rounded px-2 py-0.5">#{rank}</span>
              <h3 className="text-lg font-bold text-gray-900">{c.name || "Unknown"}</h3>
              <HiringBadge recommendation={c.hiring_recommendation} />
            </div>
            <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-500">
              <span className="flex items-center gap-1">
                <Briefcase className="w-3.5 h-3.5 text-gray-400" />
                {c.experience_years > 0 ? `${c.experience_years}y exp` : "No exp listed"}
              </span>
              {c.education[0] && (
                <span className="flex items-center gap-1 truncate">
                  <GraduationCap className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
                  <span className="truncate max-w-[250px]">{c.education[0]}</span>
                </span>
              )}
            </div>
          </div>

          {/* Score badge */}
          <ScoreBadge score={c.overall_score} size={isTop ? "lg" : "sm"} />
        </div>

        {/* ── Summary ─────────────────────────────────────────── */}
        {c.summary && (
          <p className="text-sm text-gray-600 leading-relaxed mb-4">{c.summary}</p>
        )}

        {/* ── Skills tags ─────────────────────────────────────── */}
        {c.skills.length > 0 && (
          <div className="mb-4">
            <div className="flex flex-wrap gap-1.5">
              {c.skills.slice(0, 12).map(s => {
                const isReq = requiredSkills.map(r => r.toLowerCase()).includes(s.toLowerCase());
                return (
                  <span key={s} className={clsx(
                    "badge text-xs",
                    isReq ? "bg-brand-100 text-brand-700 border-brand-200" : "bg-gray-100 text-gray-700"
                  )}>
                    {isReq && <span className="w-1.5 h-1.5 rounded-full bg-brand-500 inline-block mr-1" />}
                    {s}
                  </span>
                );
              })}
              {c.skills.length > 12 && (
                <span className="badge bg-gray-100 text-gray-600 text-xs">+{c.skills.length - 12}</span>
              )}
            </div>
          </div>
        )}

        {/* ── Missing skills ───────────────────────────────────── */}
        {c.missing_skills.length > 0 && (
          <div className="mb-4">
            <div className="flex flex-wrap items-center gap-1.5 mb-2">
              <span className="flex items-center gap-1 text-xs font-semibold text-amber-600">
                <AlertTriangle className="w-3.5 h-3.5" /> Missing Skills:
              </span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {c.missing_skills.map(s => (
                <span key={s} className="badge bg-amber-50 text-amber-700 text-xs">{s}</span>
              ))}
            </div>
          </div>
        )}

        {/* ── Score breakdown bars ────────────────────────────── */}
        {c.score_breakdown && (
          <div className="mb-4 bg-gray-50 rounded-lg p-4 space-y-3">
            <p className="text-xs font-bold text-gray-700 uppercase tracking-wide">Score Breakdown</p>
            <ScoreBar label="Skills Match"   value={c.score_breakdown.skills_score} />
            <ScoreBar label="Experience"     value={c.score_breakdown.experience_score} />
            <ScoreBar label="Education"      value={c.score_breakdown.education_score} />
            <ScoreBar label="Projects"       value={c.score_breakdown.projects_score} />
            <ScoreBar label="Culture Fit"    value={c.score_breakdown.culture_fit_score} />
          </div>
        )}

        {/* ── Expand button ───────────────────────────────────── */}
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1.5 text-xs font-semibold text-brand-600 hover:text-brand-700 transition-colors">
          {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          {expanded ? "Hide details" : "Show full breakdown"}
        </button>

        {/* ── Expanded details ────────────────────────────────── */}
        {expanded && (
          <div className="mt-4 space-y-4 border-t border-gray-100 pt-4 animate-fade-in">
            {/* Strengths & Weaknesses */}
            <div className="grid sm:grid-cols-2 gap-4">
              {c.strengths.length > 0 && (
                <div>
                  <p className="label mb-2">✅ Strengths</p>
                  <ul className="space-y-1.5">
                    {c.strengths.map(s => (
                      <li key={s} className="flex items-start gap-2 text-sm text-gray-700">
                        <CheckCircle2 className="w-4 h-4 text-emerald-500 mt-0.5 flex-shrink-0" />
                        {s}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {c.weaknesses.length > 0 && (
                <div>
                  <p className="label mb-2">❌ Weaknesses</p>
                  <ul className="space-y-1.5">
                    {c.weaknesses.map(w => (
                      <li key={w} className="flex items-start gap-2 text-sm text-gray-700">
                        <XCircle className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
                        {w}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* Red flags */}
            {c.red_flags.length > 0 && (
              <AlertBox type="warning" title="Red Flags" items={c.red_flags} />
            )}

            {/* Startup signals */}
            {c.startup_fit_signals.length > 0 && (
              <AlertBox type="info" title="Startup Signals" items={c.startup_fit_signals} />
            )}

            {/* Interview questions */}
            {c.interview_questions.length > 0 && (
              <AlertBox type="question" title="Interview Questions" items={c.interview_questions} />
            )}

            {/* Match reason */}
            {c.match_reason && (
              <div className="bg-brand-50 border border-brand-100 rounded-lg px-4 py-3">
                <p className="text-sm text-brand-800">
                  <span className="font-semibold">Why: </span>
                  {c.match_reason}
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
