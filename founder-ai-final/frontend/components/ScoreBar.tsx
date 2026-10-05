interface Props {
  label: string;
  value: number;
}

export default function ScoreBar({ label, value }: Props) {
  const pct = Math.min(100, Math.max(0, Math.round(value)));
  const color = pct >= 85 ? "#10b981" : pct >= 70 ? "#6d5ef5" : pct >= 55 ? "#f59e0b" : "#ef4444";

  return (
    <div>
      <div className="flex justify-between items-center mb-1.5">
        <span className="text-xs font-semibold text-gray-600">{label}</span>
        <span className="text-xs font-bold" style={{ color }}>{pct}</span>
      </div>
      <div className="h-2 rounded-full bg-gray-100 overflow-hidden">
        <div className="h-full rounded-full transition-all duration-700" style={{ width: `${pct}%`, background: color }} />
      </div>
    </div>
  );
}
