"""
Pydantic schemas for crawler session operations.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, SecretStr

from app.core.constants import SessionStatus


class SessionBase(BaseModel):
    """Base session schema."""
    model_config = ConfigDict(from_attributes=True)


class SessionCreate(BaseModel):
    """Schema for creating a new crawler session (login)."""
    username: str = Field(..., min_length=1)
    password: SecretStr = Field(..., min_length=1)
    totp_code: Optional[str] = Field(default=None, pattern=r"^\d{6}$")


class SessionResponse(SessionBase):
    """Schema for session response."""
    id: UUID
    status: SessionStatus
    started_at: datetime
    last_used: datetime
    cases_processed: int


class SessionHealthResponse(BaseModel):
    """Schema for session health check."""
    session_id: UUID
    status: SessionStatus
    is_valid: bool
    message: str
    cases_processed: int


class SessionListResponse(BaseModel):
    """Schema for list of sessions."""
    items: list[SessionResponse]
    total: int
