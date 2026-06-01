from datetime import date
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json

from app.core.config import settings


class SportsDataIOError(RuntimeError):
    pass


def fetch_mlb_game_odds_by_date(game_date: date) -> list[dict[str, Any]]:
    """Fetch MLB game odds that include pregame odds and live odds when available."""
    return _get_json(f"/mlb/odds/json/GameOddsByDate/{game_date.isoformat()}")


def fetch_mlb_live_game_odds_by_date(game_date: date) -> list[dict[str, Any]]:
    """Fetch MLB in-game odds. This only has odds while games are in progress."""
    return _get_json(f"/mlb/odds/json/LiveGameOddsByDate/{game_date.isoformat()}")


def fetch_mlb_injured_players() -> list[dict[str, Any]]:
    return _get_json("/mlb/projections/json/InjuredPlayers")


def fetch_mlb_news() -> list[dict[str, Any]]:
    return _get_json("/mlb/scores/json/News")


def _get_json(path: str) -> list[dict[str, Any]]:
    if not settings.sportsdataio_api_key:
        raise SportsDataIOError("SPORTSDATAIO_API_KEY is not configured.")

    url = f"{settings.sportsdataio_base_url}{path}?{urlencode({'key': settings.sportsdataio_api_key})}"
    request = Request(url, headers={"Accept": "application/json"})

    with urlopen(request, timeout=20) as response:
        payload = json.load(response)

    if not isinstance(payload, list):
        raise SportsDataIOError("SportsDataIO returned an unexpected response shape.")

    return payload
