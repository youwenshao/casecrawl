"""
Pydantic schemas for batch operations.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import BatchStatus


class BatchJobBase(BaseModel):
    """Base batch job schema."""
    model_config = ConfigDict(from_attributes=True)


class BatchJobCreate(BaseModel):
    """Schema for creating a new batch job."""
    auto_download_exact_matches: bool = Field(default=True)
    user_id: Optional[str] = None


class BatchJobResponse(BatchJobBase):
    """Schema for batch job response."""
    id: UUID
    status: BatchStatus
    created_at: datetime
    completed_at: Optional[datetime]
    total_cases: int
    user_id: Optional[str]
    auto_download_exact_matches: bool
    
    # Computed statistics
    completed_cases_count: int = 0
    error_cases_count: int = 0
    civil_procedure_blocked_count: int = 0
    pending_cases_count: int = 0


class BatchJobListResponse(BaseModel):
    """Schema for list of batch jobs."""
    items: List[BatchJobResponse]
    total: int


class BatchUploadResponse(BaseModel):
    """Schema for batch upload response."""
    batch_id: UUID
    total_cases: int
    message: str


class BatchStatistics(BaseModel):
    """Detailed batch statistics."""
    batch_id: UUID
    status: BatchStatus
    total_cases: int
    completed: int
    pending: int
    errors: int
    ambiguous: int
    civil_procedure_blocked: int
    awaiting_selection: int
    progress_percentage: float
