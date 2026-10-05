type Rec = "Strong Hire" | "Hire" | "Consider" | "Reject" | string;

const styles: Record<string, { bg: string; text: string; dot: string }> = {
  "Strong Hire": { bg: "bg-emerald-50", text: "text-emerald-700", dot: "bg-emerald-500" },
  "Hire":        { bg: "bg-blue-50",    text: "text-blue-700",    dot: "bg-blue-500" },
  "Consider":    { bg: "bg-amber-50",   text: "text-amber-700",   dot: "bg-amber-500" },
  "Reject":      { bg: "bg-red-50",     text: "text-red-700",     dot: "bg-red-400" },
};

export default function HiringBadge({ recommendation }: { recommendation: Rec }) {
  const s = styles[recommendation] || styles["Reject"];
  const icons = {
    "Strong Hire": "✅",
    "Hire":        "🟢",
    "Consider":    "🟡",
    "Reject":      "🔴",
  };
  const icon = (icons as any)[recommendation] || "•";

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${s.bg} ${s.text} border-current/10`}>
      <span>{icon}</span>
      {recommendation}
    </span>
  );
}
