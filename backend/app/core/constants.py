"""
Application constants and enums.
"""
from enum import Enum


class BatchStatus(str, Enum):
    """Batch job status values."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class CaseStatus(str, Enum):
    """Case job status values."""
    PENDING = "pending"
    SEARCHING = "searching"
    AMBIGUOUS = "ambiguous"
    AWAITING_SELECTION = "awaiting_selection"
    CIVIL_PROCEDURE_BLOCKED = "civil_procedure_blocked"
    CITATION_MISMATCH = "citation_mismatch"
    ANALYSIS_ONLY = "analysis_only"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    ERROR = "error"


class ConfidenceLevel(str, Enum):
    """Confidence level for case matches."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SearchStrategy(str, Enum):
    """Search strategy used for case lookup."""
    EXACT = "exact"
    YEAR_RANGE = "year_range"
    PARTY_ONLY = "party_only"
    FAILED = "failed"


class Jurisdiction(str, Enum):
    """Case jurisdiction."""
    HK = "HK"
    UK = "UK"
    UNKNOWN = "UNKNOWN"


class CitationMatchType(str, Enum):
    """Type of citation match found."""
    EXACT = "exact"
    SIMILAR_VOLUME = "similar_volume"
    YEAR_MATCH_ONLY = "year_match_only"
    NONE = "none"


class SessionStatus(str, Enum):
    """Crawler session status."""
    ACTIVE = "active"
    EXPIRED = "expired"
    CAPTCHA_BLOCKED = "captcha_blocked"


# Citation regex patterns for parsing
CITATION_PATTERNS = {
    "HK": r"\[(\d{4})\]\s*(HKCFI|HKCA|HKCFA|HKCUHC|HKEC|HKDC|HKLT|HKMagC)\s*(\d+)",
    "UK": r"\[(\d{4})\]\s*(UKSC|UKHL|EWCA|EWHC|EWFC|EWCC|CSIH|CSOH|NICA|NIHC)\s*(\d+)",
    "LawReports": r"\[(\d{4})\]\s*(\d+)\s*(WLR|QB|AC|Ch|Fam|All ER|TLR|HKLRD)\s*(\d+)",
}

# Westlaw selectors (centralized configuration)
WESTLAW_SELECTORS = {
    "login": {
        "username_input": "input[name='username'], input[id='username']",
        "password_input": "input[name='password'], input[id='password']",
        "submit_button": "button[type='submit'], input[type='submit']",
        "totp_input": "input[name='totp'], input[id='totp']",
    },
    "search": {
        "search_box": "input[placeholder*='Search'], textarea[placeholder*='Search'], #search-input",
        "search_button": "button[type='submit'], button[aria-label*='Search']",
        "results_container": ".search-results, [data-testid='search-results']",
        "result_item": ".result-item, .search-result",
    },
    "document": {
        "pdf_link": "a.co_format_pdf, a[title='PDF'], a[href*='pdf']",
        "transcript_link": "a:has-text('Official Transcript'), a[title='Official Transcript']",
        "analysis_link": "a:has-text('Case Analysis'), a[title='Case Analysis']",
        "party_names": ".parties, .case-parties, [data-testid='parties']",
        "citation": ".citation, .case-citation, [data-testid='citation']",
        "where_reported": ".where-reported, [data-testid='where-reported']",
        "principal_subject": ".principal-subject, [data-testid='principal-subject']",
        "decision_date": ".decision-date, [data-testid='decision-date']",
    },
    "captcha": {
        "recaptcha_frame": "iframe[src*='recaptcha'], .g-recaptcha",
        "unusual_traffic": "text=unusual traffic, text=verify you're human",
    }
}

# Document type hierarchy for selection
DOCUMENT_HIERARCHY = [
    {"type": "PDF", "priority": 1, "selector": WESTLAW_SELECTORS["document"]["pdf_link"]},
    {"type": "Official Transcript", "priority": 2, "selector": WESTLAW_SELECTORS["document"]["transcript_link"]},
    {"type": "Case Analysis", "priority": 3, "selector": WESTLAW_SELECTORS["document"]["analysis_link"]},
]
