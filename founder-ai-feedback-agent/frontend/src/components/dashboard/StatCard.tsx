import { cn } from "@/lib/utils";
import type { LucideIcon } from "lucide-react";

interface Props {
  title: string; value: string | number; subtitle?: string;
  icon: LucideIcon; color?: string; trend?: string;
}

export default function StatCard({ title, value, subtitle, icon: Icon, color = "bg-blue-500", trend }: Props) {
  return (
    <div className="card flex items-start gap-4">
      <div className={cn("w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0", color)}>
        <Icon className="w-6 h-6 text-white" />
      </div>
      <div>
        <p className="text-sm text-slate-500 font-medium">{title}</p>
        <p className="text-2xl font-bold text-slate-900 mt-0.5">{value}</p>
        {subtitle && <p className="text-xs text-slate-400 mt-1">{subtitle}</p>}
        {trend && <p className="text-xs font-medium text-blue-600 mt-1">{trend}</p>}
      </div>
    </div>
  );
}
