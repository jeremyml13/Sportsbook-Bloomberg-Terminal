from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.repository import _injury_read, get_mlb_game_context, get_mlb_injuries, get_mlb_news
from app.db.session import get_db
from app.schemas.markets import GamePlayerContextRead, PlayerInjuryRead, PlayerNewsRead

router = APIRouter(prefix="/context", tags=["context"])


@router.get("/mlb/injuries", response_model=list[PlayerInjuryRead])
def read_mlb_injuries(
    team: str | None = None,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> list[PlayerInjuryRead]:
    return [_injury_read(injury) for injury in get_mlb_injuries(db, team=team, limit=limit)]


@router.get("/mlb/news", response_model=list[PlayerNewsRead])
def read_mlb_news(
    team: str | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
) -> list[PlayerNewsRead]:
    return get_mlb_news(db, team=team, limit=limit)


@router.get("/mlb/games/{game_id}", response_model=GamePlayerContextRead)
def read_mlb_game_context(
    game_id: str,
    limit: int = 12,
    db: Session = Depends(get_db),
) -> GamePlayerContextRead:
    context = get_mlb_game_context(db, game_id, limit=limit)
    if context is None:
        raise HTTPException(status_code=404, detail="Game context not found")

    return context
