export interface HealthResponse {
  status: string;
  active_episodes: number;
  dashboard_url: string;
}

export interface StatsResponse {
  total_episodes: number;
  avg_score: number;
}

export interface LeaderboardEntry {
  rank: number;
  agent_name: string;
  score: number;
  seed: number;
  submitted_at: string;
}

export type TaskId = "bug_detection" | "security_audit" | "architectural_review";

export interface WsEvent {
  episode_id: string;
  type: string;
  reward: number;
  timestamp: string;
}
