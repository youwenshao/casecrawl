"""
Party name handling utilities following OSCOLA standards.
"""
import re
from dataclasses import dataclass
from typing import List, Optional, Set


@dataclass
class PartyNameVariations:
    """Variations of party names for search."""
    full: str
    abbreviated: str
    variations: List[str]


class PartyNameHandler:
    """
    Handle party name normalization and abbreviation following OSCOLA standards.
    
    OSCOLA abbreviation rules:
    - First letter of each word, except 'v' and 'and'
    - 'Regina v Smith' → 'R v S'
    - 'HSBC Bank Plc v Jones' → 'H v J'
    """
    
    # Words to skip in abbreviation
    SKIP_WORDS = {"v", "vs", "versus", "and", "&", "the", "of", "in", "for", "at", "by"}
    
    # Common party prefixes/suffixes to handle
    PREFIXES = {"the", "mr", "mrs", "ms", "dr", "prof", "sir"}
    SUFFIXES = {"plc", "ltd", "limited", "inc", "incorporated", "llp", "corp", "corporation"}
    
    def normalize(self, name: str) -> str:
        """
        Normalize party names by:
        - Removing extra whitespace
        - Standardizing 'v' vs 'vs' vs 'versus'
        - Converting 'and' to '&'
        """
        if not name:
            return ""
        
        normalized = name.strip()
        
        # Standardize v/vs/versus
        normalized = re.sub(
            r'\b(vs\.?|versus)\b', 
            'v', 
            normalized, 
            flags=re.IGNORECASE
        )
        
        # Standardize 'and' to '&' in some variations
        # (but keep both versions)
        
        # Remove extra whitespace
        normalized = " ".join(normalized.split())
        
        return normalized
    
    def abbreviate(self, name: str) -> str:
        """
        Create OSCOLA-style abbreviation of party names.
        
        Examples:
        - 'Smith v Jones' → 'S v J'
        - 'HSBC Bank Plc v Jones' → 'H v J'
        - 'Regina v Smith' → 'R v S'
        - 'The Attorney General v Smith' → 'A v S'
        """
        if not name:
            return ""
        
        normalized = self.normalize(name)
        
        # Split by 'v' (versus)
        parts = re.split(r'\s+v\s+', normalized, flags=re.IGNORECASE)
        
        abbreviated_parts = []
        for part in parts:
            words = part.strip().split()
            abbreviated_words = []
            
            for word in words:
                word_lower = word.lower().rstrip('.')
                
                # Skip common words
                if word_lower in self.SKIP_WORDS:
                    continue
                
                # Skip prefixes
                if word_lower in self.PREFIXES:
                    continue
                
                # Skip suffixes
                if word_lower in self.SUFFIXES:
                    continue
                
                # Take first letter
                if word and word[0].isalpha():
                    abbreviated_words.append(word[0].upper())
            
            if abbreviated_words:
                abbreviated_parts.append("".join(abbreviated_words))
        
        # Join with 'v'
        if len(abbreviated_parts) >= 2:
            return f"{abbreviated_parts[0]} v {abbreviated_parts[1]}"
        elif abbreviated_parts:
            return abbreviated_parts[0]
        
        return normalized
    
    def generate_variations(self, name: str) -> PartyNameVariations:
        """
        Generate all variations of party names for search.
        
        Returns variations including:
        - Full name
        - Abbreviated name
        - Full name with 'The' removed
        - Abbreviated with '&' instead of 'and'
        """
        if not name:
            return PartyNameVariations(full="", abbreviated="", variations=[])
        
        normalized = self.normalize(name)
        abbreviated = self.abbreviate(normalized)
        
        variations: Set[str] = set()
        
        # Full name
        variations.add(normalized)
        
        # Abbreviated
        if abbreviated != normalized:
            variations.add(abbreviated)
        
        # Without 'The'
        without_the = re.sub(r'^the\s+', '', normalized, flags=re.IGNORECASE)
        if without_the != normalized:
            variations.add(without_the)
            # Abbreviated version of 'without the'
            abbr_without_the = self.abbreviate(without_the)
            if abbr_without_the != abbreviated:
                variations.add(abbr_without_the)
        
        # With '&' instead of 'and'
        with_ampersand = normalized.replace(" and ", " & ")
        if with_ampersand != normalized:
            variations.add(with_ampersand)
        
        # With 'and' instead of '&'
        with_and = normalized.replace(" & ", " and ")
        if with_and != normalized and with_and not in variations:
            variations.add(with_and)
        
        return PartyNameVariations(
            full=normalized,
            abbreviated=abbreviated,
            variations=list(variations)
        )
    
    def build_westlaw_query(self, name: str) -> str:
        """
        Build Westlaw search query with OR operator for variations.
        
        Example: 'Smith v Jones' OR 'S v J'
        """
        variations = self.generate_variations(name)
        
        # Use full and abbreviated as primary searches
        queries = [variations.full, variations.abbreviated]
        
        # Add other unique variations
        for var in variations.variations:
            if var not in queries:
                queries.append(var)
        
        # Build OR query
        if len(queries) == 1:
            return queries[0]
        
        return " OR ".join(f'"{q}"' for q in queries[:3])  # Limit to top 3


# Singleton instance
_party_handler: Optional[PartyNameHandler] = None


def get_party_handler() -> PartyNameHandler:
    """Get singleton party name handler instance."""
    global _party_handler
    if _party_handler is None:
        _party_handler = PartyNameHandler()
    return _party_handler
