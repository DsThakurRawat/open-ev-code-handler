import { create } from "zustand";
export const useEventStore = create((set) => ({
    events: [],
    connected: false,
    push: (e) => set((s) => ({ events: [e, ...s.events].slice(0, 20) })),
    clear: () => set({ events: [] }),
    setConnected: (v) => set({ connected: v }),
}));
