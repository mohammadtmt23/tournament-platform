# Tournament Platform

A backend service for running single-elimination tournaments: register players,
generate a seeded bracket (with byes), report results, and track the champion.

## Run it

```bash
docker compose up --build
# App:      http://localhost:3000
# API docs: http://localhost:8000/docs
```

### Develop without Docker

```bash
# terminal 1 - API (SQLite by default)
cd backend && pip install -r requirements-dev.txt && uvicorn app.main:app --reload

# terminal 2 - frontend (proxies /api to localhost:8000)
cd frontend && npm install && npm run dev
# http://localhost:5173
```

## Run the tests

```bash
cd backend
pip install -r requirements-dev.txt
python -m pytest -q
```

## Deploy (Render + Neon)

`render.yaml` is a Render Blueprint for the API (Docker) and the static frontend.
The database is a free [Neon](https://neon.com) Postgres, because Render's free
Postgres expires after 30 days.

1. Create a Neon project and copy its connection string.
2. In Render: **New, Blueprint**, pick this repo, and paste the Neon string as `DATABASE_URL`.
3. When the API is live, set `VITE_API_BASE_URL` on the static site to the API's URL
   and redeploy the site (Vite bakes it in at build time).

Free-tier note: the API sleeps after about 15 minutes idle, so the first request can be slow.

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/tournaments` | Create a tournament |
| POST | `/tournaments/{id}/players` | Register a player |
| POST | `/tournaments/{id}/start` | Seed players and generate the bracket |
| GET | `/tournaments/{id}/bracket` | Current bracket and champion |
| POST | `/tournaments/{id}/matches/{round}/{position}/result` | Report a winner |

## Design notes

- **Bracket engine** (`app/bracket.py`) is pure logic with no database, so it is
  unit tested across every field size from 2 to 32. Standard seeding keeps seeds
  1 and 2 apart until the final, and top seeds get byes when the field is not a
  power of two.
- **API** (`app/main.py`) loads matches from the database into the engine,
  applies a result, and writes back every changed row, so the tested logic is the
  single source of truth.
- **Frontend** (`frontend/`) is React + Vite. The tournament id lives in the URL hash, so any bracket is shareable, and the page polls every 3 seconds so viewers stay in sync.
- **Postgres** in Docker Compose; SQLite is used for tests.

## Roadmap

- [x] React frontend (bracket view, report winners, shareable `#/t/<id>` links, polling)
- [ ] Login and organizer/player roles
- [ ] Live updates (WebSockets)
- [ ] Double elimination
