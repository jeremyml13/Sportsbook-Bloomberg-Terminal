from datetime import UTC, datetime
from typing import Any

from app.services.odds_math import american_to_implied_probability


def normalize_odds_api_snapshot(payload: dict[str, Any], snapshot_time: datetime | None = None) -> list[dict[str, Any]]:
    """Flatten an Odds API style payload into rows ready for odds_snapshots."""
    observed_at = snapshot_time or datetime.now(UTC)
    games = payload if isinstance(payload, list) else payload.get("games", [])
    rows: list[dict[str, Any]] = []

    for game in games:
        game_id = game.get("id")
        home_team = game.get("home_team")
        away_team = game.get("away_team")
        if not game_id or not home_team or not away_team:
            continue

        for bookmaker in game.get("bookmakers", []):
            sportsbook_key = bookmaker.get("key")
            sportsbook_title = bookmaker.get("title", sportsbook_key)
            for market in bookmaker.get("markets", []):
                market_type = _odds_api_market_type(market.get("key"))
                if market_type is None:
                    continue

                for outcome in market.get("outcomes", []):
                    odds = outcome.get("price")
                    if odds is None:
                        continue

                    rows.append(
                        {
                            "external_game_id": f"oddsapi-mlb-{game_id}",
                            "sport_key": game.get("sport_key"),
                            "home_team": home_team,
                            "away_team": away_team,
                            "commence_time": _parse_datetime(game.get("commence_time")) or observed_at,
                            "status": "scheduled",
                            "sportsbook_key": sportsbook_key,
                            "sportsbook_title": sportsbook_title,
                            "market_type": market_type,
                            "selection": outcome.get("name"),
                            "line": outcome.get("point"),
                            "odds_american": odds,
                            "implied_probability": american_to_implied_probability(int(odds)),
                            "snapshot_time": observed_at,
                            "source": "the_odds_api",
                            "raw_payload": outcome,
                        }
                    )

    return rows


def _odds_api_market_type(value: str | None) -> str | None:
    if value == "h2h":
        return "moneyline"
    if value in {"spreads", "spread"}:
        return "spread"
    if value in {"totals", "total"}:
        return "total"

    return None


def normalize_sportsdataio_mlb_game_odds(
    games: list[dict[str, Any]],
    snapshot_time: datetime | None = None,
) -> list[dict[str, Any]]:
    observed_at = snapshot_time or datetime.now(UTC)
    rows: list[dict[str, Any]] = []

    for game in games:
        game_id = game.get("GameId")
        home_team = game.get("HomeTeamName")
        away_team = game.get("AwayTeamName")
        if not game_id or not home_team or not away_team:
            continue

        game_base = {
            "external_game_id": f"sportsdataio-mlb-{game_id}",
            "sport_key": "baseball_mlb",
            "home_team": home_team,
            "away_team": away_team,
            "commence_time": _parse_datetime(game.get("DateTime")) or observed_at,
            "status": game.get("Status", "scheduled"),
        }

        for odds in [*(game.get("PregameOdds") or []), *(game.get("LiveOdds") or [])]:
            sportsbook_id = odds.get("SportsbookId")
            sportsbook_title = odds.get("Sportsbook") or f"SportsDataIO {sportsbook_id}"
            sportsbook_key = f"sportsdataio_{sportsbook_id}" if sportsbook_id else _slugify(sportsbook_title)
            odds_snapshot_time = _parse_datetime(odds.get("Updated")) or _parse_datetime(odds.get("Created")) or observed_at
            source = f"sportsdataio_{odds.get('OddType') or 'mlb'}"

            _append_line(
                rows,
                game_base,
                odds,
                sportsbook_key,
                sportsbook_title,
                "moneyline",
                away_team,
                None,
                odds.get("AwayMoneyLine"),
                odds_snapshot_time,
                source,
            )
            _append_line(
                rows,
                game_base,
                odds,
                sportsbook_key,
                sportsbook_title,
                "moneyline",
                home_team,
                None,
                odds.get("HomeMoneyLine"),
                odds_snapshot_time,
                source,
            )
            _append_line(
                rows,
                game_base,
                odds,
                sportsbook_key,
                sportsbook_title,
                "spread",
                away_team,
                odds.get("AwayPointSpread"),
                odds.get("AwayPointSpreadPayout"),
                odds_snapshot_time,
                source,
            )
            _append_line(
                rows,
                game_base,
                odds,
                sportsbook_key,
                sportsbook_title,
                "spread",
                home_team,
                odds.get("HomePointSpread"),
                odds.get("HomePointSpreadPayout"),
                odds_snapshot_time,
                source,
            )
            _append_line(
                rows,
                game_base,
                odds,
                sportsbook_key,
                sportsbook_title,
                "total",
                "Over",
                odds.get("OverUnder"),
                odds.get("OverPayout"),
                odds_snapshot_time,
                source,
            )
            _append_line(
                rows,
                game_base,
                odds,
                sportsbook_key,
                sportsbook_title,
                "total",
                "Under",
                odds.get("OverUnder"),
                odds.get("UnderPayout"),
                odds_snapshot_time,
                source,
            )

    return rows


