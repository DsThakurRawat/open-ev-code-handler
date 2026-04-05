import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
const StatCard = ({ label, value, icon, iconBg }) => {
    return (_jsxs("div", { className: "bg-white rounded-3xl p-7 transition-all duration-200 hover:shadow-lg hover:-translate-y-0.5 group", style: { border: "1px solid var(--color-border)" }, children: [_jsxs("div", { className: "flex items-start justify-between mb-5", children: [_jsx("p", { className: "text-[11px] font-bold uppercase tracking-[0.12em]", style: { color: "var(--color-muted)" }, children: label }), _jsx("div", { className: `p-2.5 rounded-xl transition-transform group-hover:scale-110 ${iconBg}`, children: icon })] }), _jsx("h3", { className: "text-4xl font-extrabold tracking-tight tabular-nums", style: { color: "var(--color-heading)" }, children: value })] }));
};
export default StatCard;
