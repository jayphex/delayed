export interface Game {
  game_id: string;
  date: string;
  home_team: string;
  away_team: string;
  scheduled_start: string | null;
  actual_start: string | null;
  status: string;
  delay_minutes: number;
  started_late: boolean;
  tipoff_state: "scheduled" | "late" | "on_time";
  watched: boolean;
}

export interface Summary {
  games: number;
  countDelayed: number;
  avgDelay: number;
  maxDelay: number;
  watchedGames: number;
  totalDelayMinutes: number;
  watchedDelayMinutes: number;
}

export interface WatchLogEntry {
  id: number;
  user_id: string;
  game_id: string;
  watched_at: string;
}
