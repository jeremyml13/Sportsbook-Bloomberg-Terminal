from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.models import Game, MarketSignal, OddsSnapshot, PlayerInjury, PlayerInjuryEvent, PlayerNews, Sportsbook, Team
from app.schemas.markets import (
    CurrentMarkets,
    GameDetail,
    GamePlayerContextRead,
    GameSummary,
    MarketSignalRead,
    BestPriceRead,
    MovementAlertRead,
    NoVigProbabilityRead,
    OddsHistoryPoint,
    OddsLine,
    PriceAlertRead,
    PlayerInjuryEventRead,
    PlayerInjuryRead,
    PlayerNewsRead,
    TeamRead,
)
from app.services.mlb_teams import mlb_abbreviation
from app.services.odds_math import calculate_book_disagreement, calculate_volatility


def persist_player_context(
    db: Session,
    injury_rows: list[dict[str, Any]],
    news_rows: list[dict[str, Any]],
) -> dict[str, int]:
    counts = {"injuries": 0, "news": 0}

    for row in injury_rows:
        injury = db.scalar(
            select(PlayerInjury).where(
                PlayerInjury.external_player_id == row["external_player_id"],
                PlayerInjury.team == row["team"],
            )
            .order_by(PlayerInjury.observed_at.desc())
        )
        if injury is None:
            db.add(PlayerInjury(**row))
            db.add(_injury_event(row, "new_injury"))
            counts["injuries"] += 1
        else:
            previous = {
                "status": injury.injury_status,
                "body_part": injury.injury_body_part,
                "notes": injury.injury_notes,
            }
            changed = (
                previous["status"] != row["injury_status"]
                or previous["body_part"] != row["injury_body_part"]
                or previous["notes"] != row["injury_notes"]
            )
            for key, value in row.items():
                setattr(injury, key, value)
            if changed:
                db.add(_injury_event(row, "injury_update", previous))

    for row in news_rows:
        news = db.scalar(select(PlayerNews).where(PlayerNews.external_news_id == row["external_news_id"]))
        if news is None:
            db.add(PlayerNews(**row))
            counts["news"] += 1
        else:
            for key, value in row.items():
                setattr(news, key, value)

    db.commit()
    return counts


def _injury_event(
    row: dict[str, Any],
    event_type: str,
    previous: dict[str, str | None] | None = None,
) -> PlayerInjuryEvent:
    return PlayerInjuryEvent(
        external_player_id=row["external_player_id"],
        sport_key=row["sport_key"],
        display_name=row["display_name"],
        team=row["team"],
        position=row["position"],
        event_type=event_type,
        previous_status=(previous or {}).get("status"),
        current_status=row["injury_status"],
        previous_body_part=(previous or {}).get("body_part"),
        current_body_part=row["injury_body_part"],
        previous_notes=(previous or {}).get("notes"),
        current_notes=row["injury_notes"],
        detected_at=row["observed_at"],
        raw_payload=row["raw_payload"],
    )


def get_mlb_injuries(db: Session, team: str | None = None, limit: int = 100) -> list[PlayerInjury]:
    query = select(PlayerInjury).where(PlayerInjury.sport_key == "baseball_mlb")
    if team:
        query = query.where(PlayerInjury.team == team.upper())

    return list(db.scalars(query.order_by(PlayerInjury.observed_at.desc(), PlayerInjury.display_name).limit(limit)))


def get_mlb_news(db: Session, team: str | None = None, limit: int = 50) -> list[PlayerNews]:
    query = select(PlayerNews).where(PlayerNews.sport_key == "baseball_mlb")
    if team:
        team_code = team.upper()
        query = query.where((PlayerNews.team == team_code) | (PlayerNews.team2 == team_code))

    return list(db.scalars(query.order_by(PlayerNews.updated_at.desc().nullslast(), PlayerNews.observed_at.desc()).limit(limit)))


