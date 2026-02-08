"""
Celery tasks for async case processing.
"""
import asyncio
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import UUID

from celery import shared_task
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import BatchStatus, CaseStatus
from app.core.logging import get_logger
from app.db.base import AsyncSessionLocal
from app.models import BatchJob, CaseJob, CrawlerSession
from app.services.search import SearchService
from app.services.westlaw_client import WestlawClient

logger = get_logger(__name__)


async def process_case_async(case_id: str, session_id: Optional[str] = None) -> Dict[str, Any]:
    """Async function to process a single case."""
    async with AsyncSessionLocal() as db:
        try:
            # Get case job
            from sqlalchemy import select
            result = await db.execute(
                select(CaseJob).where(CaseJob.id == UUID(case_id))
            )
            case = result.scalar_one_or_none()
            
            if not case:
                logger.error("case_not_found", case_id=case_id)
                return {"status": "error", "message": "Case not found"}
            
            # Update status
            case.status = CaseStatus.SEARCHING
            await db.commit()
            
            # Get or create Westlaw session
            westlaw_session = None
            if session_id:
                result = await db.execute(
                    select(CrawlerSession).where(CrawlerSession.id == UUID(session_id))
                )
                westlaw_session = result.scalar_one_or_none()
            
            # Perform search
            async with WestlawClient() as client:
                # Login if needed
                if westlaw_session and westlaw_session.cookies:
                    # TODO: Restore session from cookies
                    pass
                else:
                    # New login required - will be handled by frontend
                    case.status = CaseStatus.AWAITING_SELECTION
                    case.error_log = "Westlaw login required"
                    await db.commit()
                    return {"status": "awaiting_login", "case_id": case_id}
                
                # Create search service
                search_service = SearchService(client, db)
                
                # Execute search strategy
                strategy, results = await search_service.search_case(case)
                
                # Update case with strategy used
                case.search_strategy_used = strategy
                
                if strategy.value == "failed":
                    case.status = CaseStatus.ERROR
                    case.error_log = "Case not found after exhaustive search"
                    await db.commit()
                    return {"status": "error", "message": "Case not found"}
                
                # Cache results
                cached_results = await search_service.cache_search_results(
                    case.id,
                    results
                )
                
                # Determine status
                new_status = await search_service.determine_case_status(case, cached_results)
                case.status = new_status
                
                await db.commit()
                
                # Send WebSocket notification
                await notify_case_update(case)
                
                return {
                    "status": new_status.value,
                    "case_id": case_id,
                    "strategy": strategy.value,
                    "results_count": len(results),
                }
                
        except Exception as e:
            logger.error("process_case_error", case_id=case_id, error=str(e))
            
            # Update case with error
            result = await db.execute(
                select(CaseJob).where(CaseJob.id == UUID(case_id))
            )
            case = result.scalar_one_or_none()
            if case:
                case.status = CaseStatus.ERROR
                case.error_log = str(e)
                await db.commit()
            
            return {"status": "error", "message": str(e)}


