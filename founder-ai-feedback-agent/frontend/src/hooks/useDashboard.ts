import { useState, useEffect } from "react";
import { analyticsAPI } from "@/lib/api";
import type { DashboardAnalytics } from "@/types";

export function useDashboard() {
  const [data, setData] = useState<DashboardAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = async () => {
    setLoading(true);
    try {
      const res = await analyticsAPI.dashboard();
      setData(res.data);
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Failed to load dashboard");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { refresh(); }, []);
  return { data, loading, error, refresh };
}
