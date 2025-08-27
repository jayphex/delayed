import { WatchLogEntry } from "./types";

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE!;

export async function fetchGames(params = "") {
  const r = await fetch(`${API_BASE}/games${params ? `?${params}` : ""}`);
  if (!r.ok) throw new Error("/games failed");
  return r.json();
}

export async function fetchSummary(params = "") {
  const r = await fetch(`${API_BASE}/stats/summary${params ? `?${params}` : ""}`);
    if (!r.ok) throw new Error("/summary failed");
    return r.json();
}

export async function fetchWatchLog(): Promise<WatchLogEntry[]> {
  const r = await fetch(`${API_BASE}/watchlog`);
    if (!r.ok) throw new Error("/watchlog failed");
    return r.json();
}

export async function markWatched(game_id: string): Promise<WatchLogEntry> {
  const r = await fetch(`${API_BASE}/watchlog`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ game_id }),
  });
  if (!r.ok) throw new Error("/watchlog failed");
  return r.json();
}

export async function markUnwatched(game_id: string): Promise<{ removed: number }> {
  const r = await fetch(`${API_BASE}/watchlog/${game_id}`, {
    method: "DELETE",
  });
  if (!r.ok) throw new Error("/watchlog failed");
  return r.json();
}
