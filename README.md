# Delayed

Delayed is a small NBA tip-off tracker. It compares each game's scheduled start
time with the observed tip-off time, then lets you mark which games you watched
so you can see how many minutes you have lost waiting for late starts.

The idea is simple: NBA games often start later than the listed tip time, and
this project is meant to turn that annoyance into real data you can track over
time.

## What works now

- A FastAPI backend that reads game data from `data/games.csv` and falls back to
  `data/sample_games.csv`
- Delay calculations based on `scheduled_start` versus `actual_start`
- A persistent watch log stored in `data/watch_log.json`
- A Next.js dashboard for filtering games and tracking total wasted time
- A polling script that can write live scoreboard data back into `data/games.csv`

## Project layout

- `api/app/main.py`: API endpoints for games, summary stats, and watched games
- `frontend/src/app/page.tsx`: dashboard UI
- `scripts/poll_games.py`: scoreboard poller
- `data/sample_games.csv`: starter dataset

## Run it locally

### Backend

Install the Python requirements in your environment, then run:

```bash
uvicorn api.app.main:app --reload
```

The API serves:

- `GET /games`
- `GET /stats/summary`
- `GET /watchlog`
- `POST /watchlog`
- `DELETE /watchlog/{game_id}`

### Frontend

From `frontend/`:

```bash
npm install
NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000 npm run dev
```

### Poll live games

Once `nba_api` is installed, you can populate `data/games.csv` with:

```bash
python3 scripts/poll_games.py --once
```

Or keep it running:

```bash
python3 scripts/poll_games.py --interval 60
```

The poller records the first observed live state as the game's `actual_start`,
which makes the measured delay accurate to within the polling interval.
