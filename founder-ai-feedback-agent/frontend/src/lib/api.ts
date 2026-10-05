import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export const api = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  async (err) => {
    if (err.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("access_token");
      localStorage.removeItem("user");
      window.location.href = "/auth/login";
    }
    return Promise.reject(err);
  }
);

// Auth
export const authAPI = {
  register: (data: any) => api.post("/auth/register", data),
  login: (data: any) => api.post("/auth/login", data),
  me: () => api.get("/auth/me"),
};

// Feedback
export const feedbackAPI = {
  upload: (file: File, autoAnalyze = true) => {
    const form = new FormData();
    form.append("file", file);
    return api.post(`/feedback/upload?auto_analyze=${autoAnalyze}`, form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  list: (page = 1, pageSize = 20) => api.get(`/feedback?page=${page}&page_size=${pageSize}`),
};

// Analytics
export const analyticsAPI = {
  dashboard: () => api.get("/analytics/dashboard"),
  sentiment: () => api.get("/analytics/sentiment"),
  complaints: (limit = 10) => api.get(`/analytics/complaints?limit=${limit}`),
  features: (limit = 10) => api.get(`/analytics/features?limit=${limit}`),
  topics: () => api.get("/analytics/topics"),
  trend: (days = 30) => api.get(`/analytics/trend?days=${days}`),
};

// Insights
export const insightsAPI = {
  generate: (type: string) => api.post("/insights/generate", { insight_type: type }),
  list: () => api.get("/insights"),
};

// Chat
export const chatAPI = {
  send: (message: string) => api.post("/chat", { message }),
};

// Reports
export const reportsAPI = {
  generate: (data: any) => api.post("/reports", data),
  download: (id: string) => api.get(`/reports/${id}/download`, { responseType: "blob" }),
};
