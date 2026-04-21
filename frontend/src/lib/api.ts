import { Game, Summary, WatchLogEntry } from "./types";

const configuredBase = process.env.NEXT_PUBLIC_API_BASE?.replace(/\/$/, "");

if (!configuredBase) {
  throw new Error("NEXT_PUBLIC_API_BASE is required for the frontend.");
}

export const API_BASE = configuredBase;

async function readJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `${path} failed`);
  }

  return response.json() as Promise<T>;
}

export async function fetchGames(params = ""): Promise<Game[]> {
  return readJson<Game[]>(`/games${params ? `?${params}` : ""}`);
}

export async function fetchSummary(params = ""): Promise<Summary> {
  return readJson<Summary>(`/stats/summary${params ? `?${params}` : ""}`);
}

export async function fetchWatchLog(): Promise<WatchLogEntry[]> {
  return readJson<WatchLogEntry[]>("/watchlog");
}

export async function markWatched(game_id: string): Promise<WatchLogEntry> {
  return readJson<WatchLogEntry>("/watchlog", {
    method: "POST",
    body: JSON.stringify({ game_id }),
  });
}

export async function markUnwatched(game_id: string): Promise<{ removed: number }> {
  return readJson<{ removed: number }>(`/watchlog/${game_id}`, {
    method: "DELETE",
  });
}
