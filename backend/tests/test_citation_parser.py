"""
Unit tests for CitationParser - 20+ variations of HK and UK citations.
"""
import pytest

from app.core.constants import Jurisdiction
from app.utils.citation_parser import CitationParser, get_citation_parser


class TestCitationParser:
    """Test suite for citation parsing."""
    
    @pytest.fixture
    def parser(self):
        return CitationParser()
    
    # ========== HK Citations ==========
    
    def test_hk_cfci_basic(self, parser):
        """Test basic HKCFI citation."""
        result = parser.parse("[2020] HKCFI 123")
        assert result is not None
        assert result.year == 2020
        assert result.reporter == "HKCFI"
        assert result.page == 123
        assert result.jurisdiction == Jurisdiction.HK
        assert result.normalized == "[2020] HKCFI 123"
    
    def test_hk_ca(self, parser):
        """Test HKCA citation."""
        result = parser.parse("[2019] HKCA 456")
        assert result.year == 2019
        assert result.reporter == "HKCA"
        assert result.jurisdiction == Jurisdiction.HK
    
    def test_hk_cfa(self, parser):
        """Test HKCFA citation."""
        result = parser.parse("[2021] HKCFA 789")
        assert result.year == 2021
        assert result.reporter == "HKCFA"
    
    def test_hk_cuhc(self, parser):
        """Test HKCUHC citation."""
        result = parser.parse("[2018] HKCUHC 100")
        assert result.year == 2018
        assert result.reporter == "HKCUHC"
    
    def test_hk_ec(self, parser):
        """Test HKEC citation."""
        result = parser.parse("[2022] HKEC 50")
        assert result.year == 2022
        assert result.reporter == "HKEC"
    
    def test_hk_dc(self, parser):
        """Test HKDC citation."""
        result = parser.parse("[2017] HKDC 200")
        assert result.year == 2017
        assert result.reporter == "HKDC"
    
    def test_hk_lt(self, parser):
        """Test HKLT citation."""
        result = parser.parse("[2023] HKLT 15")
        assert result.year == 2023
        assert result.reporter == "HKLT"
    
    def test_hk_margc(self, parser):
        """Test HKMagC citation."""
        result = parser.parse("[2016] HKMagC 300")
        assert result.year == 2016
        assert result.reporter == "HKMagC"
    
    def test_hk_lowercase(self, parser):
        """Test lowercase HK citation."""
        result = parser.parse("[2020] hkcfi 123")
        assert result is not None
        assert result.reporter == "HKCFI"
    
    # ========== UK Citations ==========
    
    def test_uk_sc(self, parser):
        """Test UKSC citation."""
        result = parser.parse("[2020] UKSC 15")
        assert result.year == 2020
        assert result.reporter == "UKSC"
        assert result.jurisdiction == Jurisdiction.UK
    
    def test_uk_hl(self, parser):
        """Test UKHL citation."""
        result = parser.parse("[2005] UKHL 25")
        assert result.year == 2005
        assert result.reporter == "UKHL"
    
    def test_ew_ca(self, parser):
        """Test EWCA citation."""
        result = parser.parse("[2019] EWCA 100")
        assert result.year == 2019
        assert result.reporter == "EWCA"
    
    def test_ew_hc(self, parser):
        """Test EWHC citation."""
        result = parser.parse("[2021] EWHC 500")
        assert result.year == 2021
        assert result.reporter == "EWHC"
    
    def test_ew_fc(self, parser):
        """Test EWFC citation."""
        result = parser.parse("[2022] EWFC 50")
        assert result.year == 2022
        assert result.reporter == "EWFC"
    
    def test_scotland_ih(self, parser):
        """Test Scottish CSIH citation."""
        result = parser.parse("[2020] CSIH 30")
        assert result.year == 2020
        assert result.reporter == "CSIH"
    
    def test_scotland_oh(self, parser):
        """Test Scottish CSOH citation."""
        result = parser.parse("[2019] CSOH 75")
        assert result.year == 2019
        assert result.reporter == "CSOH"
    
    def test_ni_ca(self, parser):
        """Test Northern Ireland NICA citation."""
        result = parser.parse("[2018] NICA 20")
        assert result.year == 2018
        assert result.reporter == "NICA"
    
    # ========== Law Reports ==========
    
    def test_wlr(self, parser):
        """Test WLR citation with volume."""
        result = parser.parse("[2020] 1 WLR 456")
        assert result.year == 2020
        assert result.volume == 1
        assert result.reporter == "WLR"
        assert result.page == 456
        assert result.jurisdiction == Jurisdiction.UK
    
    def test_wlr_periods(self, parser):
        """Test WLR with periods (should be normalized)."""
        result = parser.parse("[2020] 1 W.L.R. 456")
        assert result.reporter == "WLR"
    
    def test_ac(self, parser):
        """Test AC (Appeal Cases) citation."""
        result = parser.parse("[2019] 2 AC 100")
        assert result.year == 2019
        assert result.volume == 2
        assert result.reporter == "AC"
    
    def test_qb(self, parser):
        """Test QB (Queen's Bench) citation."""
        result = parser.parse("[2021] 3 QB 200")
        assert result.year == 2021
        assert result.volume == 3
        assert result.reporter == "QB"
    
    def test_ch(self, parser):
        """Test Ch (Chancery) citation."""
        result = parser.parse("[2018] 1 Ch 150")
        assert result.year == 2018
        assert result.reporter == "CH"
    
    def test_fam(self, parser):
        """Test Fam (Family) citation."""
        result = parser.parse("[2022] 2 Fam 75")
        assert result.year == 2022
        assert result.reporter == "FAM"
    
    def test_hklrd(self, parser):
        """Test HKLRD (Hong Kong Law Reports) citation."""
        result = parser.parse("[2020] 1 HKLRD 300")
        assert result.year == 2020
        assert result.reporter == "HKLRD"
        assert result.jurisdiction == Jurisdiction.HK
    
    # ========== Edge Cases ==========
    
    def test_extra_spaces(self, parser):
        """Test citation with extra spaces."""
        result = parser.parse("[2020]   HKCFI   123")
        assert result is not None
        assert result.year == 2020
        assert result.page == 123
    
    def test_year_only(self, parser):
        """Test citation with only year."""
        result = parser.parse("[2020] Some Report 123")
        assert result is not None
        assert result.year == 2020
    
    def test_empty_string(self, parser):
        """Test empty string returns None."""
        result = parser.parse("")
        assert result is None
    
    def test_none_input(self, parser):
        """Test None input returns None."""
        result = parser.parse(None)
        assert result is None
    
    def test_invalid_format(self, parser):
        """Test invalid format returns None or fallback."""
        result = parser.parse("Not a citation")
        # Should return None or fallback with unknown jurisdiction
        assert result is None or result.jurisdiction == Jurisdiction.UNKNOWN