def normalize_sportsdataio_mlb_injuries(
    players: list[dict[str, Any]],
    observed_at: datetime | None = None,
) -> list[dict[str, Any]]:
    seen_at = observed_at or datetime.now(UTC)
    rows: list[dict[str, Any]] = []

    for player in players:
        player_id = player.get("PlayerID")
        first_name = player.get("FirstName")
        last_name = player.get("LastName")
        if not player_id:
            continue

        rows.append(
            {
                "external_player_id": str(player_id),
                "sport_key": "baseball_mlb",
                "first_name": first_name,
                "last_name": last_name,
                "display_name": " ".join(part for part in [first_name, last_name] if part) or str(player_id),
                "team": player.get("Team"),
                "team_id": player.get("TeamID"),
                "position": player.get("Position"),
                "status": player.get("Status"),
                "injury_status": player.get("InjuryStatus"),
                "injury_body_part": player.get("InjuryBodyPart"),
                "injury_start_date": _parse_datetime(player.get("InjuryStartDate")),
                "injury_notes": player.get("InjuryNotes"),
                "upcoming_game_external_id": _string_or_none(player.get("UpcomingGameID")),
                "source": "sportsdataio",
                "observed_at": seen_at,
                "raw_payload": player,
            }
        )

    return rows


def normalize_sportsdataio_mlb_news(
    news_items: list[dict[str, Any]],
    observed_at: datetime | None = None,
) -> list[dict[str, Any]]:
    seen_at = observed_at or datetime.now(UTC)
    rows: list[dict[str, Any]] = []

    for item in news_items:
        news_id = item.get("NewsID")
        title = item.get("Title")
        if not news_id or not title:
            continue

        rows.append(
            {
                "external_news_id": str(news_id),
                "sport_key": "baseball_mlb",
                "title": title,
                "content": item.get("Content"),
                "source": item.get("Source"),
                "url": item.get("Url"),
                "original_source": item.get("OriginalSource"),
                "original_source_url": item.get("OriginalSourceUrl"),
                "team": item.get("Team"),
                "team2": item.get("Team2"),
                "team_id": item.get("TeamID"),
                "team_id2": item.get("TeamID2"),
                "external_player_id": _string_or_none(item.get("PlayerID")),
                "external_player_id2": _string_or_none(item.get("PlayerID2")),
                "categories": item.get("Categories"),
                "updated_at": _parse_datetime(item.get("Updated")),
                "source_time_ago": item.get("TimeAgo"),
                "observed_at": seen_at,
                "raw_payload": item,
            }
        )

    return rows


def _append_line(
    rows: list[dict[str, Any]],
    game_base: dict[str, Any],
    raw_payload: dict[str, Any],
    sportsbook_key: str,
    sportsbook_title: str,
    market_type: str,
    selection: str,
    line: Any,
    odds: Any,
    snapshot_time: datetime,
    source: str,
) -> None:
    if odds is None:
        return

    odds_american = int(odds)
    rows.append(
        {
            **game_base,
            "sportsbook_key": sportsbook_key,
            "sportsbook_title": sportsbook_title,
            "market_type": market_type,
            "selection": selection,
            "line": float(line) if line is not None else None,
            "odds_american": odds_american,
            "implied_probability": american_to_implied_probability(odds_american),
            "snapshot_time": snapshot_time,
            "source": source,
            "raw_payload": raw_payload,
        }
    )


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None

    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)

    return parsed


def _slugify(value: str) -> str:
    return value.lower().replace(" ", "_")


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None

    return str(value)
