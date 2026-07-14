"""FastAPI route handlers for leaderboard operations."""
from __future__ import annotations

from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Query,
    #Request,
    status,
)

from app.db.redis_client import get_redis_metrics, is_redis_healthy
from app.exceptions import RedisUnavailableError
from app.models.schemas import (
    DeleteUserResponse,
    HealthResponse,
    IncrementRequest,
    IncrementResponse,
    LeaderboardResponse,
    MetricsResponse,
    RankResponse,
    ResetLeaderboardResponse,
    ScoreRequest,
    ScoreResponse,
)
#from app.rate_limit import limiter
#from app.security import verify_api_key
from app.services.leaderboard_service import (
    LeaderboardService,
    get_leaderboard_service,
)

router = APIRouter(tags=["Leaderboard"])

ServiceDep = Annotated[LeaderboardService, Depends(get_leaderboard_service)]

@router.post(
    "/score",
    response_model=ScoreResponse,
    status_code=status.HTTP_200_OK,
    summary="Create or update a player score",
    #dependencies=[Depends(verify_api_key)],
)
#@limiter.limit("20/minute")
def set_score(
    payload: ScoreRequest,
    service: ServiceDep,
) -> ScoreResponse:
    """
    Create or overwrite a player's score.
    """

    score = service.set_score(
        payload.username,
        payload.score,
    )

    return ScoreResponse(
        username=payload.username,
        score=score,
    )


@router.post(
    "/increment",
    response_model=IncrementResponse,
    status_code=status.HTTP_200_OK,
    summary="Atomically increment a player score",
    #dependencies=[Depends(verify_api_key)],
)
#@limiter.limit("20/minute")
def increment_score(
    payload: IncrementRequest,
    service: ServiceDep,
) -> IncrementResponse:
    """
    Increment a player's score atomically.
    """

    new_score = service.increment_score(
        payload.username,
        payload.increment,
    )

    return IncrementResponse(
        username=payload.username,
        score=new_score,
        increment=payload.increment,
    )


@router.get(
    "/leaderboard",
    response_model=LeaderboardResponse,
    summary="Get top N players",
)
def get_leaderboard(
    service: ServiceDep,
    limit: int = Query(default=10, ge=1, le=1000, description="Number of top players"),
) -> LeaderboardResponse:
    """Return the highest-scoring players ranked by score."""
    entries, total = service.get_top_players(limit)
    return LeaderboardResponse(
        total_players=total,
        limit=limit,
        entries=entries,
    )


@router.get(
    "/rank/{username}",
    response_model=RankResponse,
    summary="Get player rank and score",
)
def get_rank(username: str, service: ServiceDep) -> RankResponse:
    """Look up a player's current score and rank."""
    score, rank = service.get_rank(username.strip())
    return RankResponse(username=username.strip(), score=score, rank=rank)


@router.delete(
    "/user/{username}",
    response_model=DeleteUserResponse,
    summary="Remove a player",
    #dependencies=[Depends(verify_api_key)],
)
#@limiter.limit("10/minute")
def delete_user(
    username: str,
    service: ServiceDep,
) -> DeleteUserResponse:
    """
    Delete a player.
    """

    service.delete_user(username.strip())

    return DeleteUserResponse(
        username=username.strip(),
    )


@router.delete(
    "/leaderboard",
    response_model=ResetLeaderboardResponse,
    summary="Reset leaderboard",
    #dependencies=[Depends(verify_api_key)],
)
#@limiter.limit("5/minute")
def reset_leaderboard(
    service: ServiceDep,
) -> ResetLeaderboardResponse:
    """
    Reset the leaderboard.
    """

    service.reset_leaderboard()

    return ResetLeaderboardResponse()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service health check",
)
def health_check() -> HealthResponse:
    """Return application and Redis health status."""
    redis_ok = is_redis_healthy()
    return HealthResponse(
        status="healthy" if redis_ok else "degraded",
        redis="connected" if redis_ok else "disconnected",
        app="running",
    )


@router.get(
    "/metrics",
    response_model=MetricsResponse,
    summary="Redis server metrics",
)
def metrics() -> MetricsResponse:
    """Expose Redis INFO metrics for observability."""
    if not is_redis_healthy():
        raise RedisUnavailableError("Redis is not available for metrics collection")
    return MetricsResponse(metrics=get_redis_metrics())
