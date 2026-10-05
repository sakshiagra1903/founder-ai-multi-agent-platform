import axios from "axios";
import type {
  AuthToken,
  User,
  ResumeUploadResponse,
  AnalyzeRequest,
  AnalyzeResponse,
  Resume,
} from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
});

// Attach JWT from localStorage on every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Auth
export const authApi = {
  signup: (name: string, email: string, password: string) =>
    api.post<User>("/auth/signup", { name, email, password }),

  login: (email: string, password: string) =>
    api.post<AuthToken>("/auth/login", { email, password }),

  me: () => api.get<User>("/auth/me"),
};

// Hiring
export const hiringApi = {
  uploadResumes: (files: File[]) => {
    const form = new FormData();
    files.forEach((f) => form.append("files", f));
    return api.post<ResumeUploadResponse>("/hiring/upload-resumes", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  analyze: (payload: AnalyzeRequest) =>
    api.post<AnalyzeResponse>("/hiring/analyze", payload),

  listResumes: () => api.get<Resume[]>("/hiring/resumes"),

  deleteResume: (id: number) => api.delete(`/hiring/resumes/${id}`),
};
