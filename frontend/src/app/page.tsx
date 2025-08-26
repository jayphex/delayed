"use client";
import { useState } from "react";
import { fetchGames, fetchSummary, markWatched } from "../lib/api";

export default function Home() {
  const [games, setGames] = useState<any[]>([]);
  const [watched, setWatched] = useState<"all"|"true"|"false">("all");
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState<{countDelay: number, avgDelay: number, maxDelay: number} | null>(null);
  const [err, setErr] = useState<string|null>(null);

  async function load() {
    try {
      setLoading(true); setErr(null);
      const params = watched === "all" ? "" : `watched=${watched}`;
      setGames(await fetchGames(params));
      setSummary(await fetchSummary());
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
        <button onClick={load}>Load Games</button>
      </div>
      {loading && <p>Loading…</p>}
      {err && <p style={{color:"red"}}>{err}</p>}
      {summary && (
        <p>
          Amount of Delay: {summary.countDelay} |
          Average Delay: {summary.avgDelay.toFixed(1)} |
          Max Delay: {summary.maxDelay}
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
