import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Trophy, RefreshCw } from "lucide-react";
import { fetchLeaderboard } from "../api";
import LeaderboardTable from "./LeaderboardTable";
import { clsx } from "clsx";
const Leaderboard = () => {
    const [activeTab, setActiveTab] = useState("bug_detection");
    const { data: entries, isLoading, refetch, isRefetching } = useQuery({
        queryKey: ["leaderboard", activeTab],
        queryFn: () => fetchLeaderboard(activeTab),
    });
    const tabs = [
        { id: "bug_detection", label: "Bug Detection" },
        { id: "security_audit", label: "Security Audit" },
        { id: "architectural_review", label: "Arch. Review" },
    ];
    return (_jsxs("div", { className: "bg-white rounded-3xl overflow-hidden flex flex-col h-[600px]", style: { border: "1px solid var(--color-border)" }, children: [_jsxs("div", { className: "px-7 py-5 flex items-center justify-between", style: { borderBottom: "1px solid var(--color-border)" }, children: [_jsxs("div", { className: "flex items-center gap-3", children: [_jsx("div", { className: "p-2 bg-amber-50 rounded-xl", children: _jsx(Trophy, { className: "w-5 h-5 text-amber-600" }) }), _jsx("h2", { className: "text-lg font-extrabold tracking-tight", style: { color: "var(--color-heading)" }, children: "Leaderboard" })] }), _jsx("button", { onClick: () => refetch(), disabled: isLoading || isRefetching, className: "p-2.5 hover:bg-zinc-100 rounded-xl transition-colors disabled:opacity-40", style: { color: "var(--color-muted)" }, children: _jsx(RefreshCw, { className: clsx("w-4 h-4", (isLoading || isRefetching) && "animate-spin") }) })] }), _jsx("div", { className: "px-7", style: { borderBottom: "1px solid var(--color-border)" }, children: _jsx("div", { className: "flex gap-6 overflow-x-auto", children: tabs.map((tab) => (_jsxs("button", { onClick: () => setActiveTab(tab.id), className: clsx("py-3.5 text-sm font-semibold transition-all relative whitespace-nowrap", activeTab === tab.id
                            ? "text-zinc-900"
                            : "text-zinc-400 hover:text-zinc-600"), children: [tab.label, activeTab === tab.id && (_jsx("div", { className: "absolute bottom-0 left-0 right-0 h-[2px] bg-zinc-900 rounded-full" }))] }, tab.id))) }) }), _jsx("div", { className: "flex-1 overflow-auto", children: isLoading ? (_jsxs("div", { className: "flex items-center justify-center h-full gap-3", style: { color: "var(--color-muted)" }, children: [_jsx(RefreshCw, { className: "w-5 h-5 animate-spin" }), _jsx("span", { className: "text-sm font-medium", children: "Loading entries..." })] })) : entries && entries.length > 0 ? (_jsx(LeaderboardTable, { entries: entries })) : (_jsxs("div", { className: "flex flex-col items-center justify-center h-full space-y-4", children: [_jsx("div", { className: "p-5 bg-zinc-50 rounded-2xl", children: _jsx(Trophy, { className: "w-10 h-10 text-zinc-200" }) }), _jsx("p", { className: "text-xs font-bold uppercase tracking-[0.15em]", style: { color: "var(--color-muted)" }, children: "No rankings yet" })] })) })] }));
};
export default Leaderboard;
