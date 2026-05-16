from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.models import Game, MarketSignal, OddsSnapshot, Team
from app.schemas.markets import (
    CurrentMarkets,
    GameDetail,
    GameSummary,
    MarketSignalRead,
    OddsHistoryPoint,
    OddsLine,
    TeamRead,
)
from app.services.odds_math import calculate_book_disagreement, calculate_volatility


def get_today_game_summaries(db: Session) -> list[GameSummary]:
    start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    games = db.scalars(
        select(Game)
        .where(Game.commence_time >= start, Game.commence_time < end)
        .options(joinedload(Game.home_team), joinedload(Game.away_team))
        .order_by(Game.commence_time)
    ).all()

    return [_build_summary(db, game) for game in games]


def get_game_detail(db: Session, external_id: str) -> GameDetail | None:
    game = db.scalar(
        select(Game)
        .where(Game.external_id == external_id)
        .options(joinedload(Game.home_team), joinedload(Game.away_team))
    )
    if game is None:
        return None

    snapshots = _snapshots_for_game(db, game.id)
    history = [
        OddsHistoryPoint(
            timestamp=snapshot.snapshot_time,
            sportsbook=snapshot.sportsbook.title,
            market_type=snapshot.market_type,
            selection=snapshot.selection,
            line=snapshot.line,
            odds_american=snapshot.odds_american,
        )
        for snapshot in snapshots
    ]
    latest_time = max((snapshot.snapshot_time for snapshot in snapshots), default=None)
    book_table = [_snapshot_to_line(snapshot) for snapshot in snapshots if snapshot.snapshot_time == latest_time]

    return GameDetail(
        **_build_summary(db, game).model_dump(),
        odds_history=history,
        book_table=book_table,
    )


def get_game_odds_history(db: Session, external_id: str) -> list[OddsHistoryPoint] | None:
    detail = get_game_detail(db, external_id)
    return None if detail is None else detail.odds_history


def get_game_signals(db: Session, external_id: str) -> list[MarketSignalRead] | None:
    detail = get_game_detail(db, external_id)
    return None if detail is None else detail.signals


def _build_summary(db: Session, game: Game) -> GameSummary:
    snapshots = _snapshots_for_game(db, game.id)
    signals = _signals_for_game(db, game.id)
    current_markets = _current_markets(snapshots)
    opening_markets = _opening_markets(snapshots)
    home_spread_history = [
        snapshot.line
        for snapshot in snapshots
        if snapshot.market_type == "spread"
        and snapshot.selection == game.home_team.name
        and snapshot.sportsbook.title == "DraftKings"
        and snapshot.line is not None
    ]
    latest_spreads = [line.line for line in current_markets.spread if line.line is not None]

    return GameSummary(
        id=game.external_id,
        sport_key=game.sport_key,
        commence_time=game.commence_time,
        home_team=_team_read(game.home_team),
        away_team=_team_read(game.away_team),
        current_markets=current_markets,
        opening_markets=opening_markets,
        signals=signals,
        volatility_score=calculate_volatility(home_spread_history),
        book_disagreement_score=calculate_book_disagreement(latest_spreads),
    )


def _snapshots_for_game(db: Session, game_id) -> list[OddsSnapshot]:
    return list(
        db.scalars(
            select(OddsSnapshot)
            .where(OddsSnapshot.game_id == game_id)
            .options(joinedload(OddsSnapshot.sportsbook))
            .order_by(OddsSnapshot.snapshot_time, OddsSnapshot.market_type, OddsSnapshot.sportsbook_id)
        )
        .unique()
        .all()
    )


def _signals_for_game(db: Session, game_id) -> list[MarketSignalRead]:
    signals = db.scalars(
        select(MarketSignal)
        .where(MarketSignal.game_id == game_id)
        .order_by(MarketSignal.detected_at.desc())
    ).all()
    return [
        MarketSignalRead(
            signal_type=signal.signal_type,
            market_type=signal.market_type,
            severity=signal.severity,
            message=signal.message,
            value=signal.value,
            detected_at=signal.detected_at,
        )
        for signal in signals
    ]


def _current_markets(snapshots: list[OddsSnapshot]) -> CurrentMarkets:
    latest_time = max((snapshot.snapshot_time for snapshot in snapshots), default=None)
    latest = [snapshot for snapshot in snapshots if snapshot.snapshot_time == latest_time]
    return _markets_from_snapshots(latest)


def _opening_markets(snapshots: list[OddsSnapshot]) -> CurrentMarkets:
    opening_time = min((snapshot.snapshot_time for snapshot in snapshots), default=None)
    opening = [
        snapshot
        for snapshot in snapshots
        if snapshot.snapshot_time == opening_time and snapshot.sportsbook.title == "DraftKings"
    ]
    return _markets_from_snapshots(opening)


def _markets_from_snapshots(snapshots: list[OddsSnapshot]) -> CurrentMarkets:
    lines = [_snapshot_to_line(snapshot) for snapshot in snapshots]
    return CurrentMarkets(
        spread=[line for line in lines if line.market_type == "spread"],
        moneyline=[line for line in lines if line.market_type == "moneyline"],
        total=[line for line in lines if line.market_type == "total"],
    )


def _snapshot_to_line(snapshot: OddsSnapshot) -> OddsLine:
    return OddsLine(
        sportsbook=snapshot.sportsbook.title,
        selection=snapshot.selection,
        market_type=snapshot.market_type,
        line=snapshot.line,
        odds_american=snapshot.odds_american,
        implied_probability=snapshot.implied_probability,
        snapshot_time=snapshot.snapshot_time,
    )


def _team_read(team: Team) -> TeamRead:
    return TeamRead(id=str(team.id), name=team.name, abbreviation=team.abbreviation)
