import { create } from "zustand";
import { WsEvent } from "../types";

interface EventStore {
  events: WsEvent[];
  connected: boolean;
  push: (e: WsEvent) => void;
  clear: () => void;
  setConnected: (v: boolean) => void;
}

export const useEventStore = create<EventStore>((set) => ({
  events: [],
  connected: false,
  push: (e) => set((s) => ({ events: [e, ...s.events].slice(0, 20) })),
  clear: () => set({ events: [] }),
  setConnected: (v) => set({ connected: v }),
}));
