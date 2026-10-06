from fastapi import APIRouter, HTTPException, Query, status
from app.models.schemas import LeaderboardResponse, PlayerEntry
from app.services.leaderboard_service import get_leaderboard_service

router = APIRouter(prefix="/leaderboard", tags=["Leaderboard"])

@router.get("/{dimension}", response_model=LeaderboardResponse)
def get_dimension_leaderboard(
    dimension: str,
    view: str = Query("absolute", pattern="^(absolute|improvement)$"),
    region: str = Query(None),
    industry: str = Query(None),
    size_band: str = Query(None),
    limit: int = Query(10, ge=1, le=100),
):
    valid_dims = {"global", "industry", "region", "size"}
    if dimension not in valid_dims:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid dimension {dimension}. Allowed: {sorted(valid_dims)}",
        )
    service = get_leaderboard_service()
    entries, total = service.get_top_players(limit=limit)
    return LeaderboardResponse(
        dimension=dimension,
        view=view,
        total_players=total,
        limit=limit,
        entries=entries,
    )
