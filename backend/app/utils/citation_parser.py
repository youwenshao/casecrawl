"""
Citation Parser - Critical component for parsing and normalizing legal citations.

Supports HK and UK citation formats with fuzzy matching capabilities.
"""
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

from app.core.constants import CITATION_PATTERNS, Jurisdiction


@dataclass
class ParsedCitation:
    """Represents a parsed legal citation."""
    raw: str
    year: int
    reporter: str
    volume: Optional[int]
    page: Optional[int]
    jurisdiction: Jurisdiction
    normalized: str
    
    def __repr__(self) -> str:
        return f"ParsedCitation({self.normalized})"


class CitationParser:
    """
    Parser for legal citations following HK and UK formats.
    
    Supports formats like:
    - [2020] HKCFI 123
    - [2019] 1 WLR 456
    - [2018] UKSC 15
    """
    
    # HK reporters
    HK_REPORTERS = {
        "HKCFI", "HKCA", "HKCFA", "HKCUHC", "HKEC", "HKDC", "HKLT", "HKMagC"
    }
    
    # UK reporters
    UK_REPORTERS = {
        "UKSC", "UKHL", "EWCA", "EWHC", "EWFC", "EWCC", 
        "CSIH", "CSOH", "NICA", "NIHC"
    }
    
    # Law Reports
    LAW_REPORTS = {"WLR", "QB", "AC", "Ch", "Fam", "TLR", "HKLRD"}
    ALL_ER_VARIATIONS = {"All ER", "All ER (D)", "All ER (Comm)", "All ER (EC)"}
    
    def __init__(self):
        """Initialize the citation parser with compiled regex patterns."""
        self.patterns = {
            "HK": re.compile(CITATION_PATTERNS["HK"], re.IGNORECASE),
            "UK": re.compile(CITATION_PATTERNS["UK"], re.IGNORECASE),
            "LawReports": re.compile(CITATION_PATTERNS["LawReports"], re.IGNORECASE),
        }
    
    def normalize(self, citation: str) -> str:
        """
        Normalize a citation by:
        - Removing all periods from reporter abbreviations
        - Standardizing spaces
        - Converting to uppercase
        """
        if not citation:
            return ""
        
        # Remove periods from reporter abbreviations
        normalized = citation.replace(".", "")
        
        # Standardize spaces (collapse multiple spaces to single)
        normalized = " ".join(normalized.split())
        
        # Standardize ampersand
        normalized = normalized.replace("&", "and")
        
        return normalized.strip().upper()
    
    def parse(self, citation: str) -> Optional[ParsedCitation]:
        """
        Parse a citation string and return structured data.
        
        Args:
            citation: Raw citation string
            
        Returns:
            ParsedCitation object or None if parsing fails
        """
        if not citation or not citation.strip():
            return None
        
        normalized = self.normalize(citation)
        
        # Try HK pattern first
        match = self.patterns["HK"].match(normalized)
        if match:
            year = int(match.group(1))
            reporter = match.group(2).upper()
            volume = None
            page = int(match.group(3))
            jurisdiction = Jurisdiction.HK
            
            return ParsedCitation(
                raw=citation,
                year=year,
                reporter=reporter,
                volume=volume,
                page=page,
                jurisdiction=jurisdiction,
                normalized=f"[{year}] {reporter} {page}"
            )
        
        # Try UK pattern
        match = self.patterns["UK"].match(normalized)
        if match:
            year = int(match.group(1))
            reporter = match.group(2).upper()
            volume = None
            page = int(match.group(3))
            jurisdiction = Jurisdiction.UK
            
            return ParsedCitation(
                raw=citation,
                year=year,
                reporter=reporter,
                volume=volume,
                page=page,
                jurisdiction=jurisdiction,
                normalized=f"[{year}] {reporter} {page}"
            )
        
        # Try Law Reports pattern (has volume)
        match = self.patterns["LawReports"].match(normalized)
        if match:
            year = int(match.group(1))
            volume = int(match.group(2))
            reporter = match.group(3).upper()
            page = int(match.group(4))
            
            # Determine jurisdiction based on reporter
            if reporter in ["HKLRD"]:
                jurisdiction = Jurisdiction.HK
            elif reporter in ["WLR", "QB", "AC", "Ch", "Fam", "TLR"]:
                jurisdiction = Jurisdiction.UK
            else:
                jurisdiction = Jurisdiction.UNKNOWN
            
            return ParsedCitation(
                raw=citation,
                year=year,
                reporter=reporter,
                volume=volume,
                page=page,
                jurisdiction=jurisdiction,
                normalized=f"[{year}] {volume} {reporter} {page}"
            )
        
        # Try to extract year as fallback
        year_match = re.search(r"\[(\d{4})\]", normalized)
        if year_match:
            year = int(year_match.group(1))
            return ParsedCitation(
                raw=citation,
                year=year,
                reporter="UNKNOWN",
                volume=None,
                page=None,
                jurisdiction=Jurisdiction.UNKNOWN,
                normalized=normalized
            )
        
        return None
    
    def extract_year(self, citation: str) -> Optional[int]:
        """Extract just the year from a citation."""
        parsed = self.parse(citation)
        return parsed.year if parsed else None
    
    def compare_citations(
        self, 
        user_citation: str, 
        westlaw_citation: str
    ) -> Tuple[str, float]:
        """
        Compare user citation with Westlaw citation.
        
        Returns:
            Tuple of (match_type, similarity_score)
            match_type: "exact", "similar_volume", "year_match_only", "none"
        """
        user_parsed = self.parse(user_citation)
        westlaw_parsed = self.parse(westlaw_citation)
        
        if not user_parsed or not westlaw_parsed:
            return ("none", 0.0)
        
        # Exact match
        if user_parsed.normalized == westlaw_parsed.normalized:
            return ("exact", 1.0)
        
        # Normalize both for comparison
        user_norm = self.normalize(user_citation)
        westlaw_norm = self.normalize(westlaw_citation)
        
        if user_norm == westlaw_norm:
            return ("exact", 1.0)
        
        # Check year match
        if user_parsed.year != westlaw_parsed.year:
            # Year differs by 1
            if abs(user_parsed.year - westlaw_parsed.year) == 1:
                return ("year_match_only", 0.3)
            return ("none", 0.0)
        
        # Same year, check reporter
        if user_parsed.reporter != westlaw_parsed.reporter:
            return ("year_match_only", 0.5)
        
        # Same year and reporter, check volume tolerance
        if user_parsed.volume is not None and westlaw_parsed.volume is not None:
            if abs(user_parsed.volume - westlaw_parsed.volume) <= 1:
                return ("similar_volume", 0.8)
        
        # Same year and reporter, different page/volume
        return ("year_match_only", 0.6)
    
    def find_in_where_reported(
        self,
        user_citation: str,
        where_reported: List[str]
    ) -> Tuple[Optional[str], str, float]:
        """
        Find user citation match in Westlaw's 'Where Reported' list.
        
        Args:
            user_citation: The citation provided by user
            where_reported: List of citations from Westlaw
            
        Returns:
            Tuple of (matched_citation, match_type, similarity_score)
        """
        best_match = None
        best_type = "none"
        best_score = 0.0
        
        for citation in where_reported:
            match_type, score = self.compare_citations(user_citation, citation)
            
            if score > best_score:
                best_score = score
                best_type = match_type
                best_match = citation
                
            if match_type == "exact":
                break
        
        return (best_match, best_type, best_score)


# Singleton instance
_citation_parser: Optional[CitationParser] = None


def get_citation_parser() -> CitationParser:
    """Get singleton citation parser instance."""
    global _citation_parser
    if _citation_parser is None:
        _citation_parser = CitationParser()
    return _citation_parser
