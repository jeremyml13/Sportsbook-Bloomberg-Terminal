# Sports Betting Market Terminal

A market intelligence MVP for tracking sports betting market movement over time. This is intentionally not a picks or prediction app.

## Structure

- `backend/` FastAPI service with database models, route stubs, mock market data, and ingestion normalization scaffolding.
- `frontend/` React + Vite + TypeScript dashboard using Tailwind CSS and Recharts.

## Local Setup

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

### Database

```bash
docker compose up -d postgres
cd backend
source .venv/bin/activate
alembic upgrade head
python -m app.cli seed-mock
```

The app falls back to in-memory mock data if Postgres is not running. Once the database is migrated and seeded, the API reads the 5-game NBA board, snapshots, history, and signals from Postgres.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The app will be available at the Vite URL shown in your terminal.

## MVP API

- `GET /games/today`
- `GET /games/{game_id}`
- `GET /games/{game_id}/odds-history`
- `GET /games/{game_id}/signals`
- `POST /ingest/odds`

All routes currently use mock data or route stubs. Real Odds API integration is intentionally deferred.
