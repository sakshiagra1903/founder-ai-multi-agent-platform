import { AlertTriangle, Lightbulb, MessageSquare } from "lucide-react";

type Type = "warning" | "info" | "question";

const config = {
  warning: { bg: "bg-amber-50", border: "border-amber-200", icon: AlertTriangle, color: "text-amber-600" },
  info:    { bg: "bg-blue-50",  border: "border-blue-200",  icon: Lightbulb, color: "text-blue-600" },
  question: { bg: "bg-purple-50", border: "border-purple-200", icon: MessageSquare, color: "text-purple-600" },
};

export default function AlertBox({ type, title, items }: { type: Type; title: string; items: string[] }) {
  const c = config[type];
  const Icon = c.icon;

  return (
    <div className={`${c.bg} border ${c.border} rounded-xl p-3.5`}>
      <div className={`flex items-center gap-2 mb-2 ${c.color}`}>
        <Icon className="w-4 h-4 flex-shrink-0" />
        <span className="text-xs font-semibold uppercase tracking-wide">{title}</span>
      </div>
      <ul className="space-y-1.5">
        {items.map((item, i) => (
          <li key={i} className={`text-sm ${c.color}`}>{item}</li>
        ))}
      </ul>
    </div>
  );
}
