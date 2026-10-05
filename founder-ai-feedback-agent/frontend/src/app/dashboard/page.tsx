"use client";
import { useDashboard } from "@/hooks/useDashboard";
import StatCard from "@/components/dashboard/StatCard";
import SentimentPieChart from "@/components/charts/SentimentPieChart";
import SentimentTrendChart from "@/components/charts/SentimentTrendChart";
import ComplaintsBarChart from "@/components/charts/ComplaintsBarChart";
import { BarChart3, MessageSquare, AlertTriangle, Lightbulb, RefreshCw, TrendingUp } from "lucide-react";
import { severityColor } from "@/lib/utils";

export default function DashboardPage() {
  const { data, loading, error, refresh } = useDashboard();

  if (loading) return (
    <div className="flex items-center justify-center h-96">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto" />
        <p className="mt-3 text-slate-500">Loading analytics...</p>
      </div>
    </div>
  );

  if (error) return (
    <div className="p-8">
      <div className="card border-red-100 bg-red-50">
        <p className="text-red-600 font-medium">Error: {error}</p>
        <button onClick={refresh} className="btn-primary mt-3 text-sm">Retry</button>
      </div>
    </div>
  );

  if (!data) return null;

  return (
    <div className="p-8 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Feedback Dashboard</h1>
          <p className="text-slate-500 text-sm mt-1">Real-time customer intelligence for your startup</p>
        </div>
        <button onClick={refresh} className="btn-secondary flex items-center gap-2 text-sm">
          <RefreshCw className="w-4 h-4" /> Refresh
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard title="Total Feedback" value={data.total_feedback.toLocaleString()} icon={MessageSquare} color="bg-blue-500" />
        <StatCard title="Positive Sentiment" value={`${data.positive_pct.toFixed(1)}%`} icon={TrendingUp} color="bg-green-500" />
        <StatCard title="Total Complaints" value={data.total_complaints} icon={AlertTriangle} color="bg-red-500"
          subtitle={data.most_critical_issue ? `Top: ${data.most_critical_issue}` : undefined} />
        <StatCard title="Feature Requests" value={data.total_feature_requests} icon={Lightbulb} color="bg-purple-500" />
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="font-semibold text-slate-800 mb-4">Sentiment Distribution</h2>
          <SentimentPieChart positive={data.positive_pct} neutral={data.neutral_pct} negative={data.negative_pct} />
        </div>
        <div className="card">
          <h2 className="font-semibold text-slate-800 mb-4">Sentiment Trend (30 days)</h2>
          {data.sentiment_trend.length > 0
            ? <SentimentTrendChart data={data.sentiment_trend} />
            : <p className="text-slate-400 text-sm text-center py-12">Not enough data yet. Upload more feedback.</p>}
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="font-semibold text-slate-800 mb-4">🚨 Top Complaints</h2>
          {data.top_complaints.length > 0 ? (
            <div className="space-y-2">
              {data.top_complaints.map((c, i) => (
                <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-slate-50">
                  <div>
                    <p className="text-sm font-medium text-slate-800">{c.category}</p>
                    <span className="text-xs font-medium" style={{ color: severityColor(c.severity) }}>
                      {c.severity.toUpperCase()}
                    </span>
                  </div>
                  <span className="font-bold text-slate-900">{c.count}</span>
                </div>
              ))}
            </div>
          ) : <p className="text-slate-400 text-sm text-center py-8">No complaints detected yet.</p>}
        </div>

        <div className="card">
          <h2 className="font-semibold text-slate-800 mb-4">💡 Top Feature Requests</h2>
          {data.top_feature_requests.length > 0 ? (
            <div className="space-y-2">
              {data.top_feature_requests.map((f, i) => (
                <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-slate-50">
                  <div>
                    <p className="text-sm font-medium text-slate-800">{f.request || "Feature Request"}</p>
                    {f.category && <span className="text-xs text-slate-400">{f.category}</span>}
                  </div>
                  <div className="text-right">
                    <span className="badge badge-blue text-xs">{f.priority}</span>
                    <p className="text-xs text-slate-400 mt-1">{f.frequency}x</p>
                  </div>
                </div>
              ))}
            </div>
          ) : <p className="text-slate-400 text-sm text-center py-8">No feature requests detected yet.</p>}
        </div>
      </div>

      {/* Topics */}
      {data.top_topics.length > 0 && (
        <div className="card">
          <h2 className="font-semibold text-slate-800 mb-4">🔍 Top Discussion Topics</h2>
          <div className="flex flex-wrap gap-3">
            {data.top_topics.map((t, i) => (
              <div key={i} className="bg-slate-50 border border-slate-200 rounded-xl px-4 py-3">
                <p className="font-semibold text-slate-800 text-sm">{t.label}</p>
                <p className="text-xs text-slate-400 mt-1">{t.keywords.join(", ")}</p>
                <p className="text-xs text-blue-600 font-medium mt-1">{t.frequency} mentions</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Insights */}
      {data.recent_insights.length > 0 && (
        <div className="card">
          <h2 className="font-semibold text-slate-800 mb-4">🧠 Recent AI Insights</h2>
          <div className="space-y-2">
            {data.recent_insights.map((ins, i) => (
              <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-blue-50">
                <div>
                  <span className="badge badge-blue mr-2">{ins.type.replace("_", " ")}</span>
                  <span className="text-sm text-slate-700">{ins.title}</span>
                </div>
                <span className="text-xs text-slate-400">{new Date(ins.generated_at).toLocaleDateString()}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
