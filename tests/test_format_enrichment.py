"""Tests for AnimalRepository._format_enrichment_progress."""

from daynimal.repository import AnimalRepository


def test_no_species():
    assert AnimalRepository._format_enrichment_progress(0, 0) == "N/A"


def test_zero_enriched():
    assert AnimalRepository._format_enrichment_progress(0, 1000) == "0/1000 (0%)"


def test_less_than_0_1_percent():
    # 1/10000 = 0.01% < 0.1%
    result = AnimalRepository._format_enrichment_progress(1, 10000)
    assert "< 0.1%" in result
    assert "1/10000" in result


def test_above_0_1_percent():
    # 500/160000 = 0.3125%
    result = AnimalRepository._format_enrichment_progress(500, 160000)
    assert "0.3%" in result
    assert "500/160000" in result
