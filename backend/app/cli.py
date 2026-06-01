import argparse
from datetime import date

from app.db.repository import persist_normalized_odds, persist_player_context
from app.db.session import SessionLocal
from app.services.normalizer import (
    normalize_odds_api_snapshot,
    normalize_sportsdataio_mlb_game_odds,
    normalize_sportsdataio_mlb_injuries,
    normalize_sportsdataio_mlb_news,
)
from app.services.odds_api import fetch_mlb_odds
from app.services.seed_mock import seed_mock_data
from app.services.sportsdataio import fetch_mlb_game_odds_by_date, fetch_mlb_injured_players, fetch_mlb_news


def seed_mock() -> None:
    with SessionLocal() as db:
        counts = seed_mock_data(db)

    print("Seeded mock data: " + ", ".join(f"{name}={count}" for name, count in counts.items()))


def ingest_mlb_odds(game_date: date) -> None:
    payload = fetch_mlb_game_odds_by_date(game_date)
    rows = normalize_sportsdataio_mlb_game_odds(payload)
    with SessionLocal() as db:
        counts = persist_normalized_odds(db, rows)

    games_seen = len({row["external_game_id"] for row in rows})
    print(
        f"Ingested SportsDataIO MLB odds for {game_date.isoformat()}: "
        f"games_seen={games_seen}, "
        + ", ".join(f"{name}={count}" for name, count in counts.items())
    )


def ingest_mlb_context() -> None:
    injury_payload = fetch_mlb_injured_players()
    news_payload = fetch_mlb_news()
    injury_rows = normalize_sportsdataio_mlb_injuries(injury_payload)
    news_rows = normalize_sportsdataio_mlb_news(news_payload)
    with SessionLocal() as db:
        counts = persist_player_context(db, injury_rows, news_rows)

    print(
        "Ingested SportsDataIO MLB player context: "
        f"injuries_seen={len(injury_rows)}, injuries_created={counts['injuries']}, "
        f"news_seen={len(news_rows)}, news_created={counts['news']}"
    )


def ingest_odds_api_mlb() -> None:
    response = fetch_mlb_odds()
    rows = normalize_odds_api_snapshot(response.payload)
    with SessionLocal() as db:
        counts = persist_normalized_odds(db, rows)

    games_seen = len({row["external_game_id"] for row in rows})
    print(
        "Ingested The Odds API MLB odds: "
        f"games_seen={games_seen}, "
        + ", ".join(f"{name}={count}" for name, count in counts.items())
    )
    print(
        "The Odds API usage: "
        f"last={response.usage.requests_last}, "
        f"used={response.usage.requests_used}, "
        f"remaining={response.usage.requests_remaining}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Backend maintenance commands.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("seed-mock", help="Load the 5-game NBA mock board into Postgres.")
    ingest_parser = subparsers.add_parser("ingest-mlb-odds", help="Fetch today's MLB odds from SportsDataIO.")
    ingest_parser.add_argument("--date", dest="game_date", type=date.fromisoformat, default=date.today())
    subparsers.add_parser("ingest-mlb-context", help="Fetch MLB injuries and news from SportsDataIO.")
    subparsers.add_parser("ingest-odds-api-mlb", help="Fetch MLB odds from The Odds API.")
    args = parser.parse_args()

    if args.command == "seed-mock":
        seed_mock()
    elif args.command == "ingest-mlb-odds":
        ingest_mlb_odds(args.game_date)
    elif args.command == "ingest-mlb-context":
        ingest_mlb_context()
    elif args.command == "ingest-odds-api-mlb":
        ingest_odds_api_mlb()


if __name__ == "__main__":
    main()
