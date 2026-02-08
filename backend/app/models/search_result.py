"""
Search result cache model for temporary storage of Westlaw search results.
"""
from datetime import date
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import Boolean, Date, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import CitationMatchType
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.case import CaseJob


class SearchResultCache(Base):
    """Temporary storage of Westlaw search results for disambiguation."""
    
    __tablename__ = "search_results_cache"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    case_job_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("case_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Westlaw case information
    westlaw_citation: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    where_reported: Mapped[List[str]] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
        comment="Array of all citations"
    )
    principal_subject: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    is_civil_procedure: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    parties_display: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    decision_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True
    )
    year: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    
    # Available documents
    available_documents: Mapped[Dict[str, bool]] = mapped_column(
        JSONB,
        default=lambda: {"pdf": False, "transcript": False, "analysis": False},
        nullable=False
    )
    
    # Match quality
    citation_match_type: Mapped[CitationMatchType] = mapped_column(
        Enum(CitationMatchType, name="citation_match_type"),
        default=CitationMatchType.NONE,
        nullable=False
    )
    similarity_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False
    )
    
    # Westlaw metadata
    westlaw_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    # Relationship
    case_job: Mapped["CaseJob"] = relationship(
        "CaseJob",
        foreign_keys="CaseJob.selected_result_id",
        back_populates="search_result_cache"
    )
    
    def __repr__(self) -> str:
        return f"<SearchResultCache(id={self.id}, citation={self.westlaw_citation}, match={self.citation_match_type})>"
    
    @property
    def has_downloadable_document(self) -> bool:
        """Check if this result has a downloadable document (not just analysis)."""
        return self.available_documents.get("pdf", False) or \
               self.available_documents.get("transcript", False)
