import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useQuery } from "@tanstack/react-query";
import { Trophy, Zap, Activity } from "lucide-react";
import { fetchStats, fetchHealth } from "../api";
import StatCard from "./StatCard";
const StatsRow = () => {
    const { data: stats } = useQuery({
        queryKey: ["stats"],
        queryFn: fetchStats,
        refetchInterval: 30_000,
    });
    const { data: health } = useQuery({
        queryKey: ["health"],
        queryFn: fetchHealth,
        refetchInterval: 10_000,
    });
    return (_jsxs("div", { className: "grid grid-cols-1 md:grid-cols-3 gap-6", children: [_jsx(StatCard, { label: "Total Episodes", value: stats?.total_episodes ?? 0, icon: _jsx(Trophy, { className: "w-5 h-5 text-amber-600" }), iconBg: "bg-amber-50" }), _jsx(StatCard, { label: "Avg. Score", value: stats?.avg_score?.toFixed(2) ?? "0.00", icon: _jsx(Zap, { className: "w-5 h-5 text-blue-600" }), iconBg: "bg-blue-50" }), _jsx(StatCard, { label: "Active Episodes", value: health?.active_episodes ?? 0, icon: _jsx(Activity, { className: "w-5 h-5 text-emerald-600" }), iconBg: "bg-emerald-50" })] }));
};
export default StatsRow;
