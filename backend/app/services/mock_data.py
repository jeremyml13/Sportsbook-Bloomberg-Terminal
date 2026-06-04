from datetime import UTC, datetime, timedelta

from app.schemas.markets import (
    CurrentMarkets,
    GameDetail,
    GameSummary,
    MarketSignalRead,
    OddsHistoryPoint,
    OddsLine,
    TeamRead,
)
from app.services.odds_math import american_to_implied_probability, calculate_book_disagreement, calculate_volatility

now = datetime.now(UTC).replace(microsecond=0)

BOOKS = ("DraftKings", "FanDuel", "BetMGM", "Caesars")
SNAPSHOT_HOURS = (24, 12, 6, 2, 0)

NBA_GAMES = [
    {
        "id": "nba-lal-bos-001",
        "home": ("team-bos", "Boston Celtics", "BOS"),
        "away": ("team-lal", "Los Angeles Lakers", "LAL"),
        "start_hours": 3,
        "spread_path": (-2.5, -3.5, -4.0, -4.5, -5.0),
        "total_path": (221.5, 222.0, 222.5, 223.5, 224.0),
        "signals": ("sharp_movement", "book_disagreement", "best_number_gone"),
    },
    {
        "id": "nba-nyk-mia-002",
        "home": ("team-mia", "Miami Heat", "MIA"),
        "away": ("team-nyk", "New York Knicks", "NYK"),
        "start_hours": 4,
        "spread_path": (-1.0, -1.0, -1.5, -2.5, -2.0),
        "total_path": (214.0, 213.5, 212.5, 212.0, 211.5),
        "signals": ("high_volatility", "reverse_line_movement"),
    },
    {
        "id": "nba-den-phx-003",
        "home": ("team-den", "Denver Nuggets", "DEN"),
        "away": ("team-phx", "Phoenix Suns", "PHX"),
        "start_hours": 5,
        "spread_path": (-6.5, -6.0, -5.5, -5.5, -5.0),
        "total_path": (229.5, 230.0, 230.5, 230.5, 231.0),
        "signals": ("book_disagreement",),
    },
    {
        "id": "nba-dal-min-004",
        "home": ("team-min", "Minnesota Timberwolves", "MIN"),
        "away": ("team-dal", "Dallas Mavericks", "DAL"),
        "start_hours": 6,
        "spread_path": (-3.5, -3.0, -2.0, -1.5, -1.5),
        "total_path": (218.0, 218.5, 219.5, 220.0, 220.5),
        "signals": ("sharp_movement", "high_volatility"),
    },
    {
        "id": "nba-gsw-sac-005",
        "home": ("team-sac", "Sacramento Kings", "SAC"),
        "away": ("team-gsw", "Golden State Warriors", "GSW"),
        "start_hours": 7,
        "spread_path": (1.5, 1.0, 0.5, -1.0, -1.5),
        "total_path": (236.5, 237.0, 238.0, 239.0, 239.5),
        "signals": ("sharp_movement", "book_disagreement", "best_number_gone"),
    },
]

MLB_GAMES = [
    {
        "id": "mlb-lad-sf-001",
        "sport_key": "baseball_mlb",
        "home": ("team-sf", "San Francisco Giants", "SF"),
        "away": ("team-lad", "Los Angeles Dodgers", "LAD"),
        "start_hours": 2,
        "spread_path": (1.5, 1.5, 1.0, 1.0, 0.5),
        "total_path": (8.5, 8.0, 8.0, 7.5, 7.5),
        "signals": ("sharp_movement", "book_disagreement", "best_number_gone"),
    },
    {
        "id": "mlb-nyy-bos-002",
        "sport_key": "baseball_mlb",
        "home": ("team-bos-mlb", "Boston Red Sox", "BOS"),
        "away": ("team-nyy", "New York Yankees", "NYY"),
        "start_hours": 3,
        "spread_path": (-1.5, -1.0, -1.0, -0.5, -0.5),
        "total_path": (9.0, 9.0, 9.5, 9.5, 10.0),
        "signals": ("high_volatility", "reverse_line_movement"),
    },
    {
        "id": "mlb-atl-phi-003",
        "sport_key": "baseball_mlb",
        "home": ("team-phi", "Philadelphia Phillies", "PHI"),
        "away": ("team-atl", "Atlanta Braves", "ATL"),
        "start_hours": 4,
        "spread_path": (-0.5, -0.5, -1.0, -1.5, -1.5),
        "total_path": (8.0, 8.5, 8.5, 8.5, 9.0),
        "signals": ("book_disagreement",),
    },
    {
        "id": "mlb-chc-stl-004",
        "sport_key": "baseball_mlb",
        "home": ("team-stl", "St. Louis Cardinals", "STL"),
        "away": ("team-chc", "Chicago Cubs", "CHC"),
        "start_hours": 5,
        "spread_path": (0.5, 0.5, 0.0, -0.5, -1.0),
        "total_path": (7.5, 7.5, 8.0, 8.0, 8.5),
        "signals": ("sharp_movement", "high_volatility"),
    },
]

