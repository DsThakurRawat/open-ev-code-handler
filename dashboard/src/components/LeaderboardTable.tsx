import React from "react";
import { LeaderboardEntry } from "../types";
import ScoreBadge from "./ScoreBadge";

interface LeaderboardTableProps {
  entries: LeaderboardEntry[];
}

const LeaderboardTable: React.FC<LeaderboardTableProps> = ({ entries }) => {
  return (
    <table className="w-full text-left border-collapse">
      <thead>
        <tr style={{ borderBottom: "1px solid var(--color-border)" }}>
          <th className="px-7 py-4 text-[10px] font-bold uppercase tracking-[0.12em]" style={{ color: "var(--color-muted)" }}>
            Rank
          </th>
          <th className="px-7 py-4 text-[10px] font-bold uppercase tracking-[0.12em]" style={{ color: "var(--color-muted)" }}>
            Agent
          </th>
          <th className="px-7 py-4 text-[10px] font-bold uppercase tracking-[0.12em] text-center" style={{ color: "var(--color-muted)" }}>
            Score
          </th>
          <th className="px-7 py-4 text-[10px] font-bold uppercase tracking-[0.12em] text-right" style={{ color: "var(--color-muted)" }}>
            Seed
          </th>
          <th className="px-7 py-4 text-[10px] font-bold uppercase tracking-[0.12em] text-right" style={{ color: "var(--color-muted)" }}>
            Submitted
          </th>
        </tr>
      </thead>
      <tbody>
        {entries.map((entry, idx) => (
          <tr
            key={idx}
            className="group hover:bg-zinc-50/80 transition-colors tabular-nums"
            style={{ borderBottom: "1px solid var(--color-border)" }}
          >
            <td className="px-7 py-5">
              {idx < 3 ? (
                <span
                  className={`
                    inline-flex items-center justify-center w-7 h-7 rounded-lg text-xs font-extrabold
                    ${idx === 0 ? "bg-amber-50 text-amber-600" : ""}
                    ${idx === 1 ? "bg-zinc-100 text-zinc-500" : ""}
                    ${idx === 2 ? "bg-orange-50 text-orange-500" : ""}
                  `}
                >
                  {entry.rank}
                </span>
              ) : (
                <span className="text-sm font-semibold pl-2" style={{ color: "var(--color-muted)" }}>
                  {entry.rank}
                </span>
              )}
            </td>
            <td className="px-7 py-5">
              <span className="font-semibold group-hover:text-zinc-900 transition-colors" style={{ color: "var(--color-heading)" }}>
                {entry.agent_name}
              </span>
            </td>
            <td className="px-7 py-5 text-center">
              <ScoreBadge score={entry.score} />
            </td>
            <td className="px-7 py-5 text-right text-sm font-mono" style={{ color: "var(--color-muted)" }}>
              {entry.seed}
            </td>
            <td className="px-7 py-5 text-right text-xs" style={{ color: "var(--color-muted)" }}>
              {new Date(entry.submitted_at).toLocaleDateString()}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};

export default LeaderboardTable;
