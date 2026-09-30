from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import numpy as np
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.core.rate_limiter import check_rate_limit
from app.api.benchmark import router as benchmark_router
from app.models import UserProfile
from app.streak import update_streak
from app.badges import award_milestone_badge


app = FastAPI(
    title="CyBreach Pod Gamma API Gateway",
    version="1.0.0",
    description="Track 2 API and Endpoint Gateway",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(benchmark_router)

USERS: Dict[str, UserProfile] = {
    "user_1": UserProfile(
        user_id="user_1",
        current_streak=0,
        last_completion_time=None,
        verified_activity_time=None,
        badges=[]
    )
}

SYNTHETIC_PROFILES = [
    {"client_id": f"client_{i}", "security_score": 50 + (i * 2)}
    for i in range(15)
]

class ScoreInputItem(BaseModel):
    client_id: str
    security_score: float

class StreamAnalyticsPayload(BaseModel):
    metrics: Optional[List[ScoreInputItem]] = None

class StreakVerificationPayload(BaseModel):
    previous_login_timestamp: str
    current_login_timestamp: str
    active_streak: int

class ActivityPayload(BaseModel):
    user_id: str
    activity_type: str = Field(..., description="Type of cyber breach scenario or lab completed")
    completed_at: datetime = Field(default_factory=datetime.utcnow)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "gamma-api-gateway",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/activity/verify")
async def verify_activity(payload: ActivityPayload):
    user = USERS.get(payload.user_id)
    if user is None:
        user = UserProfile(
            user_id=payload.user_id,
            current_streak=0,
            last_completion_time=None,
            verified_activity_time=None,
            badges=[]
        )
        USERS[payload.user_id] = user

    streak_updated = update_streak(user, payload.completed_at)
    new_badges = award_milestone_badge(user)

    return {
        "status": "success",
        "user_id": user.user_id,
        "streak_updated": streak_updated,
        "current_streak": user.current_streak,
        "last_completion_time": user.last_completion_time,
        "verified_activity_time": user.verified_activity_time,
        "badges": user.badges,
        "new_badges_awarded": new_badges
    }

@app.get("/user/{user_id}/streak")
async def get_user_streak(user_id: str):
    user = USERS.get(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "user_id": user.user_id,
        "current_streak": user.current_streak,
        "last_completion_time": user.last_completion_time,
        "verified_activity_time": user.verified_activity_time,
    }

@app.get("/user/{user_id}/badges")
async def get_user_badges(user_id: str):
    user = USERS.get(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    award_milestone_badge(user)
    return {
        "user_id": user.user_id,
        "current_streak": user.current_streak,
        "badges": user.badges,
    }

@app.post(
    "/api/v1/analytics",
    dependencies=[Depends(check_rate_limit)],
)
async def analytics(payload: StreamAnalyticsPayload):
    metrics = payload.metrics

    if not metrics:
        metrics = [
            ScoreInputItem(
                client_id=profile["client_id"],
                security_score=profile["security_score"],
            )
            for profile in SYNTHETIC_PROFILES
        ]

    # PG-27: Minimum cohort size / anonymity threshold
    if len(metrics) < 10:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cohort size < 10 violates anonymity threshold",
        )

    # PG-26: Differential Privacy
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