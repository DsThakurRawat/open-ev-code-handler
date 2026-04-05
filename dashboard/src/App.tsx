import React from "react";
import Header from "./components/Header";
import StatsRow from "./components/StatsRow";
import Leaderboard from "./components/Leaderboard";
import EventFeed from "./components/EventFeed";
import { useWebSocket } from "./hooks/useWebSocket";

const App: React.FC = () => {
  useWebSocket();

  return (
    <div className="min-h-screen" style={{ backgroundColor: "var(--color-bg)" }}>
      <div className="max-w-7xl mx-auto px-6 py-10 space-y-10">
        <Header />
        <StatsRow />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2">
            <Leaderboard />
          </div>
          <div className="lg:col-span-1">
            <EventFeed />
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;
