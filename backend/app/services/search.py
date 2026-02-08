"""
Search service implementing the 4-step search strategy.

Step 1: Exact match with citation + party names
Step 2: Year range search with party names
Step 3: Party only search with date filter
Step 4: Fail if not found
"""
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import (
    CitationMatchType,
    CaseStatus,
    ConfidenceLevel,
    SearchStrategy,
)
from app.core.logging import get_logger
from app.models import CaseJob, SearchResultCache
from app.services.westlaw_client import WestlawClient
from app.utils.citation_parser import get_citation_parser
from app.utils.party_names import get_party_handler

logger = get_logger(__name__)


class SearchService:
    """
    Service for executing the 4-step search strategy on Westlaw.
    """
    
    def __init__(self, client: WestlawClient, db: AsyncSession):
        self.client = client
        self.db = db
        self.citation_parser = get_citation_parser()
        self.party_handler = get_party_handler()
    
    async def search_case(self, case_job: CaseJob) -> Tuple[SearchStrategy, List[Dict[str, Any]]]:
        """
        Execute the 4-step search strategy for a case.
        
        Returns:
            Tuple of (strategy_used, search_results)
        """
        logger.info(
            "search_started",
            case_id=str(case_job.id),
            parties=case_job.party_names_raw,
            citation=case_job.citation_raw,
        )
        
        # Step 1: Exact search with citation + party names
        results = await self._step1_exact_search(case_job)
        if results:
            logger.info("search_strategy_success", case_id=str(case_job.id), strategy="exact")
            return SearchStrategy.EXACT, results
        
        # Step 2: Year range search with party names
        results = await self._step2_year_range(case_job)
        if results:
            logger.info("search_strategy_success", case_id=str(case_job.id), strategy="year_range")
            return SearchStrategy.YEAR_RANGE, results
        
        # Step 3: Party only search with date filter
        results = await self._step3_party_only(case_job)
        if results:
            logger.info("search_strategy_success", case_id=str(case_job.id), strategy="party_only")
            return SearchStrategy.PARTY_ONLY, results
        
        # Step 4: Fail
        logger.warning("search_strategy_failed", case_id=str(case_job.id))
        return SearchStrategy.FAILED, []
    
    async def _step1_exact_search(self, case_job: CaseJob) -> List[Dict[str, Any]]:
        """
        Step 1: Exact search with citation + party names.
        
        Query template: {party_names} {exact_citation}
        """
        if not case_job.citation_raw:
            return []
        
        # Build query with party names and citation
        party_query = self.party_handler.build_westlaw_query(case_job.party_names_raw)
        citation_normalized = self.citation_parser.normalize(case_job.citation_raw)
        
        query = f"{party_query} {citation_normalized}"
        
        logger.debug("step1_exact_query", case_id=str(case_job.id), query=query)
        
        try:
            results = await self.client.search(query)
            
            # Filter for exact citation matches
            filtered_results = []
            for result in results:
                match_type, score = self._match_citation(
                    case_job.citation_raw,
                    result.get("citation", ""),
                    result.get("where_reported", [])
                )
                
                if match_type == CitationMatchType.EXACT:
                    result["citation_match_type"] = match_type.value
                    result["similarity_score"] = score
                    filtered_results.append(result)
            
            return filtered_results
            
        except Exception as e:
            logger.error("step1_search_error", case_id=str(case_job.id), error=str(e))
            return []
    
    async def _step2_year_range(self, case_job: CaseJob) -> List[Dict[str, Any]]:
        """
        Step 2: Year range search with party names.
        
        Query template: {party_names} [{year}]
        Year range: [-1, 0, 1] (year ± 1)
        """
        year = case_job.year_extracted
        if not year:
            return []
        
        party_query = self.party_handler.build_westlaw_query(case_job.party_names_raw)
        all_results = []
        
        # Try year range: year-1, year, year+1
        for year_offset in [-1, 0, 1]:
            query = f"{party_query} [{year + year_offset}]"
            
            logger.debug(
                "step2_year_query",
                case_id=str(case_job.id),
                query=query,
                year_offset=year_offset,
            )
            
            try:
                results = await self.client.search(query)
                
                # Filter results matching year
                for result in results:
                    result_year = self._extract_year_from_result(result)
                    if result_year and abs(result_year - year) <= 1:
                        match_type, score = self._match_citation(
                            case_job.citation_raw,
                            result.get("citation", ""),
                            result.get("where_reported", [])
                        )
                        result["citation_match_type"] = match_type.value
                        result["similarity_score"] = score
                        all_results.append(result)
                        
            except Exception as e:
                logger.error("step2_search_error", case_id=str(case_job.id), error=str(e))
                continue
        
        return all_results
    
    async def _step3_party_only(self, case_job: CaseJob) -> List[Dict[str, Any]]:
        """
        Step 3: Party only search with date filter.
        
        Query template: {party_names}
        Date filter: {year-1}-01-01 to {year+1}-12-31
        """
        year = case_job.year_extracted
        if not year:
            return []
        
        party_query = self.party_handler.build_westlaw_query(case_job.party_names_raw)
        
        # Add date filter if Westlaw supports it
        date_from = year - 1
        date_to = year + 1
        query = f"{party_query} after:{date_from}-01-01 before:{date_to}-12-31"
        
        logger.debug("step3_party_query", case_id=str(case_job.id), query=query)
        
        try:
            results = await self.client.search(query)
            
            # Score results
            for result in results:
                match_type, score = self._match_citation(
                    case_job.citation_raw,
                    result.get("citation", ""),
                    result.get("where_reported", [])
                )
                result["citation_match_type"] = match_type.value
                result["similarity_score"] = score * 0.8  # Lower confidence for party-only
            
            return results
            
        except Exception as e:
            logger.error("step3_search_error", case_id=str(case_job.id), error=str(e))
            return []
    
    def _match_citation(
        self,
        user_citation: Optional[str],
        westlaw_citation: str,
        where_reported: List[str]
    ) -> Tuple[CitationMatchType, float]:
        """
        Match user citation against Westlaw result.
        
        Returns:
            Tuple of (match_type, similarity_score)
        """
        if not user_citation:
            return CitationMatchType.YEAR_MATCH_ONLY, 0.3
        
        # Check against primary citation
        match_type, score = self.citation_parser.compare_citations(
            user_citation,
            westlaw_citation
        )
        
        if match_type == "exact":
            return CitationMatchType.EXACT, score
        
        # Check against Where Reported
        best_match, best_type, best_score = self.citation_parser.find_in_where_reported(
            user_citation,
            where_reported
        )
        
        if best_type == "exact":
            return CitationMatchType.EXACT, best_score
        elif best_type == "similar_volume":
            return CitationMatchType.SIMILAR_VOLUME, best_score
        elif best_type == "year_match_only":
            return CitationMatchType.YEAR_MATCH_ONLY, best_score
        
        return CitationMatchType.NONE, 0.0
    
    def _extract_year_from_result(self, result: Dict[str, Any]) -> Optional[int]:
        """Extract year from search result."""
        # Try decision date first
        date_str = result.get("date", "")
        if date_str:
            try:
                import re
                year_match = re.search(r"\b(19|20)\d{2}\b", date_str)
                if year_match:
                    return int(year_match.group(0))
            except Exception:
                pass
        
        # Try citation
        citation = result.get("citation", "")
        if citation:
            parsed = self.citation_parser.parse(citation)
            if parsed:
                return parsed.year
        
        return None
    
    async def cache_search_results(
        self,
        case_job_id: UUID,
        results: List[Dict[str, Any]]
    ) -> List[SearchResultCache]:
        """
        Cache search results to database.
        
        Returns list of cached result records.
        """
        cached_results = []
        
        for result in results:
            # Check for civil procedure
            principal_subject = result.get("principal_subject", "")
            is_civil_procedure = "civil procedure" in principal_subject.lower()
            
            # Parse available documents
            available_docs = result.get("available_documents", {})
            if not available_docs:
                available_docs = {
                    "pdf": bool(result.get("pdf_link")),
                    "transcript": bool(result.get("transcript_link")),
                    "analysis": bool(result.get("analysis_link")),
                }
            
            cached = SearchResultCache(
                case_job_id=case_job_id,
                westlaw_citation=result.get("citation", ""),
                where_reported=result.get("where_reported", []),
                principal_subject=principal_subject,
                is_civil_procedure=is_civil_procedure,
                parties_display=result.get("parties", ""),
                decision_date=result.get("decision_date"),
                year=result.get("year", 0) or self._extract_year_from_result(result) or 0,
                available_documents=available_docs,
                citation_match_type=CitationMatchType(
                    result.get("citation_match_type", "none")
                ),
                similarity_score=result.get("similarity_score", 0.0),
                westlaw_url=result.get("url"),
            )
            
            self.db.add(cached)
            cached_results.append(cached)
        
        await self.db.commit()
        return cached_results
    
    async def determine_case_status(
        self,
        case_job: CaseJob,
        results: List[SearchResultCache]
    ) -> CaseStatus:
        """
        Determine case status based on search results.
        
        Returns appropriate status for the case.
        """
        if not results:
            return CaseStatus.ERROR
        
        # Check for exact match with downloadable document
        exact_matches = [r for r in results if r.citation_match_type == CitationMatchType.EXACT]
        
        if exact_matches:
            best_match = max(exact_matches, key=lambda r: r.similarity_score)
            
            # Check civil procedure
            if best_match.is_civil_procedure:
                return CaseStatus.CIVIL_PROCEDURE_BLOCKED
            
            # Check if document is available
            if not best_match.has_downloadable_document:
                return CaseStatus.ANALYSIS_ONLY
            
            # Single exact match - can auto-download
            if len(exact_matches) == 1:
                case_job.selected_result_id = best_match.id
                return CaseStatus.DOWNLOADING
        
        # Check for any civil procedure cases
        civil_cases = [r for r in results if r.is_civil_procedure]
        
        # Multiple results or no exact match - need human disambiguation
        case_job.search_results = [
            {
                "id": str(r.id),
                "citation": r.westlaw_citation,
                "match_type": r.citation_match_type.value,
                "score": r.similarity_score,
            }
            for r in results
        ]
        
        return CaseStatus.AMBIGUOUS
