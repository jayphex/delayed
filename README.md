# Delayed

Delayed is an NBA tip-off delay tracker designed to run as a fully hosted Vercel
application. Users should only ever interact with the deployed site and API.

## Production architecture

- `frontend/`: Next.js dashboard deployed as a Vercel project
- `api/`: FastAPI backend deployed as a separate Vercel project
- Postgres: durable storage for games and watch-log data
- Vercel Cron: scheduled syncs that refresh game data inside the API project

There is no shared local-file storage in the production design. That matters
because Vercel Functions are serverless and do not provide a durable shared
filesystem for application state.

## How it should work for real users

1. A user visits the frontend on Vercel.
2. The frontend calls the deployed FastAPI backend on Vercel.
3. The backend reads and writes durable data in Postgres.
4. Vercel Cron hits `/internal/sync-games` on a schedule to keep game data fresh.

Nobody using the app should need to run scripts or services on their laptop.

## Vercel setup

Create two Vercel projects from this same repository:

1. Frontend project
   Root Directory: `frontend`

2. API project
   Root Directory: `api`

Vercel monorepo docs:
https://vercel.com/docs/monorepos

FastAPI on Vercel:
https://vercel.com/docs/frameworks/backend/fastapi

## Required environment variables

### API project

Set these in the Vercel dashboard for the `api` project:

- `DATABASE_URL`
- `CORS_ORIGINS`
- `CRON_SECRET` (recommended)
- `DEFAULT_USER_ID` (optional)
- `AUTO_SYNC_ON_EMPTY=true` (recommended)

Example values are shown in [api/.env.example](/Users/johnmuhigi/Desktop/projects/delayed/api/.env.example).

### Frontend project

Set this in the Vercel dashboard for the `frontend` project:

- `NEXT_PUBLIC_API_BASE=https://your-api-project.vercel.app`

Example:
[frontend/.env.example](/Users/johnmuhigi/Desktop/projects/delayed/frontend/.env.example)

## Database

Use a hosted Postgres database for production. The cleanest option is attaching
Postgres from the Vercel Marketplace, though any hosted Postgres provider works
as long as it gives you a standard connection string for `DATABASE_URL`.

Vercel storage overview:
https://vercel.com/docs/storage

Why local persistence is not appropriate on Vercel:
https://vercel.com/guides/is-sqlite-supported-in-vercel

## Cron syncing

The API project includes [api/vercel.json](/Users/johnmuhigi/Desktop/projects/delayed/api/vercel.json),
which schedules `/internal/sync-games`.

If `CRON_SECRET` is set, Vercel will automatically send it as a Bearer token to
the cron endpoint.

The API also supports `AUTO_SYNC_ON_EMPTY=true`, which lets the first request
for a date trigger a one-time sync if the database does not yet have games for
that date. This helps new deployments avoid showing an empty board before cron
has had a chance to run.

Cron docs:
https://vercel.com/docs/cron-jobs
https://vercel.com/docs/cron-jobs/manage-cron-jobs

## Important note

This repo is now configured around hosted deployment. The frontend expects
`NEXT_PUBLIC_API_BASE`, and the API expects `DATABASE_URL`. If those are missing,
the projects should fail fast rather than silently fall back to local state.

## Practical Vercel rollout order

1. Push the latest repo changes to GitHub.
2. Create the `api` Vercel project with root directory `api`.
3. Attach Postgres to the `api` project and set:
   `DATABASE_URL`, `CORS_ORIGINS`, `CRON_SECRET`, `AUTO_SYNC_ON_EMPTY=true`
4. Deploy the `api` project and confirm `/health` responds successfully.
5. Create the `frontend` Vercel project with root directory `frontend`.
6. Set `NEXT_PUBLIC_API_BASE` to the deployed API URL.
7. Deploy the `frontend` project.
8. Open the site and verify the board loads. If cron has not run yet, the first
   request should trigger the empty-date bootstrap sync.
