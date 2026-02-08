"""
Batch job model for tracking collections of case jobs.
"""
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional
from uuid import uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import BatchStatus
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.case import CaseJob


class BatchJob(Base):
    """Represents a batch of case crawling jobs."""
    
    __tablename__ = "batch_jobs"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    status: Mapped[BatchStatus] = mapped_column(
        Enum(BatchStatus, name="batch_status"),
        default=BatchStatus.PENDING,
        nullable=False,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    total_cases: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    auto_download_exact_matches: Mapped[bool] = mapped_column(
        default=True,
        nullable=False
    )
    
    # Relationships
    cases: Mapped[List["CaseJob"]] = relationship(
        "CaseJob",
        back_populates="batch",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<BatchJob(id={self.id}, status={self.status}, cases={self.total_cases})>"
    
    @property
    def completed_cases_count(self) -> int:
        """Count of completed cases in this batch."""
        return sum(1 for c in self.cases if c.status.value == "completed")
    
    @property
    def error_cases_count(self) -> int:
        """Count of cases with errors in this batch."""
        return sum(1 for c in self.cases if c.status.value == "error")
    
    @property
    def civil_procedure_blocked_count(self) -> int:
        """Count of civil procedure blocked cases."""
        return sum(1 for c in self.cases if c.status.value == "civil_procedure_blocked")
