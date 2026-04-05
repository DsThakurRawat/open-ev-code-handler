import React from "react";
import { Zap, Trash2 } from "lucide-react";
import { useEventStore } from "../stores/eventStore";
import EventRow from "./EventRow";

const EventFeed: React.FC = () => {
  const { events, clear, connected } = useEventStore();

  return (
    <div
      className="bg-white rounded-3xl overflow-hidden flex flex-col h-[600px]"
      style={{ border: "1px solid var(--color-border)" }}
    >
      {/* Header */}
      <div
        className="px-7 py-5 flex items-center justify-between"
        style={{ borderBottom: "1px solid var(--color-border)" }}
      >
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-xl ${connected ? "bg-amber-50" : "bg-zinc-100"}`}>
            <Zap className={`w-5 h-5 ${connected ? "text-amber-600" : "text-zinc-400"}`} />
          </div>
          <h2 className="text-lg font-extrabold tracking-tight" style={{ color: "var(--color-heading)" }}>
            Live Feed
          </h2>
        </div>
        <button
          onClick={clear}
          className="p-2.5 hover:bg-zinc-100 rounded-xl transition-colors"
          style={{ color: "var(--color-muted)" }}
          title="Clear Feed"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-5 space-y-3">
        {!connected && (
          <div className="flex flex-col items-center justify-center h-full space-y-4 text-center">
            <div className="p-5 bg-zinc-50 rounded-2xl">
              <Zap className="w-10 h-10 text-zinc-200 animate-pulse" />
            </div>
            <p className="text-[11px] uppercase tracking-[0.15em] font-bold" style={{ color: "var(--color-muted)" }}>
              Connecting to live stream...
            </p>
          </div>
        )}

        {connected && events.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full space-y-4 text-center">
            <div className="p-5 bg-zinc-50 rounded-2xl">
              <Zap className="w-10 h-10 text-zinc-200" />
            </div>
            <div className="space-y-1.5">
              <p className="text-[11px] font-bold uppercase tracking-[0.15em]" style={{ color: "var(--color-muted)" }}>
                Monitoring activity
              </p>
              <p className="text-[11px] max-w-[180px] leading-relaxed" style={{ color: "var(--color-muted)" }}>
                Evaluation events will appear here in real-time.
              </p>
            </div>
          </div>
        )}

        {events.map((event, idx) => (
          <EventRow key={idx} event={event} />
        ))}
      </div>
    </div>
  );
};

export default EventFeed;
