"""
Unit tests for PartyNameHandler - OSCOLA abbreviation standards.
"""
import pytest

from app.utils.party_names import PartyNameHandler, get_party_handler


class TestPartyNameNormalization:
    """Test party name normalization."""
    
    @pytest.fixture
    def handler(self):
        return PartyNameHandler()
    
    def test_basic_normalization(self, handler):
        """Test basic normalization."""
        result = handler.normalize("Smith v Jones")
        assert result == "Smith v Jones"
    
    def test_standardize_versus(self, handler):
        """Test standardizing vs/vs./versus to v."""
        assert handler.normalize("Smith vs Jones") == "Smith v Jones"
        assert handler.normalize("Smith vs. Jones") == "Smith v Jones"
        assert handler.normalize("Smith versus Jones") == "Smith v Jones"
    
    def test_remove_extra_spaces(self, handler):
        """Test removing extra whitespace."""
        result = handler.normalize("Smith   v   Jones")
        assert result == "Smith v Jones"
    
    def test_strip_whitespace(self, handler):
        """Test stripping leading/trailing whitespace."""
        result = handler.normalize("  Smith v Jones  ")
        assert result == "Smith v Jones"


class TestPartyNameAbbreviation:
    """Test OSCOLA-style abbreviation."""
    
    @pytest.fixture
    def handler(self):
        return PartyNameHandler()
    
    def test_simple_abbreviation(self, handler):
        """Test simple party name abbreviation."""
        result = handler.abbreviate("Smith v Jones")
        assert result == "S v J"
    
    def test_regina_abbreviation(self, handler):
        """Test Regina abbreviation."""
        result = handler.abbreviate("Regina v Smith")
        assert result == "R v S"
    
    def test_hsbc_example(self, handler):
        """Test HSBC Bank example from spec."""
        result = handler.abbreviate("HSBC Bank Plc v Jones")
        assert result == "H v J"
    
    def test_multi_word_parties(self, handler):
        """Test multi-word party names."""
        result = handler.abbreviate("The Attorney General v Smith")
        assert result == "A v S"
    
    def test_skip_suffixes(self, handler):
        """Test skipping corporate suffixes."""
        result = handler.abbreviate("ABC Ltd v XYZ Plc")
        assert result == "A v X"
    
    def test_skip_prefixes(self, handler):
        """Test skipping name prefixes."""
        result = handler.abbreviate("Mr Smith v Dr Jones")
        assert result == "S v J"
    
    def test_three_word_parties(self, handler):
        """Test three-word party names."""
        result = handler.abbreviate("John Paul Smith v Mary Jane Jones")
        assert result == "JPS v MJJ"


class TestPartyVariations:
    """Test generating party name variations."""
    
    @pytest.fixture
    def handler(self):
        return PartyNameHandler()
    
    def test_full_and_abbreviated(self, handler):
        """Test full and abbreviated variations."""
        result = handler.generate_variations("Smith v Jones")
        assert result.full == "Smith v Jones"
        assert result.abbreviated == "S v J"
    
    def test_variations_list(self, handler):
        """Test variations list includes multiple forms."""
        result = handler.generate_variations("The Smith v Jones")
        # Should include "The Smith v Jones" and "Smith v Jones"
        assert "The Smith v Jones" in result.variations
        assert "Smith v Jones" in result.variations
    
    def test_ampersand_variation(self, handler):
        """Test ampersand variation."""
        result = handler.generate_variations("Smith and Jones v Brown")
        assert "Smith & Jones v Brown" in result.variations


class TestWestlawQuery:
    """Test building Westlaw search queries."""
    
    @pytest.fixture
    def handler(self):
        return PartyNameHandler()
    
    def test_basic_query(self, handler):
        """Test basic query construction."""
        query = handler.build_westlaw_query("Smith v Jones")
        assert "Smith v Jones" in query
        assert "S v J" in query
    
    def test_or_operator(self, handler):
        """Test OR operator is used."""
        query = handler.build_westlaw_query("Smith v Jones")
        assert " OR " in query
    
    def test_quoted_variations(self, handler):
        """Test variations are quoted."""
        query = handler.build_westlaw_query("Smith v Jones")
        assert '"Smith v Jones"' in query
        assert '"S v J"' in query


def test_get_party_handler_singleton():
    """Test that get_party_handler returns singleton."""
    handler1 = get_party_handler()
    handler2 = get_party_handler()
    assert handler1 is handler2


class TestComplexPartyNames:
    """Test complex real-world party names."""
    
    @pytest.fixture
    def handler(self):
        return PartyNameHandler()
    
    def test_government_party(self, handler):
        """Test government party names."""
        result = handler.abbreviate("Secretary of State for Justice v Smith")
        assert result == "S v S"  # Secretary, Smith
    
    def test_company_names(self, handler):
        """Test company names."""
        result = handler.abbreviate("British Airways Plc v Union")
        assert result == "B v U"
    
    def test_local_authority(self, handler):
        """Test local authority names."""
        result = handler.abbreviate("London Borough of Camden v Smith")
        assert result == "L v S"
