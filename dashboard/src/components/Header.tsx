import React from "react";
import { useQuery } from "@tanstack/react-query";
import { Wifi, WifiOff } from "lucide-react";
import { fetchHealth } from "../api";
import { clsx } from "clsx";

const Header: React.FC = () => {
  const { data: health } = useQuery({
    queryKey: ["health"],
    queryFn: fetchHealth,
    refetchInterval: 10_000,
  });

  const isConnected = health?.status === "ok";

  return (
    <header className="flex items-center justify-between pb-2">
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2">
          {/* Logo Replacement */}
          <img src="/dashboard/logo.svg" className="h-[38px] w-auto" alt="CodeLens." />
          <div className="h-5 w-px bg-zinc-200 hidden sm:block mx-2" />
          <p className="text-[10px] font-mono font-bold uppercase tracking-[0.3em] hidden sm:block pt-1 opacity-40 group-hover:opacity-60 transition-opacity" style={{ color: "var(--color-heading)" }}>
            Evaluation
          </p>
        </div>
      </div>

      <div className={clsx(
        "flex items-center gap-2 px-4 py-2 rounded-full text-xs font-semibold tracking-wide uppercase transition-all",
        isConnected
          ? "bg-emerald-50 text-emerald-600 ring-1 ring-emerald-200"
          : "bg-red-50 text-red-500 ring-1 ring-red-200"
      )}>
        {isConnected ? (
          <>
            <Wifi className="w-3.5 h-3.5" />
            <span>Connected</span>
          </>
        ) : (
          <>
            <WifiOff className="w-3.5 h-3.5" />
            <span>Offline</span>
          </>
        )}
      </div>
    </header>
  );
};

export default Header;
