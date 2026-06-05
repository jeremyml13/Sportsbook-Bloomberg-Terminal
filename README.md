# Sports Market Terminal

Sports Market Terminal is a Bloomberg-style market intelligence dashboard for sports betting markets. It is intentionally **not** a picks app or prediction engine. The goal is to help a user understand market movement, sportsbook disagreement, stale prices, injury/news context, and saved betting ideas in one workflow.

For a fuller explanation of the product features, see [docs/demo_feature_guide.md](docs/demo_feature_guide.md).

## Problem & Insight

Sports bettors often have to jump between multiple sportsbooks, odds screens, injury reports, notes, and spreadsheets. The core problem is not only getting odds; it is interpreting which games deserve attention and why.

This project addresses that problem by combining:

- a multi-sport market board
- sportsbook price comparison
- stored odds snapshots and line movement charts
- market regime tags and opportunity scores
- no-vig probabilities and EV tools
- a bet idea notebook and CLV tracking
- injury/news context
- an AI Copilot that explains the current market context

The main insight is that a useful betting terminal should support the user's reasoning workflow, not simply display prices.

## Execution & Technical Work

This is a full-stack application.

- `frontend/`: React + Vite + TypeScript dashboard using Tailwind CSS, Recharts, and lucide icons.
- `backend/`: FastAPI service with SQLAlchemy models, Alembic migrations, ingestion routes, market summarization, and AI chat orchestration.
- Database: PostgreSQL, currently used with Supabase in deployment.
- External data integrations: The Odds API for live MLB odds and SportsDataIO for MLB injuries/news context.
- AI integration: DigitalOcean inference powers the Market Copilot.

Implemented features include:

- Demo Mode and Live Mode separation.
- NBA, MLB, and NFL demo boards.
- Stored mock odds data with 13 demo games and 1,040 odds snapshots.
- Line movement charts for spread, moneyline, and total.
- Sportsbook matrix with best-price highlighting.
- Opportunity scoring from price alerts, volatility, disagreement, and warning signals.
- Bet Idea Notebook with EV and quarter-Kelly calculations.
- CLV tracking that compares saved prices against the latest market.
- Market Copilot that uses selected sport and Demo/Live context.
- Live MLB odds refresh and separate injuries/news refresh.

## Evaluation & Evidence

The project was evaluated around whether it supports the intended market workflow end-to-end:

1. Scan a sports board.
2. Identify games with unusual market behavior.
3. Open a game detail page.
4. Inspect line movement across books.
5. Compare best available prices.
6. Estimate EV from a user probability.
7. Save a bet idea.
8. Track CLV against later market prices.
9. Ask Copilot for a market explanation.

As early user validation, I asked sports bettors what they would want in a platform like this. The common themes were:

- a way to track their bets or betting ideas
- help identifying potential postive EV opportunities
- tools for tracking CLV, or Closing Line Value, after a bet idea is saved

Those responses directly shaped the Bet Idea Notebook, opportunity scoring, and CLV Tracking views.

Demo Mode exists so the artifact is reproducible and understandable even when live API data is sparse or API credits are limited. Live Mode is separated from Demo Mode so users do not accidentally overwrite the polished demo workflow with incomplete live data.

Known limitations:

- Live line movement becomes more useful only after multiple live refreshes over time.
- Live data currently focuses on MLB odds.
- Injury/news refresh uses SportsDataIO separately from odds refresh.
- The AI Copilot explains market context but should not be treated as betting advice.
- Saved bet ideas currently use browser local storage rather than account-based persistence.
- Live data must be manually refreshed by the user due to API constraints - it would be better if there was an automatic scheduler that got the odds at a set interval (e.g. 5 minutes)


## Process, Integrity & Disclosure

I used AI assistance during development for coding support, debugging, deployment guidance, and documentation. I reviewed and integrated the code and product decisions myself.

The product itself also includes an AI Copilot powered by DigitalOcean inference. The Copilot is meant to explain the market context provided by the app. It does not guarantee profitable bets.

This project uses external APIs and services:

- The Odds API for live odds.
- SportsDataIO for injuries/news context.
- Supabase/PostgreSQL for deployed data storage.
- DigitalOcean inference for LLM responses.
- Vercel for deployment.

## Local Setup

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

### Environment Variables

Create `backend/.env` locally.

Required for full functionality:

```env
DATABASE_URL=postgresql+psycopg://...
SPORTSDATAIO_API_KEY=...
ODDS_API_KEY=...
DO_MODEL_ACCESS_KEY=...
DO_INFERENCE_BASE_URL=https://inference.do-ai.run
DO_INFERENCE_MODEL=openai-gpt-oss-20b
```

### Database

For local Docker Postgres:

```bash
docker compose up -d postgres
cd backend
source .venv/bin/activate
alembic upgrade head
python -m app.cli seed-mock
```

For Supabase/Postgres, set `DATABASE_URL` to the Supabase pooler URL, run migrations, and seed demo data:

```bash
cd backend
source .venv/bin/activate
alembic upgrade head
python -m app.cli seed-mock
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The app will be available at the Vite URL shown in your terminal, usually:

```text
http://localhost:5173
```

## Data Modes

### Demo Mode

Demo Mode uses stored sample odds. It is the best mode for demos because all sports, charts, signals, sportsbook comparisons, and Copilot workflows are populated.

The button:

```text
Reset Demo Data
```

calls:

```text
POST /ingest/demo/reset
```

### Live Mode

Live Mode uses real MLB odds and API credits.

The button:

```text
Refresh Live MLB Odds
```

calls:

```text
POST /ingest/odds-api/mlb
```

The button:

```text
Refresh Injuries & News
```

calls:

```text
POST /ingest/sportsdataio/mlb-context
```

## API Overview

- `GET /health`
- `GET /games/today?mode=demo`
- `GET /games/today?mode=live`
- `GET /games/meta/odds-freshness?mode=demo`
- `GET /games/{game_id}`
- `GET /games/{game_id}/odds-history`
- `GET /games/{game_id}/signals`
- `GET /context/mlb/injuries`
- `GET /context/mlb/news`
- `GET /context/mlb/games/{game_id}`
- `POST /ingest/demo/reset`
- `POST /ingest/odds-api/mlb`
- `POST /ingest/sportsdataio/mlb-context`
- `POST /chat`

## Deployment Notes

The project is deployed as two Vercel projects from the same monorepo:

- frontend project root: `frontend`
- backend project root: `backend`

The frontend production environment uses:

```env
VITE_API_BASE=https://sportsbook-bloomberg-terminal.vercel.app
```
