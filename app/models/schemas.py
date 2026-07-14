"""Pydantic request and response schemas for the leaderboard API."""

from pydantic import BaseModel, Field, field_validator


class ScoreRequest(BaseModel):
    """Request body for setting a player score."""

    username: str = Field(..., min_length=1, max_length=128, examples=["player_one"])
    score: float = Field(..., ge=0, examples=[1500.0])

    @field_validator("username")
    @classmethod
    def strip_username(cls, value: str) -> str:
        """Normalize username by stripping whitespace."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Username cannot be empty or whitespace")
        return cleaned


class IncrementRequest(BaseModel):
    """Request body for atomically incrementing a player score."""

    username: str = Field(..., min_length=1, max_length=128, examples=["player_one"])
    increment: float = Field(..., gt=0, examples=[10.0])

    @field_validator("username")
    @classmethod
    def strip_username(cls, value: str) -> str:
        """Normalize username by stripping whitespace."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Username cannot be empty or whitespace")
        return cleaned


class PlayerEntry(BaseModel):
    """A single entry in the leaderboard."""

    rank: int = Field(..., ge=1)
    username: str
    score: float


class ScoreResponse(BaseModel):
    """Response after setting or updating a score."""

    success: bool = True
    username: str
    score: float
    message: str = "Score updated successfully"


class IncrementResponse(BaseModel):
    """Response after incrementing a score."""

    success: bool = True
    username: str
    score: float
    increment: float
    message: str = "Score incremented successfully"


class LeaderboardResponse(BaseModel):
    """Top-N leaderboard response."""

    success: bool = True
    total_players: int
    limit: int
    entries: list[PlayerEntry]


class RankResponse(BaseModel):
    """Player rank and score lookup response."""

    success: bool = True
    username: str
    score: float
    rank: int = Field(..., ge=1)


class DeleteUserResponse(BaseModel):
    """Response after deleting a player."""

    success: bool = True
    username: str
    message: str = "User removed from leaderboard"


class ResetLeaderboardResponse(BaseModel):
    """Response after clearing the entire leaderboard."""

    success: bool = True
    message: str = "Leaderboard cleared successfully"


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    redis: str
    app: str


class MetricsResponse(BaseModel):
    """Redis metrics response."""

    success: bool = True
    metrics: dict[str, str | int | float]


class ErrorResponse(BaseModel):
    """Structured error response."""

    success: bool = False
    error: str
    detail: str | None = None
