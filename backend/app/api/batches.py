"""
API endpoints for batch operations.
"""
import io
from typing import List, Optional
from uuid import UUID

import pandas as pd
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import BatchStatus
from app.core.logging import get_logger
from app.db.base import get_db
from app.models import BatchJob, CaseJob
from app.schemas import (
    BatchJobResponse,
    BatchStatistics,
    BatchUploadResponse,
    CaseJobListResponse,
    CaseJobResponse,
    ManualBatchCreateRequest,
    ManualCaseEntry,
)
from app.utils.citation_parser import get_citation_parser
from app.utils.party_names import get_party_handler

logger = get_logger(__name__)
router = APIRouter(prefix="/batches", tags=["batches"])


@router.post(
    "",
    response_model=BatchUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload CSV/Excel with cases",
)
async def create_batch(
    file: UploadFile = File(..., description="CSV or Excel file with columns: party_name, citation, notes (optional)"),
    auto_download_exact_matches: bool = Form(default=True),
    user_id: Optional[str] = Form(default=None),
    db: AsyncSession = Depends(get_db),
) -> BatchUploadResponse:
    """
    Upload a CSV or Excel file containing case information.
    
    Required columns:
    - party_name: Party names (e.g., "Smith v Jones")
    - citation: Case citation (e.g., "[2020] HKCFI 123")
    - notes: Optional notes (optional column)
    
    Returns batch_id for tracking progress.
    """
    logger.info(
        "batch_upload_started",
        filename=file.filename,
        user_id=user_id,
        auto_download=auto_download_exact_matches,
    )
    
    # Validate file type
    content_type = file.content_type or ""
    filename = file.filename or ""
    
    is_csv = filename.endswith(".csv") or "csv" in content_type
    is_excel = filename.endswith((".xlsx", ".xls")) or "excel" in content_type or "spreadsheet" in content_type
    
    if not (is_csv or is_excel):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be CSV or Excel (.xlsx, .xls)",
        )
    
    try:
        # Read file content
        contents = await file.read()
        
        # Parse file
        if is_csv:
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))
        
        # Validate required columns
        df.columns = df.columns.str.lower().str.strip()
        
        if "party_name" not in df.columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required column: 'party_name'",
            )
        
        # Create batch job
        batch = BatchJob(
            status=BatchStatus.PENDING,
            total_cases=len(df),
            user_id=user_id,
            auto_download_exact_matches=auto_download_exact_matches,
        )
        db.add(batch)
        await db.flush()  # Get batch ID
        
        # Create case jobs
        citation_parser = get_citation_parser()
        party_handler = get_party_handler()
        
        for _, row in df.iterrows():
            party_names = str(row.get("party_name", "")).strip()
            citation = str(row.get("citation", "")).strip() if pd.notna(row.get("citation")) else None
            notes = str(row.get("notes", "")).strip() if pd.notna(row.get("notes")) else None
            
            if not party_names:
                continue
            
            # Parse citation
            parsed_citation = citation_parser.parse(citation) if citation else None
            
            # Generate party name variations
            party_variations = party_handler.generate_variations(party_names)
            
            case_job = CaseJob(
                batch_id=batch.id,
                party_names_raw=party_names,
                party_names_normalized={
                    "full": party_variations.full,
                    "abbreviated": party_variations.abbreviated,
                    "variations": party_variations.variations,
                },
                citation_raw=citation,
                citation_normalized=parsed_citation.normalized if parsed_citation else None,
                year_extracted=parsed_citation.year if parsed_citation else None,
                jurisdiction=parsed_citation.jurisdiction if parsed_citation else None,
            )
            db.add(case_job)
        
        await db.commit()
        
        logger.info(
            "batch_upload_completed",
            batch_id=str(batch.id),
            total_cases=batch.total_cases,
        )
        
        return BatchUploadResponse(
            batch_id=batch.id,
            total_cases=batch.total_cases,
            message=f"Batch created successfully with {batch.total_cases} cases",
        )
        
    except pd.errors.EmptyDataError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty",
        )
    except pd.errors.ParserError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse file: {str(e)}",
        )
    except Exception as e:
        logger.error("batch_upload_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process file: {str(e)}",
        )


