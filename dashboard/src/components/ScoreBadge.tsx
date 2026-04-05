import React from "react";
import { clsx } from "clsx";

interface ScoreBadgeProps {
  score: number;
}

const ScoreBadge: React.FC<ScoreBadgeProps> = ({ score }) => {
  const colorClass =
    score >= 0.8
      ? "text-emerald-700 bg-emerald-50 ring-1 ring-emerald-200"
      : score >= 0.5
        ? "text-amber-700 bg-amber-50 ring-1 ring-amber-200"
        : "text-red-600 bg-red-50 ring-1 ring-red-200";

  return (
    <span
      className={clsx(
        "inline-flex items-center px-3 py-1 rounded-full text-xs font-bold tabular-nums",
        colorClass
      )}
    >
      {score.toFixed(2)}
    </span>
  );
};

export default ScoreBadge;
