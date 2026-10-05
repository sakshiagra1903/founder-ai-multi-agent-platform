import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatPct(val: number) {
  return `${val.toFixed(1)}%`;
}

export function sentimentColor(label: string) {
  return { positive: "#22c55e", neutral: "#f59e0b", negative: "#ef4444" }[label] || "#94a3b8";
}

export function severityColor(s: string) {
  return { critical: "#dc2626", high: "#ea580c", medium: "#d97706", low: "#65a30d" }[s] || "#94a3b8";
}
