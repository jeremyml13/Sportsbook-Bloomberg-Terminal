from datetime import datetime
from enum import Enum
from uuid import UUID as PyUUID
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class MarketType(str, Enum):
    spread = "spread"
    moneyline = "moneyline"
    total = "total"


class SignalType(str, Enum):
    high_volatility = "high_volatility"
    sharp_movement = "sharp_movement"
    reverse_line_movement = "reverse_line_movement"
    book_disagreement = "book_disagreement"
    best_number_gone = "best_number_gone"


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    abbreviation: Mapped[str | None] = mapped_column(String(12))
    sport_key: Mapped[str] = mapped_column(String(80), nullable=False, index=True)

    home_games: Mapped[list["Game"]] = relationship(back_populates="home_team", foreign_keys="Game.home_team_id")
    away_games: Mapped[list["Game"]] = relationship(back_populates="away_team", foreign_keys="Game.away_team_id")


class Game(Base):
    __tablename__ = "games"

    id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    external_id: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    sport_key: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    commence_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    home_team_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    away_team_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="scheduled", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    home_team: Mapped[Team] = relationship(back_populates="home_games", foreign_keys=[home_team_id])
    away_team: Mapped[Team] = relationship(back_populates="away_games", foreign_keys=[away_team_id])
    odds_snapshots: Mapped[list["OddsSnapshot"]] = relationship(back_populates="game")
    market_signals: Mapped[list["MarketSignal"]] = relationship(back_populates="game")


class Sportsbook(Base):
    __tablename__ = "sportsbooks"

    id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    key: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    region: Mapped[str | None] = mapped_column(String(20))

    odds_snapshots: Mapped[list["OddsSnapshot"]] = relationship(back_populates="sportsbook")


class OddsSnapshot(Base):
    __tablename__ = "odds_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "game_id",
            "sportsbook_id",
            "market_type",
            "selection",
            "snapshot_time",
            name="uq_odds_snapshot_market_selection_time",
        ),
    )

    id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    game_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("games.id"), nullable=False, index=True)
    sportsbook_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sportsbooks.id"), nullable=False, index=True)
    market_type: Mapped[MarketType] = mapped_column(String(20), nullable=False, index=True)
    selection: Mapped[str] = mapped_column(String(120), nullable=False)
    line: Mapped[float | None] = mapped_column(Float)
    odds_american: Mapped[int] = mapped_column(Integer, nullable=False)
    implied_probability: Mapped[float] = mapped_column(Float, nullable=False)
    snapshot_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(40), default="mock", nullable=False)
    raw_payload: Mapped[dict | None] = mapped_column(JSONB)

    game: Mapped[Game] = relationship(back_populates="odds_snapshots")
    sportsbook: Mapped[Sportsbook] = relationship(back_populates="odds_snapshots")


class MarketSignal(Base):
    __tablename__ = "market_signals"

    id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    game_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("games.id"), nullable=False, index=True)
    signal_type: Mapped[SignalType] = mapped_column(String(40), nullable=False, index=True)
    market_type: Mapped[MarketType] = mapped_column(String(20), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="info", nullable=False)
    message: Mapped[str] = mapped_column(String(240), nullable=False)
    value: Mapped[float | None] = mapped_column(Float)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    game: Mapped[Game] = relationship(back_populates="market_signals")


class PlayerInjury(Base):
    __tablename__ = "player_injuries"
    __table_args__ = (
        UniqueConstraint("external_player_id", "team", "injury_status", name="uq_player_injury_status"),
    )

    id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    external_player_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    sport_key: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    first_name: Mapped[str | None] = mapped_column(String(80))
    last_name: Mapped[str | None] = mapped_column(String(80))
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    team: Mapped[str | None] = mapped_column(String(12), index=True)
    team_id: Mapped[int | None] = mapped_column(Integer)
    position: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[str | None] = mapped_column(String(40))
    injury_status: Mapped[str | None] = mapped_column(String(80), index=True)
    injury_body_part: Mapped[str | None] = mapped_column(String(80))
    injury_start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    injury_notes: Mapped[str | None] = mapped_column(Text)
    upcoming_game_external_id: Mapped[str | None] = mapped_column(String(80), index=True)
    source: Mapped[str] = mapped_column(String(40), default="sportsdataio", nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    raw_payload: Mapped[dict | None] = mapped_column(JSONB)


class PlayerInjuryEvent(Base):
    __tablename__ = "player_injury_events"

    id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    external_player_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    sport_key: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    team: Mapped[str | None] = mapped_column(String(12), index=True)
    position: Mapped[str | None] = mapped_column(String(20))
    event_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    previous_status: Mapped[str | None] = mapped_column(String(80))
    current_status: Mapped[str | None] = mapped_column(String(80))
    previous_body_part: Mapped[str | None] = mapped_column(String(80))
    current_body_part: Mapped[str | None] = mapped_column(String(80))
    previous_notes: Mapped[str | None] = mapped_column(Text)
    current_notes: Mapped[str | None] = mapped_column(Text)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    raw_payload: Mapped[dict | None] = mapped_column(JSONB)


class PlayerNews(Base):
    __tablename__ = "player_news"

    id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    external_news_id: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    sport_key: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    content: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String(120))
    url: Mapped[str | None] = mapped_column(String(500))
    original_source: Mapped[str | None] = mapped_column(String(120))
    original_source_url: Mapped[str | None] = mapped_column(String(500))
    team: Mapped[str | None] = mapped_column(String(12), index=True)
    team2: Mapped[str | None] = mapped_column(String(12), index=True)
    team_id: Mapped[int | None] = mapped_column(Integer)
    team_id2: Mapped[int | None] = mapped_column(Integer)
    external_player_id: Mapped[str | None] = mapped_column(String(80), index=True)
    external_player_id2: Mapped[str | None] = mapped_column(String(80), index=True)
    categories: Mapped[str | None] = mapped_column(String(240))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    source_time_ago: Mapped[str | None] = mapped_column(String(80))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    raw_payload: Mapped[dict | None] = mapped_column(JSONB)
