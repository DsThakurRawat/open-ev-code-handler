import { jsx as _jsx } from "react/jsx-runtime";
import { clsx } from "clsx";
const ScoreBadge = ({ score }) => {
    const colorClass = score >= 0.8
        ? "text-emerald-700 bg-emerald-50 ring-1 ring-emerald-200"
        : score >= 0.5
            ? "text-amber-700 bg-amber-50 ring-1 ring-amber-200"
            : "text-red-600 bg-red-50 ring-1 ring-red-200";
    return (_jsx("span", { className: clsx("inline-flex items-center px-3 py-1 rounded-full text-xs font-bold tabular-nums", colorClass), children: score.toFixed(2) }));
};
export default ScoreBadge;
