from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.db.models import Game, MarketSignal, OddsSnapshot, Sportsbook, Team
from app.services.mock_data import ALL_GAMES, BOOKS, get_mock_game
from app.services.odds_math import american_to_implied_probability


def seed_mock_data(db: Session) -> dict[str, int]:
    db.execute(delete(MarketSignal))
    db.execute(delete(OddsSnapshot))
    db.execute(delete(Game))
    db.execute(delete(Team))
    db.execute(delete(Sportsbook))

    sportsbooks = _seed_sportsbooks(db)
    teams = _seed_teams(db)
    counts = {
        "games": 0,
        "teams": len(teams),
        "sportsbooks": len(sportsbooks),
        "odds_snapshots": 0,
        "market_signals": 0,
    }

    for mock_game in ALL_GAMES:
        detail = get_mock_game(mock_game["id"])
        if detail is None:
            continue

        game = Game(
            external_id=detail.id,
            sport_key=detail.sport_key,
            commence_time=detail.commence_time,
            home_team_id=teams[detail.home_team.name].id,
            away_team_id=teams[detail.away_team.name].id,
            status="scheduled",
        )
        db.add(game)
        db.flush()
        counts["games"] += 1

        for snapshot in detail.odds_history:
            db.add(
                OddsSnapshot(
                    game_id=game.id,
                    sportsbook_id=sportsbooks[snapshot.sportsbook].id,
                    market_type=snapshot.market_type,
                    selection=snapshot.selection,
                    line=snapshot.line,
                    odds_american=snapshot.odds_american,
                    implied_probability=american_to_implied_probability(snapshot.odds_american),
                    snapshot_time=snapshot.timestamp,
                    source="mock",
                    raw_payload=None,
                )
            )
            counts["odds_snapshots"] += 1

        for signal in detail.signals:
            db.add(
                MarketSignal(
                    game_id=game.id,
                    signal_type=signal.signal_type,
                    market_type=signal.market_type,
                    severity=signal.severity,
                    message=signal.message,
                    value=signal.value,
                    detected_at=signal.detected_at,
                )
            )
            counts["market_signals"] += 1

    db.commit()
    return counts


def _seed_sportsbooks(db: Session) -> dict[str, Sportsbook]:
    sportsbooks: dict[str, Sportsbook] = {}
    for title in BOOKS:
        sportsbook = Sportsbook(key=title.lower().replace(" ", "_"), title=title, region="us")
        db.add(sportsbook)
        sportsbooks[title] = sportsbook
    db.flush()
    return sportsbooks


def _seed_teams(db: Session) -> dict[str, Team]:
    teams: dict[str, Team] = {}
    for mock_game in ALL_GAMES:
        for _, name, abbreviation in (mock_game["home"], mock_game["away"]):
            if name in teams:
                continue
            team = Team(name=name, abbreviation=abbreviation, sport_key=mock_game["sport_key"])
            db.add(team)
            teams[name] = team
    db.flush()
    return teams