def get_mlb_game_context(db: Session, external_id: str, limit: int = 12) -> GamePlayerContextRead | None:
    game = db.scalar(
        select(Game)
        .where(Game.external_id == external_id)
        .options(joinedload(Game.home_team), joinedload(Game.away_team))
    )
    if game is None:
        return None

    teams = [
        team
        for team in [
            game.away_team.abbreviation or mlb_abbreviation(game.away_team.name),
            game.home_team.abbreviation or mlb_abbreviation(game.home_team.name),
        ]
        if team
    ]
    injuries = list(
        db.scalars(
            select(PlayerInjury)
            .where(PlayerInjury.sport_key == game.sport_key, PlayerInjury.team.in_(teams))
            .order_by(PlayerInjury.observed_at.desc(), PlayerInjury.display_name)
            .limit(limit)
        )
    )
    injury_events = list(
        db.scalars(
            select(PlayerInjuryEvent)
            .where(PlayerInjuryEvent.sport_key == game.sport_key, PlayerInjuryEvent.team.in_(teams))
            .order_by(PlayerInjuryEvent.detected_at.desc())
            .limit(limit)
        )
    )
    news = list(
        db.scalars(
            select(PlayerNews)
            .where(
                PlayerNews.sport_key == game.sport_key,
                (PlayerNews.team.in_(teams)) | (PlayerNews.team2.in_(teams)),
            )
            .order_by(PlayerNews.updated_at.desc().nullslast(), PlayerNews.observed_at.desc())
            .limit(limit)
        )
    )

    return GamePlayerContextRead(
        game_id=external_id,
        teams=teams,
        injuries=[_injury_read(injury) for injury in injuries],
        injury_events=[_injury_event_read(event) for event in injury_events],
        news=[PlayerNewsRead.model_validate(item) for item in news],
    )


def _clean_scrambled(value: str | None) -> str | None:
    if value is None:
        return None
    if value.strip().lower() == "scrambled":
        return None

    return value


def _injury_read(injury: PlayerInjury) -> PlayerInjuryRead:
    return PlayerInjuryRead(
        external_player_id=injury.external_player_id,
        display_name=injury.display_name,
        team=injury.team,
        position=injury.position,
        status=injury.status,
        injury_status=_clean_scrambled(injury.injury_status),
        injury_body_part=_clean_scrambled(injury.injury_body_part),
        injury_start_date=injury.injury_start_date,
        injury_notes=_clean_scrambled(injury.injury_notes),
        upcoming_game_external_id=injury.upcoming_game_external_id,
        observed_at=injury.observed_at,
    )


def _injury_event_read(event: PlayerInjuryEvent) -> PlayerInjuryEventRead:
    return PlayerInjuryEventRead(
        external_player_id=event.external_player_id,
        display_name=event.display_name,
        team=event.team,
        position=event.position,
        event_type=event.event_type,
        previous_status=_clean_scrambled(event.previous_status),
        current_status=_clean_scrambled(event.current_status),
        previous_body_part=_clean_scrambled(event.previous_body_part),
        current_body_part=_clean_scrambled(event.current_body_part),
        previous_notes=_clean_scrambled(event.previous_notes),
        current_notes=_clean_scrambled(event.current_notes),
        detected_at=event.detected_at,
    )


