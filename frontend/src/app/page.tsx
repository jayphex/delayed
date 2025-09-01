"use client";
import { Game, Summary, WatchLogEntry } from "../lib/types";
import { useState } from "react";
import { fetchGames, fetchSummary, markWatched, markUnwatched, fetchWatchLog } from "../lib/api";
import Hero from "@/components/Hero";

export default function Home() {
  const [games, setGames] = useState<Game[]>([]);
  const [watched, setWatched] = useState<"all"|"true"|"false">("all");
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [err, setErr] = useState<string|null>(null);
  const [team, setTeam] = useState<string>("");
  const teams = [
    "ATL", "BKN", "BOS", "CHA", "CHI", "CLE", "DAL", "DEN", "DET", "GSW", "HOU",
    "IND", "LAC", "LAL", "MEM", "MIA", "MIL", "MIN", "NOP", "NYK", "OKC",
    "ORL", "PHI", "PHX", "POR", "SAC", "SAS", "TOR", "UTA", "WAS"
  ];
  const [date, setDate] = useState<string>("");
  const [watchedIDs, setWatchedIDs] = useState<Set<string>>(new Set());

  async function load() {
    try {
      setLoading(true); setErr(null);
      const params = new URLSearchParams();
      if (watched !== "all") params.append("watched", watched);
      if (team) params.append("team", team);
      if (date) params.append("date", date);
      const query = params.toString();

      setGames(await fetchGames(query));

      const watchLog = await fetchWatchLog();
      setWatchedIDs(new Set(watchLog.map((e: WatchLogEntry) => e.game_id)));

      setSummary(await fetchSummary(query));
    } catch (e: unknown) {
      if (e instanceof Error) {
        setErr(e.message ?? "error");
      } else {
        setErr("error");
      }
    }
    finally { setLoading(false); }
  }

  async function onWatch(id: string) {
    await markWatched(id);
    load();
  }

  async function onUnwatch(id: string) {
    await markUnwatched(id);
    load();
  }

  return (
    <main style={{padding:16}}>
      <Hero />
      <div className="filters" style={{display:"flex", gap:8, marginBottom:12}}>
        <select value={watched} onChange={e=>setWatched(e.target.value as "all"|"true"|"false")}>
          <option value="all">All</option>
          <option value="true">Watched</option>
          <option value="false">Unwatched</option>
        </select>
        <select value={team} onChange={(e=>setTeam(e.target.value))}>
          <option value="">All Teams</option>
          {teams.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
        <input type="date" value={date} onChange={(e=>setDate(e.target.value))}
          style = {{padding:4, fontSize: 16}} />
        <button className="gamesButton" onClick={load}>Games</button>
      </div>
      {loading && <p>Loading…</p>}
      {err && <p style={{color:"red"}}>{err}</p>}
      {summary && (
        <div className="summary">
          <p><strong>Games Delayed:</strong> {summary.countDelayed}</p>
          <p><strong>Average Delay:</strong> {summary.avgDelay.toFixed(1)}</p>
          <p><strong>Most Delayed Game:</strong> {summary.maxDelay}</p>
        </div>
      )}
      <ul>
        {games.map((g)=> {
          const isWatched = watchedIDs.has(g.game_id);
          return (
            <li key={g.game_id} style={{marginBottom:8}}>
              {g.away_team} @ {g.home_team} — delay {g.delay_minutes} min
              { isWatched 
                ? <button className="unwatchButton" onClick={()=>onUnwatch(String(g.game_id))}>Unwatch</button>
                : <button className="watchButton" onClick={()=>onWatch(String(g.game_id))}>Watch</button>
              }
            </li>
          );
        })}
      </ul>
    </main>
  );
}
