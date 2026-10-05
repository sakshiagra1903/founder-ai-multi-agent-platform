export interface User {
  id: string; email: string; full_name: string; role: string;
  company: { id: string; name: string; slug: string } | null;
}

export interface DashboardAnalytics {
  total_feedback: number;
  positive_pct: number; neutral_pct: number; negative_pct: number;
  total_complaints: number; total_feature_requests: number;
  top_complaints: Complaint[];
  top_feature_requests: FeatureRequest[];
  top_topics: Topic[];
  most_critical_issue: string | null;
  sentiment_trend: TrendPoint[];
  recent_insights: RecentInsight[];
}

export interface Complaint {
  category: string; count: number; severity: string;
}
export interface FeatureRequest {
  request: string; frequency: number; priority: string; category: string | null;
}
export interface Topic {
  label: string; keywords: string[]; frequency: number;
}
export interface TrendPoint {
  date: string; positive_pct: number; neutral_pct: number; negative_pct: number; total: number;
}
export interface RecentInsight {
  type: string; title: string; generated_at: string;
}
