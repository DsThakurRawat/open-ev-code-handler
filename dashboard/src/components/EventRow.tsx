import React from "react";
import { WsEvent } from "../types";
import { clsx } from "clsx";

interface EventRowProps {
  event: WsEvent;
}

const EventRow: React.FC<EventRowProps> = ({ event }) => {
  const time = new Date(event.timestamp).toLocaleTimeString([], {
    hour12: false,
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });

  return (
    <div
      className="rounded-2xl p-4 transition-all duration-200 hover:shadow-sm animate-fade-slide-in"
      style={{
        backgroundColor: "#fafafa",
        border: "1px solid var(--color-border)",
      }}
    >
      <div className="flex items-center justify-between mb-2">
        <span
          className="text-[10px] tabular-nums font-bold uppercase tracking-wider"
          style={{ color: "var(--color-muted)" }}
        >
          {time}
        </span>
        <span className="text-[10px] font-mono font-bold bg-indigo-50 text-indigo-600 px-2 py-0.5 rounded-md">
          {event.episode_id.slice(0, 8)}
        </span>
      </div>
      <div className="flex items-center justify-between">
        <span
          className="text-sm font-semibold capitalize truncate max-w-[140px]"
          style={{ color: "var(--color-heading)" }}
        >
          {event.type}
        </span>
        <span
          className={clsx(
            "text-xs font-bold font-mono px-2.5 py-1 rounded-full",
            event.reward > 0
              ? "text-emerald-700 bg-emerald-50"
              : event.reward < 0
                ? "text-red-600 bg-red-50"
                : "text-zinc-500 bg-zinc-100"
          )}
        >
          {event.reward > 0 ? "+" : ""}
          {event.reward.toFixed(2)}
        </span>
      </div>
    </div>
  );
};

export default EventRow;
