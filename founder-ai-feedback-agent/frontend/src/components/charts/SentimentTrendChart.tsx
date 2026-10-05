"use client";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import type { TrendPoint } from "@/types";

interface Props { data: TrendPoint[]; }

export default function SentimentTrendChart({ data }: Props) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
        <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#94a3b8" }} tickLine={false} />
        <YAxis tick={{ fontSize: 11, fill: "#94a3b8" }} tickLine={false} unit="%" />
        <Tooltip formatter={(v: any) => `${Number(v).toFixed(1)}%`} />
        <Legend />
        <Line type="monotone" dataKey="positive_pct" stroke="#22c55e" strokeWidth={2} dot={false} name="Positive %" />
        <Line type="monotone" dataKey="neutral_pct" stroke="#f59e0b" strokeWidth={2} dot={false} name="Neutral %" />
        <Line type="monotone" dataKey="negative_pct" stroke="#ef4444" strokeWidth={2} dot={false} name="Negative %" />
      </LineChart>
    </ResponsiveContainer>
  );
}
