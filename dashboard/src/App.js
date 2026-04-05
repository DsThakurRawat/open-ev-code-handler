import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import Header from "./components/Header";
import StatsRow from "./components/StatsRow";
import Leaderboard from "./components/Leaderboard";
import EventFeed from "./components/EventFeed";
import { useWebSocket } from "./hooks/useWebSocket";
const App = () => {
    useWebSocket();
    return (_jsx("div", { className: "min-h-screen", style: { backgroundColor: "var(--color-bg)" }, children: _jsxs("div", { className: "max-w-7xl mx-auto px-6 py-10 space-y-10", children: [_jsx(Header, {}), _jsx(StatsRow, {}), _jsxs("div", { className: "grid grid-cols-1 lg:grid-cols-3 gap-8", children: [_jsx("div", { className: "lg:col-span-2", children: _jsx(Leaderboard, {}) }), _jsx("div", { className: "lg:col-span-1", children: _jsx(EventFeed, {}) })] })] }) }));
};
export default App;
