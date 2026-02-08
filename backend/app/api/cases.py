"""
API endpoints for case operations.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import CaseStatus
from app.core.logging import get_logger
from app.db.base import get_db
from app.models import CaseJob, SearchResultCache
from app.schemas import (
    CaseDownloadResponse,
    CaseForceManualRequest,
    CaseJobResponse,
    CaseSearchResultsResponse,
    CaseSelectRequest,
    CaseSelectResponse,
    SearchResultItem,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/cases", tags=["cases"])


@router.get(
    "/{case_id}",
    response_model=CaseJobResponse,
    summary="Get case details",
)
async def get_case(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> CaseJobResponse:
    """Get details of a specific case job."""
    result = await db.execute(
        select(CaseJob).where(CaseJob.id == case_id)
    )
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case {case_id} not found",
        )
    
    return CaseJobResponse.model_validate(case)


@router.get(
    "/{case_id}/search-results",
    response_model=CaseSearchResultsResponse,
    summary="Get ambiguous search results for human selection",
)
async def get_search_results(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> CaseSearchResultsResponse:
    """
    Get search results for a case that requires human disambiguation.
    
    Returns all potential matches found on Westlaw with match quality indicators.
    """
    result = await db.execute(
        select(CaseJob).where(CaseJob.id == case_id)
    )
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case {case_id} not found",
        )
    
    # Get cached search results
    cached_result = await db.execute(
        select(SearchResultCache).where(SearchResultCache.case_job_id == case_id)
    )
    cached_results = cached_result.scalars().all()
    
    # Build response items
    items = []
    has_exact = False
    has_civil = False
    
    for r in cached_results:
        # Determine badge
        badge = "no_match"
        if r.citation_match_type.value == "exact":
            badge = "exact"
            has_exact = True
        elif r.citation_match_type.value == "similar_volume":
            badge = "volume_tolerance"
        elif r.citation_match_type.value == "year_match_only":
            badge = "year_match"
        
        if r.is_civil_procedure:
            has_civil = True
        
        items.append(SearchResultItem(
            id=r.id,
            westlaw_citation=r.westlaw_citation,
            where_reported=r.where_reported,
            principal_subject=r.principal_subject,
            is_civil_procedure=r.is_civil_procedure,
            parties_display=r.parties_display,
            decision_date=r.decision_date.isoformat() if r.decision_date else None,
            year=r.year,
            available_documents=r.available_documents,
            citation_match_type=r.citation_match_type,
            similarity_score=r.similarity_score,
            westlaw_url=r.westlaw_url,
            citation_match_badge=badge,
        ))
    
    # Sort by similarity score (highest first)
    items.sort(key=lambda x: x.similarity_score, reverse=True)
    
    return CaseSearchResultsResponse(
        case_id=case.id,
        party_names_raw=case.party_names_raw,
        citation_raw=case.citation_raw,
        user_citation_normalized=case.citation_normalized,
        results=items,
        total_results=len(items),
        has_exact_match=has_exact,
        has_civil_procedure=has_civil,
    )


@router.post(
    "/{case_id}/select",
    response_model=CaseSelectResponse,
    summary="Human selects correct case from ambiguous results",
)
async def select_case_result(
    case_id: UUID,
    request: CaseSelectRequest,
    db: AsyncSession = Depends(get_db),
) -> CaseSelectResponse:
    """
    Select the correct case from ambiguous search results.
    
    Note: Civil Procedure override is strictly forbidden and will be logged but ignored.
    """
    result = await db.execute(
        select(CaseJob).where(CaseJob.id == case_id)
    )
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case {case_id} not found",
        )
    
    # Verify the result exists and belongs to this case
    cached_result = await db.execute(
        select(SearchResultCache).where(
            SearchResultCache.id == request.result_id,
            SearchResultCache.case_job_id == case_id,
        )
    )
    selected_result = cached_result.scalar_one_or_none()
    
    if not selected_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Search result {request.result_id} not found for case {case_id}",
        )
    
    # Check for civil procedure
    if selected_result.is_civil_procedure:
        # Log the attempt but don't allow override
        logger.warning(
            "civil_procedure_selection_attempt",
            case_id=str(case_id),
            result_id=str(request.result_id),
            override_requested=request.override_civil_procedure,
        )
        
        # Still update the selection, but status remains blocked
        case.selected_result_id = request.result_id
        case.status = CaseStatus.CIVIL_PROCEDURE_BLOCKED
        case.westlaw_url = selected_result.westlaw_url
        await db.commit()
        
        return CaseSelectResponse(
            case_id=case.id,
            selected_result_id=selected_result.id,
            status=CaseStatus.CIVIL_PROCEDURE_BLOCKED,
            message="Civil Procedure case detected. Manual Westlaw review required. Auto-download disabled.",
        )
    
    # Check if document is available
    if not selected_result.has_downloadable_document:
        case.selected_result_id = request.result_id
        case.status = CaseStatus.ANALYSIS_ONLY
        case.westlaw_url = selected_result.westlaw_url
        await db.commit()
        
        return CaseSelectResponse(
            case_id=case.id,
            selected_result_id=selected_result.id,
            status=CaseStatus.ANALYSIS_ONLY,
            message="Only Case Analysis document available. Manual review required.",
        )
    
    # Valid selection
    case.selected_result_id = request.result_id
    case.status = CaseStatus.DOWNLOADING
    case.westlaw_url = selected_result.westlaw_url
    case.volume_tolerance_applied = (selected_result.citation_match_type.value == "similar_volume")
    await db.commit()
    
    # TODO: Trigger download task via Celery
    logger.info(
        "case_selected_for_download",
        case_id=str(case_id),
        result_id=str(request.result_id),
    )
    
    return CaseSelectResponse(
        case_id=case.id,
        selected_result_id=selected_result.id,
        status=CaseStatus.DOWNLOADING,
        message="Case selected. Download will begin shortly.",
    )


@router.post(
    "/{case_id}/force-manual",
    response_model=CaseJobResponse,
    summary="Mark case for manual Westlaw review",
)
async def force_manual_review(
    case_id: UUID,
    request: CaseForceManualRequest,
    db: AsyncSession = Depends(get_db),
) -> CaseJobResponse:
    """
    Mark a case for manual review on Westlaw.
    
    Use this for cases that are blocked (Civil Procedure) or have other issues
    that require human intervention.
    """
    result = await db.execute(
        select(CaseJob).where(CaseJob.id == case_id)
    )
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case {case_id} not found",
        )
    
    old_status = case.status
    case.status = CaseStatus.AWAITING_SELECTION
    
    if request.reason:
        case.error_log = f"Manual review requested: {request.reason}"
    
    await db.commit()
    
    logger.info(
        "case_marked_manual_review",
        case_id=str(case_id),
        old_status=old_status.value if old_status else None,
        reason=request.reason,
    )
    
    return CaseJobResponse.model_validate(case)


@router.get(
    "/{case_id}/download",
    response_model=CaseDownloadResponse,
    summary="Download completed case file",
)
async def download_case(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> CaseDownloadResponse:
    """
    Get download information for a completed case.
    
    Returns a URL to download the case file.
    """
    result = await db.execute(
        select(CaseJob).where(CaseJob.id == case_id)
    )
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case {case_id} not found",
        )
    
    if case.status != CaseStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Case is not completed (current status: {case.status.value})",
        )
    
    if not case.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case file not found",
        )
    
    return CaseDownloadResponse(
        case_id=case.id,
        file_name=case.file_name or "case.pdf",
        download_url=f"/api/v1/files/download/{case_id}",
    )
