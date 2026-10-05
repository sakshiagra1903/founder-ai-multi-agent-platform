export interface User {
  id: number;
  name: string;
  email: string;
  created_at: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Resume {
  id: number;
  filename: string;
  original_filename: string;
  file_size: number;
  uploaded_at: string;
}

export interface ResumeUploadResponse {
  resume_ids: number[];
  filenames: string[];
  message: string;
}

export interface FilterOptions {
  min_experience?: number;
  required_skills?: string[];
}

export interface AnalyzeRequest {
  resume_ids: number[];
  job_description: string;
  filters?: FilterOptions;
}

export interface ScoreBreakdown {
  skills_score: number;
  experience_score: number;
  education_score: number;
  projects_score: number;
  culture_fit_score: number;
  overall_score: number;
}

export interface Candidate {
  id: number;
  resume_id: number;
  rank: number;
  name: string | null;
  overall_score: number;
  score_breakdown: ScoreBreakdown | null;
  skills: string[];
  missing_skills: string[];
  summary: string | null;
  strengths: string[];
  weaknesses: string[];
  match_reason: string | null;
  experience_years: number;
  education: string[];
  hiring_recommendation: "Strong Hire" | "Hire" | "Consider" | "Reject";
  recommendation_reason: string | null;
  startup_fit_signals: string[];
  red_flags: string[];
  interview_questions: string[];
}

export interface FinalRankingRow {
  rank: number;
  name: string;
  overall_score: number;
  hiring_recommendation: string;
}

export interface AnalyzeResponse {
  candidates: Candidate[];
  total: number;
  filtered_count: number;
  message: string;
  final_ranking: FinalRankingRow[];
  best_candidate_name: string | null;
  best_candidate_reason: string | null;
}

export interface ApiError {
  detail: string;
}
