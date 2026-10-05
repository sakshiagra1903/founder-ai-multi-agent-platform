import clsx from "clsx";

interface ScoreBadgeProps {
  score: number;
  size?: "sm" | "lg";
}

export default function ScoreBadge({ score, size = "sm" }: ScoreBadgeProps) {
  const color =
    score >= 80
      ? "bg-green-100 text-green-700 ring-green-300"
      : score >= 60
      ? "bg-yellow-100 text-yellow-700 ring-yellow-300"
      : "bg-red-100 text-red-700 ring-red-300";

  return (
    <span
      className={clsx(
        "inline-flex items-center justify-center font-bold rounded-full ring-1",
        color,
        size === "lg" ? "w-16 h-16 text-xl" : "px-2.5 py-0.5 text-sm"
      )}
    >
      {Math.round(score)}
    </span>
  );
}