NFL_GAMES = [
    {
        "id": "nfl-kc-buf-001",
        "sport_key": "americanfootball_nfl",
        "home": ("team-buf", "Buffalo Bills", "BUF"),
        "away": ("team-kc", "Kansas City Chiefs", "KC"),
        "start_hours": 8,
        "spread_path": (-1.5, -2.0, -2.0, -2.5, -3.0),
        "total_path": (48.5, 49.0, 49.5, 50.0, 50.5),
        "signals": ("sharp_movement", "book_disagreement"),
    },
    {
        "id": "nfl-dal-phi-002",
        "sport_key": "americanfootball_nfl",
        "home": ("team-phi-nfl", "Philadelphia Eagles", "PHI"),
        "away": ("team-dal-nfl", "Dallas Cowboys", "DAL"),
        "start_hours": 9,
        "spread_path": (-4.5, -4.0, -3.5, -3.0, -3.0),
        "total_path": (45.0, 45.5, 46.0, 46.0, 46.5),
        "signals": ("reverse_line_movement", "book_disagreement"),
    },
    {
        "id": "nfl-sf-sea-003",
        "sport_key": "americanfootball_nfl",
        "home": ("team-sea", "Seattle Seahawks", "SEA"),
        "away": ("team-sf-nfl", "San Francisco 49ers", "SF"),
        "start_hours": 10,
        "spread_path": (6.5, 6.0, 5.5, 5.0, 4.5),
        "total_path": (43.5, 43.0, 42.5, 42.0, 41.5),
        "signals": ("sharp_movement", "best_number_gone"),
    },
    {
        "id": "nfl-cin-bal-004",
        "sport_key": "americanfootball_nfl",
        "home": ("team-bal", "Baltimore Ravens", "BAL"),
        "away": ("team-cin", "Cincinnati Bengals", "CIN"),
        "start_hours": 11,
        "spread_path": (-6.0, -6.5, -7.0, -7.0, -7.5),
        "total_path": (46.5, 47.0, 47.5, 47.5, 48.0),
        "signals": ("high_volatility", "book_disagreement", "best_number_gone"),
    },
]

for game in NBA_GAMES:
    game["sport_key"] = "basketball_nba"

ALL_GAMES = [*NBA_GAMES, *MLB_GAMES, *NFL_GAMES]

BOOK_ADJUSTMENTS = {
    "DraftKings": 0.0,
    "FanDuel": -0.5,
    "BetMGM": 0.0,
    "Caesars": 0.5,
}


def _team(data: tuple[str, str, str]) -> TeamRead:
    return TeamRead(id=data[0], name=data[1], abbreviation=data[2])


def _american_moneyline_from_spread(spread: float, is_home: bool) -> int:
    home_favored = spread < 0
    strength = min(abs(spread), 8)
    if is_home == home_favored:
        return int(-115 - strength * 14)
    return int(105 + strength * 13)


def _line(sportsbook: str, selection: str, market_type: str, line: float | None, odds: int, timestamp: datetime) -> OddsLine:
    return OddsLine(
        sportsbook=sportsbook,
        selection=selection,
        market_type=market_type,
        line=line,
        odds_american=odds,
        implied_probability=american_to_implied_probability(odds),
        snapshot_time=timestamp,
    )


def _snapshots(game: dict) -> list[OddsLine]:
    home = _team(game["home"])
    away = _team(game["away"])
    rows: list[OddsLine] = []

    for index, hours in enumerate(SNAPSHOT_HOURS):
        timestamp = now - timedelta(hours=hours)
        base_spread = game["spread_path"][index]
        base_total = game["total_path"][index]

        for book in BOOKS:
            adjustment = BOOK_ADJUSTMENTS[book]
            spread = base_spread + adjustment
            total = base_total + (adjustment * 0.5)
            spread_odds = -110 + (index % 2) * 5
            total_odds = -110 - (index % 3) * 2

            rows.extend(
                [
                    _line(book, home.name, "spread", spread, spread_odds, timestamp),
                    _line(book, home.name, "moneyline", None, _american_moneyline_from_spread(spread, True), timestamp),
                    _line(book, away.name, "moneyline", None, _american_moneyline_from_spread(spread, False), timestamp),
                    _line(book, "Over", "total", total, total_odds, timestamp),
                ]
            )

    return rows


