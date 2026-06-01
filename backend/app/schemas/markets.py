from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


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


class BestPriceRead(BaseModel):
    market_type: str
    selection: str
    sportsbook: str
    line: float | None = None
    odds_american: int
    implied_probability: float


class NoVigProbabilityRead(BaseModel):
    selection: str
    fair_probability: float
    best_sportsbook: str | None = None
    best_odds_american: int | None = None


class PriceAlertRead(BaseModel):
    market_type: str
    selection: str
    sportsbook: str
    line: float | None = None
    odds_american: int
    edge_to_market: float
    message: str


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


class MovementAlertRead(BaseModel):
    sportsbook: str
    market_type: str
    selection: str
    opening_line: float | None = None
    current_line: float | None = None
    line_delta: float | None = None
    opening_odds_american: int
    current_odds_american: int
    odds_delta: int
    first_seen: datetime
    last_seen: datetime
    message: str


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
    opportunity_score: float = 0.0
    opportunity_reasons: list[str] = Field(default_factory=list)
    best_prices: list[BestPriceRead] = Field(default_factory=list)
    no_vig_moneyline: list[NoVigProbabilityRead] = Field(default_factory=list)
    price_alerts: list[PriceAlertRead] = Field(default_factory=list)


class GameDetail(GameSummary):
    odds_history: list[OddsHistoryPoint]
    book_table: list[OddsLine]
    movement_alerts: list[MovementAlertRead] = Field(default_factory=list)


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


class PlayerInjuryRead(BaseModel):
    external_player_id: str
    display_name: str
    team: str | None = None
    position: str | None = None
    status: str | None = None
    injury_status: str | None = None
    injury_body_part: str | None = None
    injury_start_date: datetime | None = None
    injury_notes: str | None = None
    upcoming_game_external_id: str | None = None
    observed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PlayerNewsRead(BaseModel):
    external_news_id: str
    title: str
    content: str | None = None
    source: str | None = None
    url: str | None = None
    original_source: str | None = None
    original_source_url: str | None = None
    team: str | None = None
    team2: str | None = None
    external_player_id: str | None = None
    external_player_id2: str | None = None
    categories: str | None = None
    updated_at: datetime | None = None
    source_time_ago: str | None = None
    observed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PlayerInjuryEventRead(BaseModel):
    external_player_id: str
    display_name: str
    team: str | None = None
    position: str | None = None
    event_type: str
    previous_status: str | None = None
    current_status: str | None = None
    previous_body_part: str | None = None
    current_body_part: str | None = None
    previous_notes: str | None = None
    current_notes: str | None = None
    detected_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IngestPlayerContextResponse(BaseModel):
    accepted: bool
    source: str
    injuries_seen: int
    injuries_upserted: int
    news_seen: int
    news_upserted: int
    message: str


class GamePlayerContextRead(BaseModel):
    game_id: str
    teams: list[str]
    injuries: list[PlayerInjuryRead]
    injury_events: list[PlayerInjuryEventRead]
    news: list[PlayerNewsRead]
