"use client";
import { useState, useSyncExternalStore } from "react";
import { fetchGames, fetchSummary, markWatched } from "../lib/api";

export default function Home() {
  const [games, setGames] = useState<any[]>([]);
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

  async function load() {
    try {
      setLoading(true); setErr(null);
      const params = new URLSearchParams();
      if (watched !== "all") params.append("watched", watched);
      if (team) params.append("team", team);
      if (date) params.append("date", date);
      const query = params.toString();
      setGames(await fetchGames(query));
      setSummary(await fetchSummary(query));
    } catch (e:any) { setErr(e.message ?? "error"); }
    finally { setLoading(false); }
  }

  async function onMark(id: string) {
    await markWatched(id);
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
          <option value="team">All Teams</option>
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
        {games.map((g)=>(
          <li key={g.game_id} style={{marginBottom:8}}>
            {g.away_team} @ {g.home_team} — delay {g.delay_minutes} min
            {" "}
            <button onClick={()=>onMark(String(g.game_id))}>Mark as watched</button>
          </li>
        ))}
      </ul>
    </main>
  );
}
