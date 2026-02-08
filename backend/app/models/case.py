"""
Case job model for individual case crawling jobs.
"""
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import (
    CaseStatus,
    CitationMatchType,
    ConfidenceLevel,
    Jurisdiction,
    SearchStrategy,
)
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.batch import BatchJob
    from app.models.search_result import SearchResultCache


class CaseJob(Base):
    """Represents an individual case crawling job."""
    
    __tablename__ = "case_jobs"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    batch_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("batch_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Input data
    party_names_raw: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Original input party names"
    )
    party_names_normalized: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Array of variations [full, abbreviated]"
    )
    citation_raw: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    citation_normalized: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    year_extracted: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        index=True
    )
    jurisdiction: Mapped[Jurisdiction] = mapped_column(
        Enum(Jurisdiction, name="jurisdiction"),
        default=Jurisdiction.UNKNOWN,
        nullable=False
    )
    
    # Search metadata
    search_strategy_used: Mapped[Optional[SearchStrategy]] = mapped_column(
        Enum(SearchStrategy, name="search_strategy"),
        nullable=True
    )
    status: Mapped[CaseStatus] = mapped_column(
        Enum(CaseStatus, name="case_status"),
        default=CaseStatus.PENDING,
        nullable=False,
        index=True
    )
    confidence_level: Mapped[Optional[ConfidenceLevel]] = mapped_column(
        Enum(ConfidenceLevel, name="confidence_level"),
        nullable=True
    )
    search_results: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Array of potential matches with metadata"
    )
    selected_result_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("search_results_cache.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Flags
    civil_procedure_flag: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    volume_tolerance_applied: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="True if volume differed from user citation"
    )
    
    # File information
    file_path: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    file_name: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Generated from user citation + parties"
    )
    
    # Error tracking
    error_log: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    westlaw_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Direct link to case for manual review"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    # Relationships
    batch: Mapped["BatchJob"] = relationship("BatchJob", back_populates="cases")
    search_result_cache: Mapped[Optional["SearchResultCache"]] = relationship(
        "SearchResultCache",
        foreign_keys=[selected_result_id]
    )
    cached_results: Mapped[List["SearchResultCache"]] = relationship(
        "SearchResultCache",
        back_populates="case_job",
        foreign_keys="SearchResultCache.case_job_id",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<CaseJob(id={self.id}, status={self.status}, citation={self.citation_raw})>"
