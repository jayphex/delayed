export const API_BASE = "http://localhost:8000";

export async function fetchGames(params = "") {
  const r = await fetch(`${API_BASE}/games${params ? `?${params}` : ""}`);
  if (!r.ok) throw new Error("/games failed");
  return r.json();
}

export async function fetchSummary() {
    const r = await fetch(`${API_BASE}/stats/summary`)
    if (!r.ok) throw new Error("/summary failed");
    return r.json();
}

export async function markWatched(game_id: string) {
  const r = await fetch(`${API_BASE}/watchlog`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ game_id }),
  });
  if (!r.ok) throw new Error("/watchlog failed");
  return r.json();
}
