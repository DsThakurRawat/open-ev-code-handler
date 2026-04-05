import { HealthResponse, StatsResponse, LeaderboardEntry, TaskId } from "./types";

const BASE = import.meta.env.DEV ? "/api" : "";

export const fetchHealth  = (): Promise<HealthResponse>         => fetch(`${BASE}/health`).then(r => r.json());
export const fetchStats   = (): Promise<StatsResponse>          => fetch(`${BASE}/stats`).then(r => r.json());
export const fetchLeaderboard = (taskId: TaskId, limit = 10): Promise<LeaderboardEntry[]> =>
  fetch(`${BASE}/leaderboard?task_id=${taskId}&limit=${limit}`)
    .then(r => r.json())
    .then(data => data.entries || []);
