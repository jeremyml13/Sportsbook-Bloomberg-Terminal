from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.repository import get_game_detail, get_game_odds_history, get_game_signals, get_odds_freshness, get_today_game_summaries
from app.db.session import get_db
from app.schemas.markets import GameDetail, GameSummary, MarketSignalRead, OddsFreshnessRead, OddsHistoryPoint
from app.services.mock_data import get_mock_game, mock_games

router = APIRouter(prefix="/games", tags=["games"])


@router.get("/today", response_model=list[GameSummary])
def get_today_games(db: Session = Depends(get_db)) -> list[GameSummary]:
    try:
        games = get_today_game_summaries(db)
        if games:
            return games
    except SQLAlchemyError:
        db.rollback()

    return mock_games


@router.get("/meta/odds-freshness", response_model=OddsFreshnessRead)
def get_odds_freshness_route(db: Session = Depends(get_db)) -> OddsFreshnessRead:
    return get_odds_freshness(db)


@router.get("/{game_id}", response_model=GameDetail)
def get_game(game_id: str, db: Session = Depends(get_db)) -> GameDetail:
    try:
        game = get_game_detail(db, game_id)
        if game is not None:
            return game
    except SQLAlchemyError:
        db.rollback()

    game = get_mock_game(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    return game


@router.get("/{game_id}/odds-history", response_model=list[OddsHistoryPoint])
def get_game_odds_history_route(game_id: str, db: Session = Depends(get_db)) -> list[OddsHistoryPoint]:
    try:
        history = get_game_odds_history(db, game_id)
        if history is not None:
            return history
    except SQLAlchemyError:
        db.rollback()

    game = get_mock_game(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    return game.odds_history


@router.get("/{game_id}/signals", response_model=list[MarketSignalRead])
def get_game_signals_route(game_id: str, db: Session = Depends(get_db)) -> list[MarketSignalRead]:
    try:
        signals = get_game_signals(db, game_id)
        if signals is not None:
            return signals
    except SQLAlchemyError:
        db.rollback()

    game = get_mock_game(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    return game.signals
