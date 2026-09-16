from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.api.benchmark import router as benchmark_router
from app.models import UserProfile
from app.streak import update_streak
from app.badges import award_milestone_badge

app = FastAPI(
    title="CyBreach Pod Gamma API Gateway",
    version="1.0.0",
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