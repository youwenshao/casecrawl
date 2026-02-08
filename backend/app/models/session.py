"""
Crawler session model for tracking Westlaw authentication sessions.
"""
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from sqlalchemy import DateTime, Enum, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import SessionStatus
from app.db.base import Base


class CrawlerSession(Base):
    """Track Westlaw authentication sessions."""
    
    __tablename__ = "crawler_sessions"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus, name="session_status"),
        default=SessionStatus.ACTIVE,
        nullable=False
    )
    
    # Encrypted session storage
    cookies: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Encrypted session storage"
    )
    
    # Session metadata
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    last_used: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    cases_processed: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    
    # Credentials reference (encrypted at rest)
    credentials_key: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Reference to encrypted credentials"
    )
    
    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    def __repr__(self) -> str:
        return f"<CrawlerSession(id={self.id}, status={self.status}, cases={self.cases_processed})>"
    
    def touch(self) -> None:
        """Update last_used timestamp."""
        self.last_used = datetime.now(timezone.utc)
    
    def increment_cases(self) -> None:
        """Increment the cases processed counter."""
        self.cases_processed += 1
        self.touch()
