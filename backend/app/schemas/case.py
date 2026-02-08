"""
Pydantic schemas for case operations.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import (
    CaseStatus,
    CitationMatchType,
    ConfidenceLevel,
    Jurisdiction,
    SearchStrategy,
)


class CaseJobBase(BaseModel):
    """Base case job schema."""
    model_config = ConfigDict(from_attributes=True)


class CaseJobCreate(BaseModel):
    """Schema for creating a new case job."""
    party_names_raw: str = Field(..., min_length=1)
    citation_raw: Optional[str] = None
    notes: Optional[str] = None


class CaseJobResponse(CaseJobBase):
    """Schema for case job response."""
    id: UUID
    batch_id: UUID
    party_names_raw: str
    party_names_normalized: Optional[Dict[str, Any]]
    citation_raw: Optional[str]
    citation_normalized: Optional[str]
    year_extracted: Optional[int]
    jurisdiction: Jurisdiction
    search_strategy_used: Optional[SearchStrategy]
    status: CaseStatus
    confidence_level: Optional[ConfidenceLevel]
    civil_procedure_flag: bool
    volume_tolerance_applied: bool
    file_path: Optional[str]
    file_name: Optional[str]
    westlaw_url: Optional[str]
    created_at: datetime
    updated_at: datetime


class CaseJobListResponse(BaseModel):
    """Schema for list of case jobs."""
    items: List[CaseJobResponse]
    total: int


class CaseJobFilter(BaseModel):
    """Filter options for case jobs."""
    status: Optional[CaseStatus] = None
    confidence: Optional[ConfidenceLevel] = None
    year: Optional[int] = None


class CaseSelectRequest(BaseModel):
    """Schema for selecting a case from ambiguous results."""
    result_id: UUID
    override_civil_procedure: bool = Field(
        default=False,
        description="For logging only - civil procedure override is strictly forbidden"
    )


class CaseSelectResponse(BaseModel):
    """Schema for case selection response."""
    case_id: UUID
    selected_result_id: UUID
    status: CaseStatus
    message: str


class CaseForceManualRequest(BaseModel):
    """Schema for marking case for manual review."""
    reason: Optional[str] = None


class SearchResultItem(BaseModel):
    """Schema for a search result item."""
    id: UUID
    westlaw_citation: str
    where_reported: List[str]
    principal_subject: Optional[str]
    is_civil_procedure: bool
    parties_display: str
    decision_date: Optional[str]
    year: int
    available_documents: Dict[str, bool]
    citation_match_type: CitationMatchType
    similarity_score: float
    westlaw_url: Optional[str]
    
    # Display helpers
    citation_match_badge: Optional[str] = None  # "exact", "volume_tolerance", "no_match"


class CaseSearchResultsResponse(BaseModel):
    """Schema for case search results."""
    case_id: UUID
    party_names_raw: str
    citation_raw: Optional[str]
    user_citation_normalized: Optional[str]
    results: List[SearchResultItem]
    total_results: int
    has_exact_match: bool
    has_civil_procedure: bool


class CaseDownloadResponse(BaseModel):
    """Schema for case download response."""
    case_id: UUID
    file_name: str
    download_url: str
