"use client";
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from "recharts";

interface Props { positive: number; neutral: number; negative: number; }

export default function SentimentPieChart({ positive, neutral, negative }: Props) {
  const data = [
    { name: "Positive", value: positive, color: "#22c55e" },
    { name: "Neutral", value: neutral, color: "#f59e0b" },
    { name: "Negative", value: negative, color: "#ef4444" },
  ];
  return (
    <ResponsiveContainer width="100%" height={260}>
      <PieChart>
        <Pie data={data} cx="50%" cy="50%" outerRadius={90} dataKey="value" label={({ name, value }) => `${name}: ${value.toFixed(1)}%`} labelLine={false}>
          {data.map((d, i) => <Cell key={i} fill={d.color} />)}
        </Pie>
        <Tooltip formatter={(v: any) => `${Number(v).toFixed(1)}%`} />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}
