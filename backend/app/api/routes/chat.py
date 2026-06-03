from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.repository import (
    get_game_detail,
    get_odds_freshness,
    get_recent_game_summaries,
    get_today_game_summaries,
)
from app.db.session import get_db
from app.schemas.markets import ChatRequest, ChatResponse, GameDetail, GameSummary
from app.services.llm import LLMError, ask_market_copilot

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat_with_market_copilot(request: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    try:
        games = get_today_game_summaries(db)
        if not games:
            games = get_recent_game_summaries(db)
        if request.sport_key:
            games = [game for game in games if game.sport_key == request.sport_key]
        selected_game = get_game_detail(db, request.game_id) if request.game_id else None
        freshness = get_odds_freshness(db)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail="Could not load market context for chat.") from exc

    context = {
        "odds_freshness": freshness.model_dump(mode="json"),
        "games": [_game_context(game) for game in games[:5]],
        "selected_game": _detail_context(selected_game) if selected_game else None,
    }

    try:
        answer, model = ask_market_copilot(request.message, context)
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return ChatResponse(answer=answer, model=model, context_games=len(games[:5]))


def _game_context(game: GameSummary) -> dict:
    return {
        "id": game.id,
        "matchup": f"{game.away_team.name} at {game.home_team.name}",
        "start": game.commence_time.isoformat(),
        "opportunity_score": game.opportunity_score,
        "opportunity_reasons": game.opportunity_reasons[:3],
        "volatility_score": game.volatility_score,
        "book_disagreement_score": game.book_disagreement_score,
        "price_alerts": [alert.model_dump(mode="json") for alert in game.price_alerts[:2]],
        "signals": [signal.model_dump(mode="json") for signal in game.signals[:3]],
        "best_prices": [price.model_dump(mode="json") for price in game.best_prices[:6]],
        "no_vig_moneyline": [row.model_dump(mode="json") for row in game.no_vig_moneyline[:2]],
    }


def _detail_context(detail: GameDetail) -> dict:
    return {
        **_game_context(detail),
        "movement_alerts": [alert.model_dump(mode="json") for alert in detail.movement_alerts[:4]],
        "latest_book_table": [line.model_dump(mode="json") for line in detail.book_table[:12]],
    }
