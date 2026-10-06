from datetime import datetime
from typing import List

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.award_repository import find_award, find_awards, save_award
from app.db import SessionLocal
from app.models import UserProfile
from app.streak import update_streak
from app.user_repository import find_user, save_user


async def get_session():
    async with SessionLocal() as session:
        yield session


app = FastAPI(
    title="CyBreach Pod Gamma API Gateway",
    version="1.0.0",
    description="Track 2 API and Endpoint Gateway",
)

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


class AchievementCheckPayload(BaseModel):
    type: str
    key: str
    tenant_id: str
    evidence_ref: str | None = None

    @field_validator("evidence_ref")
    @classmethod
    def validate_evidence_ref(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        parts = value.split(":")

        valid_mod2 = (
            len(parts) == 4
            and parts[0] == "mod2"
            and all(parts[1:])
        )

        valid_mod2_verdict = (
            len(parts) == 3
            and parts[0] == "mod2"
            and parts[1] == "verdict"
            and parts[2]
        )

        valid_mod3 = (
            len(parts) == 4
            and parts[0] == "mod3"
            and all(parts[1:])
        )

        if not (
            valid_mod2
            or valid_mod2_verdict
            or valid_mod3
        ):
            raise ValueError(
                "evidence_ref must use a valid mod2 or mod3 format"
            )

        return value


class StreakVerificationPayload(BaseModel):
    previous_login_timestamp: str
    current_login_timestamp: str
    active_streak: int = Field(ge=0)
    user_id: str = "api-user"
    tenant_id: str = "default"


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


@app.post("/api/v1/analytics")
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

    average_score = sum(
        item.security_score for item in metrics
    ) / len(metrics)

    return {
        "status": "processed",
        "records_processed": len(metrics),
        "average_security_score": round(average_score, 2),
        "metrics": [item.model_dump() for item in metrics],
    }


@app.post("/achievement/check")
async def check_achievement(
    payload: AchievementCheckPayload,
    session: AsyncSession = Depends(get_session),
):
    badge_id = payload.key

    existing_award = await find_award(
        session,
        badge_id,
        payload.tenant_id,
    )

    if existing_award is not None:
        return {
            "status": "already_awarded",
            "award_id": existing_award.award_id,
            "badge_id": existing_award.badge_id,
            "tenant_id": existing_award.tenant_id,
            "awarded_at": existing_award.awarded_at,
            "evidence_ref": existing_award.evidence_ref,
        }

    award = await save_award(
        session,
        badge_id,
        payload.tenant_id,
        payload.evidence_ref,
    )

    return {
        "status": "awarded",
        "award_id": award.award_id,
        "badge_id": award.badge_id,
        "tenant_id": award.tenant_id,
        "awarded_at": award.awarded_at,
        "evidence_ref": award.evidence_ref,
    }


@app.post("/api/v1/streaks")
async def verify_streak(
    payload: StreakVerificationPayload,
    session: AsyncSession = Depends(get_session),
):
    try:
        previous_login = datetime.fromisoformat(
            payload.previous_login_timestamp.replace("Z", "+00:00")
        )

        current_login = datetime.fromisoformat(
            payload.current_login_timestamp.replace("Z", "+00:00")
        )

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid timestamp format",
        )

    persisted_user = await find_user(
        session,
        payload.user_id,
        payload.tenant_id,
    )

    if persisted_user is None:
        user = UserProfile(
            user_id=payload.user_id,
            tenant_id=payload.tenant_id,
            current_streak=payload.active_streak,
            last_completion_time=previous_login,
            verified_activity_time=previous_login,
        )

    else:
        user = UserProfile(
            user_id=persisted_user.user_id,
            tenant_id=persisted_user.tenant_id,
            current_streak=persisted_user.current_streak,
            last_completion_time=persisted_user.last_completion_time,
            verified_activity_time=persisted_user.verified_activity_time,
        )

    updated_user = update_streak(
        user,
        current_login,
    )

    await save_user(
        session,
        user_id=updated_user.user_id,
        tenant_id=updated_user.tenant_id,
        current_streak=updated_user.current_streak,
        last_completion_time=updated_user.last_completion_time,
        verified_activity_time=updated_user.verified_activity_time,
    )

    return {
        "status": "processed",
        "previous_active_streak": payload.active_streak,
        "verified_streak": updated_user.current_streak,
        "last_completion_time": updated_user.last_completion_time,
        "verified_activity_time": updated_user.verified_activity_time,
    }


@app.get("/user/{user_id}/streak")
async def get_user_streak(
    user_id: str,
    tenant_id: str = "default",
    session: AsyncSession = Depends(get_session),
):
    user = await find_user(
        session,
        user_id,
        tenant_id,
    )

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    return {
        "user_id": user.user_id,
        "tenant_id": user.tenant_id,
        "current_streak": user.current_streak,
        "last_completion_time": user.last_completion_time,
        "verified_activity_time": user.verified_activity_time,
    }


@app.get("/user/{user_id}/badges")
async def get_user_badges(
    user_id: str,
    tenant_id: str = "default",
    session: AsyncSession = Depends(get_session),
):
    awards = await find_awards(
        session,
        tenant_id,
    )

    return {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "badges": [
            {
                "award_id": award.award_id,
                "badge_id": award.badge_id,
                "awarded_at": award.awarded_at,
                "evidence_ref": award.evidence_ref,
            }
            for award in awards
        ],
    }