def persist_normalized_odds(db: Session, rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = {
        "games": 0,
        "teams": 0,
        "sportsbooks": 0,
        "odds_snapshots": 0,
    }

    teams: dict[tuple[str, str], Team] = {}
    sportsbooks: dict[str, Sportsbook] = {}
    games: dict[str, Game] = {}

    for row in rows:
        sport_key = row["sport_key"]
        home_team = _get_or_create_team(db, teams, row["home_team"], sport_key, counts)
        away_team = _get_or_create_team(db, teams, row["away_team"], sport_key, counts)
        sportsbook = _get_or_create_sportsbook(
            db,
            sportsbooks,
            row["sportsbook_key"],
            row["sportsbook_title"],
            counts,
        )
        game = _get_or_create_game(db, games, row, home_team, away_team, counts)

        exists = db.scalar(
            select(OddsSnapshot.id).where(
                OddsSnapshot.game_id == game.id,
                OddsSnapshot.sportsbook_id == sportsbook.id,
                OddsSnapshot.market_type == row["market_type"],
                OddsSnapshot.selection == row["selection"],
                OddsSnapshot.snapshot_time == row["snapshot_time"],
            )
        )
        if exists is not None:
            continue

        db.add(
            OddsSnapshot(
                game_id=game.id,
                sportsbook_id=sportsbook.id,
                market_type=row["market_type"],
                selection=row["selection"],
                line=row["line"],
                odds_american=row["odds_american"],
                implied_probability=row["implied_probability"],
                snapshot_time=row["snapshot_time"],
                source=row["source"],
                raw_payload=row["raw_payload"],
            )
        )
        counts["odds_snapshots"] += 1

    db.commit()
    return counts


def get_today_game_summaries(db: Session) -> list[GameSummary]:
    start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    games = list(db.scalars(
        select(Game)
        .where(Game.commence_time >= start, Game.commence_time < end)
        .options(joinedload(Game.home_team), joinedload(Game.away_team))
        .order_by(Game.commence_time)
    ).all())
    odds_api_games = [game for game in games if game.external_id.startswith("oddsapi-mlb-")]
    if odds_api_games:
        games = odds_api_games

    summaries = [_build_summary(db, game) for game in games]
    return sorted(summaries, key=lambda game: (-game.opportunity_score, game.commence_time))


def _get_or_create_team(
    db: Session,
    cache: dict[tuple[str, str], Team],
    name: str,
    sport_key: str,
    counts: dict[str, int],
) -> Team:
    cache_key = (sport_key, name)
    if cache_key in cache:
        return cache[cache_key]

    team = db.scalar(select(Team).where(Team.name == name))
    abbreviation = mlb_abbreviation(name) if sport_key == "baseball_mlb" else None
    if team is None:
        team = Team(name=name, abbreviation=abbreviation or (name if len(name) <= 12 else None), sport_key=sport_key)
        db.add(team)
        db.flush()
        counts["teams"] += 1
    elif abbreviation and team.abbreviation != abbreviation:
        team.abbreviation = abbreviation

    cache[cache_key] = team
    return team


def _get_or_create_sportsbook(
    db: Session,
    cache: dict[str, Sportsbook],
    key: str,
    title: str,
    counts: dict[str, int],
) -> Sportsbook:
    if key in cache:
        return cache[key]

    sportsbook = db.scalar(select(Sportsbook).where(Sportsbook.key == key))
    if sportsbook is None:
        sportsbook = Sportsbook(key=key, title=title, region="us")
        db.add(sportsbook)
        db.flush()
        counts["sportsbooks"] += 1

    cache[key] = sportsbook
    return sportsbook


def _get_or_create_game(
    db: Session,
    cache: dict[str, Game],
    row: dict[str, Any],
    home_team: Team,
    away_team: Team,
    counts: dict[str, int],
) -> Game:
    external_id = row["external_game_id"]
    if external_id in cache:
        return cache[external_id]

    game = db.scalar(select(Game).where(Game.external_id == external_id))
    if game is None:
        game = Game(
            external_id=external_id,
            sport_key=row["sport_key"],
            commence_time=row["commence_time"],
            home_team_id=home_team.id,
            away_team_id=away_team.id,
            status=row.get("status", "scheduled").lower(),
        )
        db.add(game)
        db.flush()
        counts["games"] += 1
    else:
        game.commence_time = row["commence_time"]
        game.status = row.get("status", game.status).lower()

    cache[external_id] = game
    return game


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
        movement_alerts=_movement_alerts(snapshots),
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
    volatility_score = calculate_volatility(home_spread_history)
    book_disagreement_score = calculate_book_disagreement(latest_spreads)
    best_prices = _best_prices(current_markets)
    no_vig_moneyline = _no_vig_moneyline(current_markets.moneyline)
    price_alerts = _price_alerts(current_markets)
    opportunity_score, opportunity_reasons = _opportunity(
        signals=signals,
        volatility_score=volatility_score,
        book_disagreement_score=book_disagreement_score,
        price_alerts=price_alerts,
    )

    return GameSummary(
        id=game.external_id,
        sport_key=game.sport_key,
        commence_time=game.commence_time,
        home_team=_team_read(game.home_team),
        away_team=_team_read(game.away_team),
        current_markets=current_markets,
        opening_markets=opening_markets,
        signals=signals,
        volatility_score=volatility_score,
        book_disagreement_score=book_disagreement_score,
        opportunity_score=opportunity_score,
        opportunity_reasons=opportunity_reasons,
        best_prices=best_prices,
        no_vig_moneyline=no_vig_moneyline,
        price_alerts=price_alerts,
    )


def _best_prices(markets: CurrentMarkets) -> list[BestPriceRead]:
    rows = [*markets.spread, *markets.moneyline, *markets.total]
    best: dict[tuple[str, str, float | None], OddsLine] = {}

    for row in rows:
        key = (row.market_type, row.selection, row.line)
        current = best.get(key)
        if current is None or row.odds_american > current.odds_american:
            best[key] = row

    return [
        BestPriceRead(
            market_type=row.market_type,
            selection=row.selection,
            sportsbook=row.sportsbook,
            line=row.line,
            odds_american=row.odds_american,
            implied_probability=row.implied_probability,
        )
        for row in sorted(best.values(), key=lambda item: (item.market_type, item.selection, item.line or 0))
    ]


def _no_vig_moneyline(lines: list[OddsLine]) -> list[NoVigProbabilityRead]:
    by_book: dict[str, list[OddsLine]] = {}
    for line in lines:
        by_book.setdefault(line.sportsbook, []).append(line)

    fair_probs: dict[str, list[float]] = {}
    for book_lines in by_book.values():
        total_probability = sum(line.implied_probability for line in book_lines)
        if total_probability <= 0 or len(book_lines) < 2:
            continue

        for line in book_lines:
            fair_probs.setdefault(line.selection, []).append(line.implied_probability / total_probability)

    best_by_selection: dict[str, OddsLine] = {}
    for line in lines:
        current = best_by_selection.get(line.selection)
        if current is None or line.odds_american > current.odds_american:
            best_by_selection[line.selection] = line

    return [
        NoVigProbabilityRead(
            selection=selection,
            fair_probability=sum(probabilities) / len(probabilities),
            best_sportsbook=best_by_selection.get(selection).sportsbook if selection in best_by_selection else None,
            best_odds_american=best_by_selection.get(selection).odds_american if selection in best_by_selection else None,
        )
        for selection, probabilities in sorted(fair_probs.items())
    ]


def _price_alerts(markets: CurrentMarkets) -> list[PriceAlertRead]:
    alerts: list[PriceAlertRead] = []
    market_rows = [*markets.spread, *markets.moneyline, *markets.total]
    grouped: dict[tuple[str, str, float | None], list[OddsLine]] = {}
    for row in market_rows:
        grouped.setdefault((row.market_type, row.selection, row.line), []).append(row)

    for (market_type, selection, line), rows in grouped.items():
        if len(rows) < 3:
            continue

        average_implied = sum(row.implied_probability for row in rows) / len(rows)
        best = max(rows, key=lambda row: row.odds_american)
        edge_to_market = round((average_implied - best.implied_probability) * 100, 2)
        if edge_to_market < 1.5:
            continue

        alerts.append(
            PriceAlertRead(
                market_type=market_type,
                selection=selection,
                sportsbook=best.sportsbook,
                line=line,
                odds_american=best.odds_american,
                edge_to_market=edge_to_market,
                message=f"{best.sportsbook} is {edge_to_market:.1f} implied points cheaper than the market average on {selection}.",
            )
        )

    return sorted(alerts, key=lambda alert: alert.edge_to_market, reverse=True)[:5]


def _opportunity(
    signals: list[MarketSignalRead],
    volatility_score: float,
    book_disagreement_score: float,
    price_alerts: list[PriceAlertRead],
) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []

    if price_alerts:
        best_alert = price_alerts[0]
        score += min(35.0, best_alert.edge_to_market * 8)
        reasons.append(f"Best price is {best_alert.edge_to_market:.1f} implied points cheaper than market.")

    if book_disagreement_score >= 1:
        score += min(25.0, book_disagreement_score * 10)
        reasons.append(f"Books disagree by {book_disagreement_score:.1f} points on the spread.")

    if volatility_score >= 0.5:
        score += min(20.0, volatility_score * 12)
        reasons.append(f"Spread volatility is elevated at {volatility_score:.2f}.")

    warning_signals = [signal for signal in signals if signal.severity == "warning"]
    if warning_signals:
        score += min(20.0, len(warning_signals) * 8)
        reasons.append(f"{len(warning_signals)} warning market signal{'s' if len(warning_signals) != 1 else ''} active.")

    return round(min(score, 100.0), 1), reasons[:4]


def _movement_alerts(snapshots: list[OddsSnapshot]) -> list[MovementAlertRead]:
    grouped: dict[tuple[str, str, str], list[OddsSnapshot]] = {}
    for snapshot in snapshots:
        grouped.setdefault(
            (snapshot.sportsbook.title, snapshot.market_type, snapshot.selection),
            [],
        ).append(snapshot)

    alerts: list[MovementAlertRead] = []
    for (sportsbook, market_type, selection), rows in grouped.items():
        ordered = sorted(rows, key=lambda snapshot: snapshot.snapshot_time)
        if len(ordered) < 2:
            continue

        opening = ordered[0]
        current = ordered[-1]
        line_delta = None
        if opening.line is not None and current.line is not None:
            line_delta = round(current.line - opening.line, 2)
        odds_delta = current.odds_american - opening.odds_american
        line_moved = line_delta is not None and abs(line_delta) >= 0.5
        odds_moved = abs(odds_delta) >= 15
        if not line_moved and not odds_moved:
            continue

        move_parts: list[str] = []
        if line_moved:
            move_parts.append(f"line moved {line_delta:+.1f}")
        if odds_moved:
            move_parts.append(f"price moved {odds_delta:+d} cents")

        alerts.append(
            MovementAlertRead(
                sportsbook=sportsbook,
                market_type=market_type,
                selection=selection,
                opening_line=opening.line,
                current_line=current.line,
                line_delta=line_delta,
                opening_odds_american=opening.odds_american,
                current_odds_american=current.odds_american,
                odds_delta=odds_delta,
                first_seen=opening.snapshot_time,
                last_seen=current.snapshot_time,
                message=f"{sportsbook} {market_type} on {selection}: {', '.join(move_parts)}.",
            )
        )

    return sorted(
        alerts,
        key=lambda alert: (abs(alert.line_delta or 0) * 20) + abs(alert.odds_delta),
        reverse=True,
    )[:8]


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
