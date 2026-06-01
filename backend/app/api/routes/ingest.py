from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.repository import persist_normalized_odds, persist_player_context
from app.db.session import get_db
from app.schemas.markets import IngestOddsRequest, IngestOddsResponse, IngestPlayerContextResponse
from app.services.normalizer import (
    normalize_odds_api_snapshot,
    normalize_sportsdataio_mlb_game_odds,
    normalize_sportsdataio_mlb_injuries,
    normalize_sportsdataio_mlb_news,
)
from app.services.odds_api import fetch_mlb_odds
from app.services.sportsdataio import fetch_mlb_game_odds_by_date, fetch_mlb_injured_players, fetch_mlb_news

router = APIRouter(prefix="/ingest", tags=["ingestion"])


@router.post("/odds", response_model=IngestOddsResponse)
def ingest_odds_snapshot(request: IngestOddsRequest) -> IngestOddsResponse:
    normalized_rows = normalize_odds_api_snapshot(request.payload, request.snapshot_time)
    game_ids = {row["external_game_id"] for row in normalized_rows if row.get("external_game_id")}

    return IngestOddsResponse(
        accepted=True,
        source=request.source,
        games_seen=len(game_ids),
        snapshots_normalized=len(normalized_rows),
        message="Snapshot normalized. Database persistence will be wired in the next backend milestone.",
    )


@router.post("/sportsdataio/mlb", response_model=IngestOddsResponse)
def ingest_sportsdataio_mlb_odds(
    game_date: date | None = None,
    db: Session = Depends(get_db),
) -> IngestOddsResponse:
    target_date = game_date or date.today()
    payload = fetch_mlb_game_odds_by_date(target_date)
    normalized_rows = normalize_sportsdataio_mlb_game_odds(payload)
    counts = persist_normalized_odds(db, normalized_rows)
    games_seen = len({row["external_game_id"] for row in normalized_rows})

    return IngestOddsResponse(
        accepted=True,
        source="sportsdataio_mlb",
        games_seen=games_seen,
        snapshots_normalized=counts["odds_snapshots"],
        message=(
            f"Ingested MLB odds for {target_date.isoformat()}: "
            f"teams={counts['teams']}, sportsbooks={counts['sportsbooks']}, "
            f"games_created={counts['games']}, odds_snapshots_created={counts['odds_snapshots']}."
        ),
    )


@router.post("/odds-api/mlb", response_model=IngestOddsResponse)
def ingest_odds_api_mlb(db: Session = Depends(get_db)) -> IngestOddsResponse:
    response = fetch_mlb_odds()
    normalized_rows = normalize_odds_api_snapshot(response.payload)
    counts = persist_normalized_odds(db, normalized_rows)
    games_seen = len({row["external_game_id"] for row in normalized_rows})

    return IngestOddsResponse(
        accepted=True,
        source="the_odds_api_mlb",
        games_seen=games_seen,
        snapshots_normalized=counts["odds_snapshots"],
        message=(
            "Ingested The Odds API MLB odds: "
            f"games_created={counts['games']}, odds_snapshots_created={counts['odds_snapshots']}; "
            f"usage_last={response.usage.requests_last}, "
            f"usage_remaining={response.usage.requests_remaining}."
        ),
    )


@router.post("/sportsdataio/mlb-context", response_model=IngestPlayerContextResponse)
def ingest_sportsdataio_mlb_context(db: Session = Depends(get_db)) -> IngestPlayerContextResponse:
    injury_payload = fetch_mlb_injured_players()
    news_payload = fetch_mlb_news()
    injury_rows = normalize_sportsdataio_mlb_injuries(injury_payload)
    news_rows = normalize_sportsdataio_mlb_news(news_payload)
    counts = persist_player_context(db, injury_rows, news_rows)

    return IngestPlayerContextResponse(
        accepted=True,
        source="sportsdataio_mlb",
        injuries_seen=len(injury_rows),
        injuries_upserted=counts["injuries"],
        news_seen=len(news_rows),
        news_upserted=counts["news"],
        message=(
            "Ingested MLB player context: "
            f"injuries_seen={len(injury_rows)}, injuries_created={counts['injuries']}, "
            f"news_seen={len(news_rows)}, news_created={counts['news']}."
        ),
    )
