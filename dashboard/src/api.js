const BASE = import.meta.env.DEV ? "/api" : "";
export const fetchHealth = () => fetch(`${BASE}/health`).then(r => r.json());
export const fetchStats = () => fetch(`${BASE}/stats`).then(r => r.json());
export const fetchLeaderboard = (taskId, limit = 10) => fetch(`${BASE}/leaderboard?task_id=${taskId}&limit=${limit}`)
    .then(r => r.json())
    .then(data => data.entries || []);