@shared_task(bind=True, max_retries=3)
def process_case(self, case_id: str, session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Celery task to process a single case.
    
    This task:
    1. Logs into Westlaw (if needed)
    2. Executes the 4-step search strategy
    3. Caches results
    4. Determines next status (download/ambiguous/error)
    """
    try:
        result = asyncio.run(process_case_async(case_id, session_id))
        return result
    except Exception as exc:
        logger.error("task_failed", task_id=self.request.id, error=str(exc))
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


async def process_batch_async(batch_id: str, session_id: Optional[str] = None) -> Dict[str, Any]:
    """Async function to process an entire batch."""
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        
        # Get batch
        result = await db.execute(
            select(BatchJob).where(BatchJob.id == UUID(batch_id))
        )
        batch = result.scalar_one_or_none()
        
        if not batch:
            return {"status": "error", "message": "Batch not found"}
        
        # Update status
        batch.status = BatchStatus.PROCESSING
        await db.commit()
        
        # Queue tasks for all pending cases
        for case in batch.cases:
            if case.status == CaseStatus.PENDING:
                process_case.delay(str(case.id), session_id)
        
        return {
            "status": "processing",
            "batch_id": batch_id,
            "total_cases": batch.total_cases,
        }


@shared_task
def process_batch(batch_id: str, session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Celery task to process a batch of cases.
    
    Queues individual case processing tasks.
    """
    return asyncio.run(process_batch_async(batch_id, session_id))


@shared_task
def download_case(case_id: str, result_id: str, session_id: str) -> Dict[str, Any]:
    """
    Celery task to download a case document.
    """
    async def download_async():
        async with AsyncSessionLocal() as db:
            from sqlalchemy import select
            
            # Get case and result
            result = await db.execute(
                select(CaseJob).where(CaseJob.id == UUID(case_id))
            )
            case = result.scalar_one_or_none()
            
            if not case:
                return {"status": "error", "message": "Case not found"}
            
            result = await db.execute(
                select(SearchResultCache).where(SearchResultCache.id == UUID(result_id))
            )
            search_result = result.scalar_one_or_none()
            
            if not search_result:
                return {"status": "error", "message": "Search result not found"}
            
            # Download document
            settings = get_settings()
            download_dir = Path(settings.download_dir) / str(case.batch_id)
            download_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            citation_clean = case.citation_normalized.replace("[", "").replace("]", "").replace(" ", "_") if case.citation_normalized else "unknown"
            parties_short = case.party_names_raw[:50].replace(" ", "_") if case.party_names_raw else "unknown"
            filename = f"{case.id}_{parties_short}_{citation_clean}.pdf"
            
            file_path = download_dir / filename
            
            async with WestlawClient() as client:
                # TODO: Restore session
                success = await client.download_document(
                    search_result.westlaw_url,
                    file_path
                )
                
                if success:
                    case.status = CaseStatus.COMPLETED
                    case.file_path = str(file_path)
                    case.file_name = filename
                    await db.commit()
                    
                    await notify_case_update(case)
                    
                    return {"status": "completed", "case_id": case_id, "file": str(file_path)}
                else:
                    case.status = CaseStatus.ERROR
                    case.error_log = "Download failed"
                    await db.commit()
                    return {"status": "error", "message": "Download failed"}
    
    return asyncio.run(download_async())


# WebSocket notification helper
async def notify_case_update(case: CaseJob) -> None:
    """Send WebSocket notification for case update."""
    try:
        import aiohttp
        
        notification = {
            "type": "case_update",
            "case_id": str(case.id),
            "batch_id": str(case.batch_id),
            "status": case.status.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        # This would connect to the WebSocket manager
        # For now, just log it
        logger.info("websocket_notification", notification=notification)
        
    except Exception as e:
        logger.error("websocket_notification_error", error=str(e))


@shared_task
def cleanup_old_files() -> Dict[str, Any]:
    """Clean up files older than retention period."""
    settings = get_settings()
    retention_days = settings.file_retention_days
    
    from datetime import datetime, timedelta
    cutoff = datetime.now() - timedelta(days=retention_days)
    
    download_dir = Path(settings.download_dir)
    cleaned = 0
    
    for file_path in download_dir.rglob("*"):
        if file_path.is_file():
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            if mtime < cutoff:
                file_path.unlink()
                cleaned += 1
    
    logger.info("cleanup_old_files", cleaned=cleaned, retention_days=retention_days)
    return {"cleaned": cleaned}


@shared_task
def cleanup_expired_sessions() -> Dict[str, Any]:
    """Clean up expired crawler sessions."""
    async def cleanup_async():
        async with AsyncSessionLocal() as db:
            from sqlalchemy import select, update
            from datetime import datetime, timezone, timedelta
            
            # Mark sessions inactive after 8 hours
            cutoff = datetime.now(timezone.utc) - timedelta(hours=8)
            
            stmt = (
                update(CrawlerSession)
                .where(
                    CrawlerSession.status == "active",
                    CrawlerSession.last_used < cutoff
                )
                .values(status="expired")
            )
            
            result = await db.execute(stmt)
            await db.commit()
            
            logger.info("cleanup_expired_sessions", expired=result.rowcount)
            return {"expired": result.rowcount}
    
    return asyncio.run(cleanup_async())
