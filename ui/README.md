# Agent Eval UI

Local Next.js UI on top of `evals.db`. Read-mostly; the Golden Dataset screens are editable.

## Run

```bash
cd ui
npm install
npm run dev   # http://localhost:3030
```

`evals.db` is opened from the repo root (`../evals.db`). The app must run from the `ui/` directory.

## Layout

- `/` — overview
- `/golden` — fixed outputs + gold labels (editable)
- `/cases` — cases + criteria (editable)
- `/judges` — judge health (P/R/F1) — placeholder until the next slot

## Stack

- Next.js 15 App Router + React 19
- `better-sqlite3` reads `../evals.db` directly
- Server Actions handle writes; no API routes
- Tailwind for styling
