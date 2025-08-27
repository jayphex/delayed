export interface Game {
    game_id: string;
    home_team: string;
    away_team: string;
    delay_minutes: number;
    watched?: boolean;
}

export interface Summary {
    countDelayed: number;
    avgDelay: number;
    maxDelay: number;
}

export interface WatchLogEntry {
    id: number;
    user_id: string;
    game_id: string;
    watched_at: string; // ISO date string
}