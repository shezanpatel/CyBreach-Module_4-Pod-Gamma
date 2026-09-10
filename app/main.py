from datetime import datetime
from typing import List

from fastapi import Depends
from app.core.rate_limiter import check_rate_limit

import numpy as np
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.api.benchmark import router as benchmark_router


app = FastAPI(
    title="CyBreach Pod Gamma API Gateway",
    version="1.0.0",
    description="Track 2 API and Endpoint Gateway",
)

app.include_router(benchmark_router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class ScoreInputItem(BaseModel):
    client_id: str = Field(min_length=3, max_length=50)
    security_score: float = Field(ge=0.0, le=100.0)


class StreamAnalyticsPayload(BaseModel):
    metrics: List[ScoreInputItem] = Field(default_factory=list)


class StreakVerificationPayload(BaseModel):
    previous_login_timestamp: str
    current_login_timestamp: str
    active_streak: int = Field(ge=0)


def seed_corporate_profiles() -> List[dict]:
    return [
        {
            "client_id": f"CORP-{index:03d}",
            "company_name": f"Synthetic Corporation {index:03d}",
            "security_score": float(50 + (index * 7) % 51),
        }
        for index in range(1, 51)
    ]


SYNTHETIC_PROFILES = seed_corporate_profiles()


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post(
    "/api/v1/analytics",
    dependencies=[Depends(check_rate_limit)],
)
async def analytics(payload: StreamAnalyticsPayload):
    metrics = payload.metrics

    # Use existing synthetic data only when no metrics
    # are supplied by the client.
    if not metrics:
        metrics = [
            ScoreInputItem(
                client_id=profile["client_id"],
                security_score=profile["security_score"],
            )
            for profile in SYNTHETIC_PROFILES
        ]

    # --------------------------------------------------------
    # PG-27: Minimum cohort size / anonymity threshold
    # --------------------------------------------------------
    if len(metrics) < 10:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cohort size < 10 violates anonymity threshold",
        )

    # --------------------------------------------------------
    # PG-26: Differential Privacy
    # --------------------------------------------------------
    scores = np.array(
        [item.security_score for item in metrics],
        dtype=float,
    )

    epsilon = 0.5
    sensitivity = 100.0 / len(metrics)
    scale = sensitivity / epsilon

    p25 = float(
        np.percentile(scores, 25)
        + np.random.laplace(0, scale)
    )

    p50 = float(
        np.percentile(scores, 50)
        + np.random.laplace(0, scale)
    )

    p75 = float(
        np.percentile(scores, 75)
        + np.random.laplace(0, scale)
    )

    return {
        "status": "processed",
        "records_processed": len(metrics),
        "differential_privacy": {
            "mechanism": "Laplace",
            "epsilon": epsilon,
            "percentiles": {
                "p25": round(p25, 2),
                "p50_median": round(p50, 2),
                "p75": round(p75, 2),
            },
        },
    }


@app.post("/api/v1/streaks")
async def verify_streak(payload: StreakVerificationPayload):
    try:
        previous_login = datetime.fromisoformat(
            payload.previous_login_timestamp.replace("Z", "+00:00")
        )

        current_login = datetime.fromisoformat(
            payload.current_login_timestamp.replace("Z", "+00:00")
        )

        elapsed_seconds = (
            current_login - previous_login
        ).total_seconds()

        elapsed_days = elapsed_seconds / 86400

        consecutive_login = 0 < elapsed_days <= 1.0

    except ValueError:
        consecutive_login = False
        elapsed_days = None

    verified_streak = (
        payload.active_streak + 1
        if consecutive_login
        else 0
    )

    return {
        "status": "processed",
        "consecutive_login": consecutive_login,
        "previous_active_streak": payload.active_streak,
        "verified_streak": verified_streak,
        "elapsed_days": elapsed_days,
    }
