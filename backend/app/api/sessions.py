"""
API endpoints for crawler session operations.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import SessionStatus
from app.core.logging import get_logger
from app.db.base import get_db
from app.models import CrawlerSession
from app.schemas import SessionCreate, SessionHealthResponse, SessionListResponse, SessionResponse

logger = get_logger(__name__)
router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post(
    "",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initialize new Westlaw session (login)",
)
async def create_session(
    request: SessionCreate,
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    """
    Create a new Westlaw crawling session.
    
    This initiates a login to Westlaw and stores the session for subsequent requests.
    
    Note: Actual browser automation will be handled by Celery workers.
    This endpoint creates the session record and queues the login task.
    """
    # Create session record
    session = CrawlerSession(
        status=SessionStatus.ACTIVE,
        credentials_key=f"user:{request.username}",  # Reference only, actual creds handled securely
    )
    db.add(session)
    await db.commit()
    
    logger.info(
        "session_created",
        session_id=str(session.id),
        username=request.username,
    )
    
    # TODO: Queue Celery task for actual login
    
    return SessionResponse.model_validate(session)


@router.get(
    "",
    response_model=SessionListResponse,
    summary="List all crawler sessions",
)
async def list_sessions(
    status: Optional[SessionStatus] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
) -> SessionListResponse:
    """List all crawler sessions with optional filtering."""
    query = select(CrawlerSession)
    
    if status:
        query = query.where(CrawlerSession.status == status)
    
    # Count total
    count_result = await db.execute(select(CrawlerSession))
    total = len(count_result.scalars().all())
    
    # Get paginated results
    query = query.offset(skip).limit(limit).order_by(CrawlerSession.started_at.desc())
    result = await db.execute(query)
    sessions = result.scalars().all()
    
    return SessionListResponse(
        items=[SessionResponse.model_validate(s) for s in sessions],
        total=total,
    )


@router.get(
    "/{session_id}",
    response_model=SessionResponse,
    summary="Get session details",
)
async def get_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    """Get details of a specific crawler session."""
    result = await db.execute(
        select(CrawlerSession).where(CrawlerSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )
    
    return SessionResponse.model_validate(session)


@router.get(
    "/{session_id}/health",
    response_model=SessionHealthResponse,
    summary="Check if session still valid",
)
async def check_session_health(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> SessionHealthResponse:
    """
    Check if a crawler session is still valid.
    
    Returns health status and will trigger re-authentication if needed.
    """
    result = await db.execute(
        select(CrawlerSession).where(CrawlerSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )
    
    # Check session validity
    is_valid = session.status == SessionStatus.ACTIVE
    
    if is_valid:
        message = "Session is active and valid"
    elif session.status == SessionStatus.EXPIRED:
        message = "Session has expired, re-authentication required"
    elif session.status == SessionStatus.CAPTCHA_BLOCKED:
        message = "Session blocked by CAPTCHA, manual intervention required"
    else:
        message = f"Session status: {session.status.value}"
    
    return SessionHealthResponse(
        session_id=session.id,
        status=session.status,
        is_valid=is_valid,
        message=message,
        cases_processed=session.cases_processed,
    )


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Terminate a crawler session",
)
async def terminate_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Terminate (invalidate) a crawler session."""
    result = await db.execute(
        select(CrawlerSession).where(CrawlerSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )
    
    session.status = SessionStatus.EXPIRED
    await db.commit()
    
    logger.info("session_terminated", session_id=str(session_id))
