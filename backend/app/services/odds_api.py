from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json

from app.core.config import settings


class OddsAPIError(RuntimeError):
    pass


@dataclass(frozen=True)
class OddsAPIUsage:
    requests_remaining: str | None
    requests_used: str | None
    requests_last: str | None


@dataclass(frozen=True)
class OddsAPIResponse:
    payload: list[dict[str, Any]]
    usage: OddsAPIUsage


def fetch_mlb_odds() -> OddsAPIResponse:
    params = {
        "apiKey": _api_key(),
        "regions": "us",
        "markets": "h2h,spreads,totals",
        "oddsFormat": "american",
    }
    return _get_json("/sports/baseball_mlb/odds", params)


def _api_key() -> str:
    if not settings.odds_api_key:
        raise OddsAPIError("ODDS_API_KEY is not configured.")

    return settings.odds_api_key


def _get_json(path: str, params: dict[str, str]) -> OddsAPIResponse:
    url = f"{settings.odds_api_base_url}{path}?{urlencode(params)}"
    request = Request(url, headers={"Accept": "application/json"})

    with urlopen(request, timeout=20) as response:
        payload = json.load(response)
        usage = OddsAPIUsage(
            requests_remaining=response.headers.get("x-requests-remaining"),
            requests_used=response.headers.get("x-requests-used"),
            requests_last=response.headers.get("x-requests-last"),
        )

    if not isinstance(payload, list):
        raise OddsAPIError("The Odds API returned an unexpected response shape.")

    return OddsAPIResponse(payload=payload, usage=usage)
