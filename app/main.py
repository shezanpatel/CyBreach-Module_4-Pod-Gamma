"""FastAPI application entry point with lifespan management."""
# ==========================================================
# SECURITY FEATURE (TEMPORARILY DISABLED)
#
# Reason:
# API authentication and rate limiting will be enabled after
# the API module is merged by the teammate.
#
# To enable:
# 1. Uncomment the import.
# 2. Uncomment the dependency/decorator.
# ==========================================================
from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

#import app
from app.api.leaderboard import router as leaderboard_router
from app.config import get_settings
from app.db.redis_client import close_redis, init_redis
from app.exceptions import (
    InvalidScoreError,
    LeaderboardError,
    NegativeScoreError,
    RedisTimeoutError,
    RedisUnavailableError,
    UserNotFoundError,
)
#from slowapi.errors import RateLimitExceeded
#from slowapi.middleware import SlowAPIMiddleware

#from app.rate_limit import limiter

from app.models.schemas import ErrorResponse
from app.utils.logger import get_logger, setup_logging

settings = get_settings()
logger = get_logger("main")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Manage startup and graceful shutdown lifecycle."""
    setup_logging(settings.log_level)  # type: ignore[arg-type]
    logger.info("Starting %s | env=%s", settings.app_name, settings.app_env)

    try:
        init_redis(settings)
    except RedisUnavailableError as exc:
        logger.error("Startup Redis connection failed: %s", exc.message)

    yield

    logger.info("Shutting down %s", settings.app_name)
    close_redis()
    logger.info("Graceful shutdown complete")


def create_app() -> FastAPI:
    """Application factory for production and test usage."""
    app = FastAPI(
        title=settings.app_name,
        description=(
            "High-performance leaderboard microservice powered by Redis Sorted Sets. "
            "Supports real-time score updates and O(log N) rank lookups."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    #app.state.limiter = limiter
    #app.add_middleware(SlowAPIMiddleware)

    app.add_middleware(
        CORSMiddleware,
        #allow_origins=settings.allowed_origins,
        #allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
# =====================================================
# SECURITY MIDDLEWARE (Disabled for teammate integration)
# Uncomment after API authentication is merged.
# =====================================================
    # @app.middleware("http")
    # async def security_headers(request, call_next):
    #     response = await call_next(request)

    #     response.headers["X-Content-Type-Options"] = "nosniff"
    #     response.headers["X-Frame-Options"] = "DENY"
    #     response.headers["Referrer-Policy"] = "strict-origin"
    #     response.headers["Permissions-Policy"] = "geolocation=()"
    #     response.headers["Content-Security-Policy"] = "default-src 'self'"

    #     return response

    _register_exception_handlers(app)
    app.include_router(leaderboard_router)

    return app


def _register_exception_handlers(app: FastAPI) -> None:
    """Map domain exceptions to structured JSON error responses."""

    def _build_response(status_code: int, exc: LeaderboardError) -> JSONResponse:
        body = ErrorResponse(error=exc.message, detail=str(exc.details) if exc.details else None)
        logger.error("Request failed | error=%s status=%s", exc.message, status_code)
        return JSONResponse(status_code=status_code, content=body.model_dump())

    @app.exception_handler(UserNotFoundError)
    async def user_not_found_handler(_request: Request, exc: UserNotFoundError) -> JSONResponse:
        return _build_response(status.HTTP_404_NOT_FOUND, exc)

    @app.exception_handler(InvalidScoreError)
    async def invalid_score_handler(_request: Request, exc: InvalidScoreError) -> JSONResponse:
        return _build_response(status.HTTP_400_BAD_REQUEST, exc)

    @app.exception_handler(NegativeScoreError)
    async def negative_score_handler(_request: Request, exc: NegativeScoreError) -> JSONResponse:
        return _build_response(status.HTTP_400_BAD_REQUEST, exc)

    @app.exception_handler(RedisTimeoutError)
    async def timeout_handler(_request: Request, exc: RedisTimeoutError) -> JSONResponse:
        return _build_response(status.HTTP_504_GATEWAY_TIMEOUT, exc)

    @app.exception_handler(RedisUnavailableError)
    async def redis_unavailable_handler(
        _request: Request,
        exc: RedisUnavailableError,
    ) -> JSONResponse:
        return _build_response(status.HTTP_503_SERVICE_UNAVAILABLE, exc)

    @app.exception_handler(LeaderboardError)
    async def generic_leaderboard_handler(
        _request: Request,
        exc: LeaderboardError,
    ) -> JSONResponse:
        return _build_response(status.HTTP_500_INTERNAL_SERVER_ERROR, exc)


app = create_app()