class TestCitationComparison:
    """Test citation comparison and matching."""
    
    @pytest.fixture
    def parser(self):
        return CitationParser()
    
    def test_exact_match(self, parser):
        """Test exact citation match."""
        match_type, score = parser.compare_citations(
            "[2020] HKCFI 123",
            "[2020] HKCFI 123"
        )
        assert match_type == "exact"
        assert score == 1.0
    
    def test_similar_volume(self, parser):
        """Test volume tolerance match."""
        match_type, score = parser.compare_citations(
            "[2020] 1 WLR 100",
            "[2020] 2 WLR 100"
        )
        assert match_type == "similar_volume"
        assert score == 0.8
    
    def test_year_match_only(self, parser):
        """Test year-only match."""
        match_type, score = parser.compare_citations(
            "[2020] HKCFI 100",
            "[2020] HKCFI 200"
        )
        # Same year and reporter, different page
        assert match_type == "year_match_only"
    
    def test_no_match_different_year(self, parser):
        """Test no match with different year."""
        match_type, score = parser.compare_citations(
            "[2020] HKCFI 100",
            "[2021] HKCFI 100"
        )
        assert match_type == "none"
        assert score == 0.0
    
    def test_year_fuzzy(self, parser):
        """Test year fuzzy match (year differs by 1)."""
        match_type, score = parser.compare_citations(
            "[2020] HKCFI 100",
            "[2019] HKCFI 100"
        )
        assert match_type == "year_match_only"
        assert score == 0.3


class TestWhereReportedMatching:
    """Test matching against Where Reported lists."""
    
    @pytest.fixture
    def parser(self):
        return CitationParser()
    
    def test_find_exact_in_list(self, parser):
        """Test finding exact match in Where Reported."""
        where_reported = [
            "[2020] 1 WLR 456",
            "[2020] HKCFI 123",
            "[2020] 2 HKC 100",
        ]
        match, match_type, score = parser.find_in_where_reported(
            "[2020] HKCFI 123",
            where_reported
        )
        assert match == "[2020] HKCFI 123"
        assert match_type == "exact"
    
    def test_find_volume_tolerance_in_list(self, parser):
        """Test finding volume tolerance match."""
        where_reported = [
            "[2020] 2 WLR 456",
        ]
        match, match_type, score = parser.find_in_where_reported(
            "[2020] 1 WLR 456",
            where_reported
        )
        assert match is not None
        assert match_type == "similar_volume"
    
    def test_no_match_in_list(self, parser):
        """Test no match found."""
        where_reported = [
            "[2019] HKCFI 100",
            "[2021] HKCFI 200",
        ]
        match, match_type, score = parser.find_in_where_reported(
            "[2020] HKCA 50",
            where_reported
        )
        assert match_type == "none"


class TestNormalization:
    """Test citation normalization."""
    
    @pytest.fixture
    def parser(self):
        return CitationParser()
    
    def test_remove_periods(self, parser):
        """Test removing periods from reporter."""
        normalized = parser.normalize("[2020] 1 W.L.R. 456")
        assert "." not in normalized
        assert "WLR" in normalized
    
    def test_standardize_spaces(self, parser):
        """Test standardizing spaces."""
        normalized = parser.normalize("[2020]   1   WLR   456")
        assert "  " not in normalized
    
    def test_uppercase(self, parser):
        """Test conversion to uppercase."""
        normalized = parser.normalize("[2020] hkcfi 123")
        assert normalized == "[2020] HKCFI 123"


def test_get_citation_parser_singleton():
    """Test that get_citation_parser returns singleton."""
    parser1 = get_citation_parser()
    parser2 = get_citation_parser()
    assert parser1 is parser2
