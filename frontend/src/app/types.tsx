type Game = {
    game_id: string;
    home_team: string;
    away_team: string;
    delay_minutes: number;
    watched?: boolean;
}

type Summary = {
    countDelayed: number;
    avgDelay: number;
    maxDelay: number;
}