from fastapi import APIRouter

from app.schemas.markets import IngestOddsRequest, IngestOddsResponse
from app.services.normalizer import normalize_odds_api_snapshot

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
