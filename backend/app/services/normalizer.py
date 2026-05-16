from datetime import UTC, datetime
from typing import Any

from app.services.odds_math import american_to_implied_probability


def normalize_odds_api_snapshot(payload: dict[str, Any], snapshot_time: datetime | None = None) -> list[dict[str, Any]]:
    """Flatten an Odds API style payload into rows ready for odds_snapshots."""
    observed_at = snapshot_time or datetime.now(UTC)
    games = payload.get("games", payload if isinstance(payload, list) else [])
    rows: list[dict[str, Any]] = []

    for game in games:
        game_id = game.get("id")
        for bookmaker in game.get("bookmakers", []):
            sportsbook_key = bookmaker.get("key")
            sportsbook_title = bookmaker.get("title", sportsbook_key)
            for market in bookmaker.get("markets", []):
                market_type = market.get("key")
                for outcome in market.get("outcomes", []):
                    odds = outcome.get("price")
                    if odds is None:
                        continue

                    rows.append(
                        {
                            "external_game_id": game_id,
                            "sport_key": game.get("sport_key"),
                            "home_team": game.get("home_team"),
                            "away_team": game.get("away_team"),
                            "commence_time": game.get("commence_time"),
                            "sportsbook_key": sportsbook_key,
                            "sportsbook_title": sportsbook_title,
                            "market_type": market_type,
                            "selection": outcome.get("name"),
                            "line": outcome.get("point"),
                            "odds_american": odds,
                            "implied_probability": american_to_implied_probability(int(odds)),
                            "snapshot_time": observed_at,
                            "raw_payload": outcome,
                        }
                    )

    return rows