def _current_markets(snapshot_rows: list[OddsLine]) -> CurrentMarkets:
    latest_time = max(row.snapshot_time for row in snapshot_rows)
    latest = [row for row in snapshot_rows if row.snapshot_time == latest_time]
    return CurrentMarkets(
        spread=[row for row in latest if row.market_type == "spread"],
        moneyline=[row for row in latest if row.market_type == "moneyline"],
        total=[row for row in latest if row.market_type == "total"],
    )


def _opening_markets(snapshot_rows: list[OddsLine]) -> CurrentMarkets:
    opening_time = min(row.snapshot_time for row in snapshot_rows)
    opening = [row for row in snapshot_rows if row.snapshot_time == opening_time and row.sportsbook == "DraftKings"]
    return CurrentMarkets(
        spread=[row for row in opening if row.market_type == "spread"],
        moneyline=[row for row in opening if row.market_type == "moneyline"],
        total=[row for row in opening if row.market_type == "total"],
    )


def _signals(game: dict, snapshot_rows: list[OddsLine]) -> list[MarketSignalRead]:
    home = _team(game["home"])
    opening_spread = game["spread_path"][0]
    current_spread = game["spread_path"][-1]
    current_total = game["total_path"][-1]
    latest_spreads = [row.line for row in _current_markets(snapshot_rows).spread if row.line is not None]
    spread_disagreement = calculate_book_disagreement(latest_spreads)
    spread_volatility = calculate_volatility([float(value) for value in game["spread_path"]])
    messages = {
        "high_volatility": ("High Volatility", "warning", "Spread and total have moved through multiple price levels."),
        "sharp_movement": ("Sharp Movement", "warning", f"{home.abbreviation} spread moved {abs(current_spread - opening_spread):.1f} points from the opener."),
        "reverse_line_movement": ("Reverse Line Movement", "placeholder", "Placeholder until bet split and handle data are available."),
        "book_disagreement": ("Book Disagreement", "info", f"Current spread differs by {spread_disagreement:.1f} points across major books."),
        "best_number_gone": ("Best Number Gone", "warning", f"The opening number is no longer broadly available; current total is {current_total:.1f}."),
    }

    return [
        MarketSignalRead(
            signal_type=messages[signal][0],
            market_type="spread" if signal != "best_number_gone" else "total",
            severity=messages[signal][1],
            message=messages[signal][2],
            value=spread_volatility if signal == "high_volatility" else spread_disagreement if signal == "book_disagreement" else None,
            detected_at=now,
        )
        for signal in game["signals"]
    ]


def _summary(game: dict) -> GameSummary:
    snapshot_rows = _snapshots(game)
    latest_spreads = [row.line for row in _current_markets(snapshot_rows).spread if row.line is not None]
    return GameSummary(
        id=game["id"],
        sport_key=game["sport_key"],
        commence_time=now + timedelta(hours=game["start_hours"]),
        home_team=_team(game["home"]),
        away_team=_team(game["away"]),
        current_markets=_current_markets(snapshot_rows),
        opening_markets=_opening_markets(snapshot_rows),
        signals=_signals(game, snapshot_rows),
        volatility_score=calculate_volatility([float(value) for value in game["spread_path"]]),
        book_disagreement_score=calculate_book_disagreement(latest_spreads),
    )


mock_games: list[GameSummary] = [_summary(game) for game in ALL_GAMES]


def get_mock_game(game_id: str) -> GameDetail | None:
    game = next((item for item in ALL_GAMES if item["id"] == game_id), None)
    if game is None:
        return None

    summary = _summary(game)
    snapshot_rows = _snapshots(game)
    odds_history = [
        OddsHistoryPoint(
            timestamp=row.snapshot_time,
            sportsbook=row.sportsbook,
            market_type=row.market_type,
            selection=row.selection,
            line=row.line,
            odds_american=row.odds_american,
        )
        for row in snapshot_rows
    ]

    latest_time = max(row.snapshot_time for row in snapshot_rows)
    book_table = [row for row in snapshot_rows if row.snapshot_time == latest_time]
    return GameDetail(**summary.model_dump(), odds_history=odds_history, book_table=book_table)
