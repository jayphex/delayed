"use client";
import { useState } from "react";
import { fetchGames, fetchSummary, markWatched, markUnwatched, fetchWatchLog } from "../lib/api";
import { stringify } from "querystring";

export default function Home() {
  const [games, setGames] = useState<{game_id: string, home_team: string, away_team: string, delay_minutes: number}[]>([]);
  const [watched, setWatched] = useState<"all"|"true"|"false">("all");
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState<{countDelayed: number, avgDelay: number, maxDelay: number} | null>(null);
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
      setWatchedIDs(new Set(watchLog.map((e: any) => e.game_id)));

      setSummary(await fetchSummary(query));
    } catch (e:any) { setErr(e.message ?? "error"); }
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
      <div style={{display:"flex", gap:8, marginBottom:12}}>
        <select value={watched} onChange={e=>setWatched(e.target.value as any)}>
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
        <button onClick={load}>Games</button>
      </div>
      {loading && <p>Loading…</p>}
      {err && <p style={{color:"red"}}>{err}</p>}
      {summary && (
        <p>
          Delayed: {summary.countDelayed} |
          Average: {summary.avgDelay.toFixed(1)} |
          Max: {summary.maxDelay}
        </p>
      )}
      <ul>
        {games.map((g)=> {
          const isWatched = watchedIDs.has(g.game_id);
          return (
            <li key={g.game_id} style={{marginBottom:8}}>
              {g.away_team} @ {g.home_team} — delay {g.delay_minutes} min
              { isWatched 
                ? <button onClick={()=>onUnwatch(String(g.game_id))}>unWatch</button>
                : <button onClick={()=>onWatch(String(g.game_id))}>Watch</button>
              }
            </li>
          );
        })}
      </ul>
    </main>
  );
}
