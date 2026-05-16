from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class TeamRead(BaseModel):
    id: str
    name: str
    abbreviation: str | None = None


class OddsLine(BaseModel):
    sportsbook: str
    selection: str
    market_type: str
    line: float | None = None
    odds_american: int
    implied_probability: float
    snapshot_time: datetime


class CurrentMarkets(BaseModel):
    spread: list[OddsLine]
    moneyline: list[OddsLine]
    total: list[OddsLine]


class MarketSignalRead(BaseModel):
    signal_type: str
    market_type: str
    severity: str
    message: str
    value: float | None = None
    detected_at: datetime


class OddsHistoryPoint(BaseModel):
    timestamp: datetime
    sportsbook: str
    market_type: str
    selection: str
    line: float | None = None
    odds_american: int


class GameSummary(BaseModel):
    id: str
    sport_key: str
    commence_time: datetime
    home_team: TeamRead
    away_team: TeamRead
    current_markets: CurrentMarkets
    opening_markets: CurrentMarkets | None = None
    signals: list[MarketSignalRead]
    volatility_score: float
    book_disagreement_score: float


class GameDetail(GameSummary):
    odds_history: list[OddsHistoryPoint]
    book_table: list[OddsLine]


class IngestOddsRequest(BaseModel):
    source: str = "mock"
    snapshot_time: datetime | None = None
    payload: dict[str, Any]


class IngestOddsResponse(BaseModel):
    accepted: bool
    source: str
    games_seen: int
    snapshots_normalized: int
    message: str

    model_config = ConfigDict(extra="forbid")
