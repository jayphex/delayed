"use client";

import { startTransition, useEffect, useState } from "react";

import Hero from "@/components/Hero";
import {
  fetchGames,
  fetchSummary,
  fetchWatchLog,
  markUnwatched,
  markWatched,
} from "@/lib/api";
import { Game, Summary, WatchLogEntry } from "@/lib/types";

const TEAMS = [
  "ATL",
  "BKN",
  "BOS",
  "CHA",
  "CHI",
  "CLE",
  "DAL",
  "DEN",
  "DET",
  "GSW",
  "HOU",
  "IND",
  "LAC",
  "LAL",
  "MEM",
  "MIA",
  "MIL",
  "MIN",
  "NOP",
  "NYK",
  "OKC",
  "ORL",
  "PHI",
  "PHX",
  "POR",
  "SAC",
  "SAS",
  "TOR",
  "UTA",
  "WAS",
];

function formatTipoff(value: string | null): string {
  if (!value) {
    return "Not tipped yet";
  }

  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(value));
}

function delayLabel(game: Game): string {
  if (!game.actual_start) {
    return "Awaiting tip";
  }
  if (game.delay_minutes <= 0) {
    return "On time";
  }
  return `+${game.delay_minutes.toFixed(1)} min`;
}

export default function Home() {
  const [games, setGames] = useState<Game[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [watchLog, setWatchLog] = useState<WatchLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [watched, setWatched] = useState<"all" | "true" | "false">("all");
  const [team, setTeam] = useState("");
  const [date, setDate] = useState("");
  const [minDelay, setMinDelay] = useState("0");

  function buildQuery() {
    const params = new URLSearchParams();
    if (watched !== "all") {
      params.append("watched", watched);
    }
    if (team) {
      params.append("team", team);
    }
    if (date) {
      params.append("date", date);
    }
    if (Number(minDelay) > 0) {
      params.append("minDelay", minDelay);
    }
    return params.toString();
  }

  const query = buildQuery();

  async function loadBoard() {
    try {
      setLoading(true);
      setError(null);

      const [gamesResponse, summaryResponse, watchLogResponse] = await Promise.all([
        fetchGames(query),
        fetchSummary(query),
        fetchWatchLog(),
      ]);

      startTransition(() => {
        setGames(gamesResponse);
        setSummary(summaryResponse);
        setWatchLog(watchLogResponse);
      });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unable to load the board.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadBoard();
  }, [query]);

  async function toggleWatched(game: Game) {
    try {
      if (game.watched) {
        await markUnwatched(game.game_id);
      } else {
        await markWatched(game.game_id);
      }
      await loadBoard();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unable to update watch list.");
    }
  }

  const watchedGames = watchLog.length;

  return (
    <main className="page-shell">
      <div className="page-backdrop" />
      <section className="board">
        <Hero summary={summary} />

        <section className="cards" aria-label="Summary stats">
          <article className="card">
            <span>Games on board</span>
            <strong>{summary?.games ?? 0}</strong>
            <p>Current slice after your filters.</p>
          </article>
          <article className="card">
            <span>Total waiting time</span>
            <strong>{summary?.totalDelayMinutes.toFixed(1) ?? "0.0"} min</strong>
            <p>Combined delay across the games in view.</p>
          </article>
          <article className="card">
            <span>Your watched games</span>
            <strong>{watchedGames}</strong>
            <p>{summary?.watchedDelayMinutes.toFixed(1) ?? "0.0"} minutes lost.</p>
          </article>
          <article className="card">
            <span>Worst delay</span>
            <strong>{summary?.maxDelay.toFixed(1) ?? "0.0"} min</strong>
            <p>Longest late tip in this board.</p>
          </article>
        </section>

        <section className="panel">
          <div className="panel__header">
            <div>
              <h2>Filter the slate</h2>
              <p>Focus on a date, a team, or only games that started meaningfully late.</p>
            </div>
            <button className="ghost-button" onClick={() => void loadBoard()} type="button">
              Refresh board
            </button>
          </div>

          <div className="filters">
            <label>
              Watch state
              <select value={watched} onChange={(event) => setWatched(event.target.value as "all" | "true" | "false")}>
                <option value="all">All games</option>
                <option value="true">Watched only</option>
                <option value="false">Unwatched only</option>
              </select>
            </label>
            <label>
              Team
              <select value={team} onChange={(event) => setTeam(event.target.value)}>
                <option value="">All teams</option>
                {TEAMS.map((teamCode) => (
                  <option key={teamCode} value={teamCode}>
                    {teamCode}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Date
              <input type="date" value={date} onChange={(event) => setDate(event.target.value)} />
            </label>
            <label>
              Min delay
              <input
                type="number"
                min="0"
                step="1"
                value={minDelay}
                onChange={(event) => setMinDelay(event.target.value)}
              />
            </label>
          </div>
        </section>

        <section className="panel panel--tight">
          <div className="panel__header">
            <div>
              <h2>Delay board</h2>
              <p>Scheduled tip, observed tip-off, and whether that game cost you waiting time.</p>
            </div>
            {loading ? <span className="status-pill">Refreshing</span> : null}
          </div>

          {error ? <p className="error-banner">{error}</p> : null}

          {!loading && games.length === 0 ? (
            <div className="empty-state">
              <h3>No games match these filters.</h3>
              <p>Try widening the date range or lowering the minimum delay.</p>
            </div>
          ) : (
            <div className="games-grid">
              {games.map((game) => (
                <article className="game-card" key={game.game_id}>
                  <div className="game-card__row">
                    <div>
                      <div className="matchup">
                        {game.away_team} <span>@</span> {game.home_team}
                      </div>
                      <p className="game-card__meta">
                        {game.date} • {game.status.replace("_", " ")}
                      </p>
                    </div>
                    <span className={`delay-pill delay-pill--${game.tipoff_state}`}>
                      {delayLabel(game)}
                    </span>
                  </div>

                  <dl className="tip-grid">
                    <div>
                      <dt>Scheduled</dt>
                      <dd>{formatTipoff(game.scheduled_start)}</dd>
                    </div>
                    <div>
                      <dt>Observed tip</dt>
                      <dd>{formatTipoff(game.actual_start)}</dd>
                    </div>
                  </dl>

                  <div className="game-card__footer">
                    <p>
                      {game.watched
                        ? "You marked this one as watched."
                        : "Add this game to your watched log to track your lost time."}
                    </p>
                    <button
                      className={game.watched ? "watch-button watch-button--active" : "watch-button"}
                      onClick={() => void toggleWatched(game)}
                      type="button"
                    >
                      {game.watched ? "Remove from watched" : "Mark as watched"}
                    </button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      </section>
    </main>
  );
}