@router.post(
    "/manual",
    response_model=BatchUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create batch from manually entered cases",
)
async def create_manual_batch(
    request: ManualBatchCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> BatchUploadResponse:
    """
    Create a batch from manually entered case information.
    
    This endpoint allows users to enter case information directly via the frontend
    without needing to upload a CSV/Excel file.
    
    Each case requires:
    - party_name: Party names (e.g., "Smith v Jones")
    - citation: Case citation (optional, e.g., "[2020] HKCFI 123")
    - notes: Optional notes
    
    Maximum 100 cases per batch.
    """
    logger.info(
        "manual_batch_creation_started",
        case_count=len(request.cases),
        user_id=request.user_id,
        auto_download=request.auto_download_exact_matches,
    )
    
    try:
        # Create batch job
        batch = BatchJob(
            status=BatchStatus.PENDING,
            total_cases=len(request.cases),
            user_id=request.user_id,
            auto_download_exact_matches=request.auto_download_exact_matches,
        )
        db.add(batch)
        await db.flush()  # Get batch ID
        
        # Create case jobs
        citation_parser = get_citation_parser()
        party_handler = get_party_handler()
        
        for case_entry in request.cases:
            party_names = case_entry.party_name.strip()
            citation = case_entry.citation.strip() if case_entry.citation else None
            
            if not party_names:
                continue
            
            # Parse citation
            parsed_citation = citation_parser.parse(citation) if citation else None
            
            # Generate party name variations
            party_variations = party_handler.generate_variations(party_names)
            
            case_job = CaseJob(
                batch_id=batch.id,
                party_names_raw=party_names,
                party_names_normalized={
                    "full": party_variations.full,
                    "abbreviated": party_variations.abbreviated,
                    "variations": party_variations.variations,
                },
                citation_raw=citation,
                citation_normalized=parsed_citation.normalized if parsed_citation else None,
                year_extracted=parsed_citation.year if parsed_citation else None,
                jurisdiction=parsed_citation.jurisdiction if parsed_citation else None,
            )
            db.add(case_job)
        
        await db.commit()
        
        logger.info(
            "manual_batch_creation_completed",
            batch_id=str(batch.id),
            total_cases=batch.total_cases,
        )
        
        return BatchUploadResponse(
            batch_id=batch.id,
            total_cases=batch.total_cases,
            message=f"Batch created successfully with {batch.total_cases} cases",
        )
        
    except Exception as e:
        logger.error("manual_batch_creation_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create batch: {str(e)}",
        )


@router.get(
    "/{batch_id}",
    response_model=BatchJobResponse,
    summary="Get batch status and statistics",
)
async def get_batch(
    batch_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> BatchJobResponse:
    """Get batch details including statistics."""
    result = await db.execute(
        select(BatchJob).where(BatchJob.id == batch_id)
    )
    batch = result.scalar_one_or_none()
    
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch {batch_id} not found",
        )
    
    return BatchJobResponse(
        id=batch.id,
        status=batch.status,
        created_at=batch.created_at,
        completed_at=batch.completed_at,
        total_cases=batch.total_cases,
        user_id=batch.user_id,
        auto_download_exact_matches=batch.auto_download_exact_matches,
        completed_cases_count=batch.completed_cases_count,
        error_cases_count=batch.error_cases_count,
        civil_procedure_blocked_count=batch.civil_procedure_blocked_count,
        pending_cases_count=batch.total_cases - batch.completed_cases_count - batch.error_cases_count,
    )


@router.get(
    "/{batch_id}/statistics",
    response_model=BatchStatistics,
    summary="Get detailed batch statistics",
)
async def get_batch_statistics(
    batch_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> BatchStatistics:
    """Get detailed statistics for a batch."""
    result = await db.execute(
        select(BatchJob).where(BatchJob.id == batch_id)
    )
    batch = result.scalar_one_or_none()
    
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch {batch_id} not found",
        )
    
    # Count by status
    completed = sum(1 for c in batch.cases if c.status.value == "completed")
    errors = sum(1 for c in batch.cases if c.status.value == "error")
    ambiguous = sum(1 for c in batch.cases if c.status.value == "ambiguous")
    civil_blocked = sum(1 for c in batch.cases if c.status.value == "civil_procedure_blocked")
    awaiting = sum(1 for c in batch.cases if c.status.value == "awaiting_selection")
    pending = batch.total_cases - completed - errors
    
    progress = (completed / batch.total_cases * 100) if batch.total_cases > 0 else 0
    
    return BatchStatistics(
        batch_id=batch.id,
        status=batch.status,
        total_cases=batch.total_cases,
        completed=completed,
        pending=pending,
        errors=errors,
        ambiguous=ambiguous,
        civil_procedure_blocked=civil_blocked,
        awaiting_selection=awaiting,
        progress_percentage=round(progress, 2),
    )


@router.get(
    "/{batch_id}/cases",
    response_model=CaseJobListResponse,
    summary="List all cases in batch with filtering",
)
async def list_batch_cases(
    batch_id: UUID,
    status: Optional[str] = Query(default=None, description="Filter by status"),
    confidence: Optional[str] = Query(default=None, description="Filter by confidence level"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
) -> CaseJobListResponse:
    """List all cases in a batch with optional filtering."""
    # Verify batch exists
    batch_result = await db.execute(
        select(BatchJob).where(BatchJob.id == batch_id)
    )
    batch = batch_result.scalar_one_or_none()
    
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch {batch_id} not found",
        )
    
    # Build query
    query = select(CaseJob).where(CaseJob.batch_id == batch_id)
    
    if status:
        query = query.where(CaseJob.status == status)
    
    if confidence:
        query = query.where(CaseJob.confidence_level == confidence)
    
    # Count total
    count_result = await db.execute(
        select(CaseJob).where(CaseJob.batch_id == batch_id)
    )
    total = len(count_result.scalars().all())
    
    # Get paginated results
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    cases = result.scalars().all()
    
    return CaseJobListResponse(
        items=[CaseJobResponse.model_validate(c) for c in cases],
        total=total,
    )
