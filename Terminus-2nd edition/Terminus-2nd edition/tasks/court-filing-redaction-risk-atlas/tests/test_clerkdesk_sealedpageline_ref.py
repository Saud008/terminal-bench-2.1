"""Sealed term normalization and provenance reference probes."""

from clerkdesk_refmath import locate_line, matches_sealed, normalize_term, pick_primary_docket


def test_clerkredact_sealedpg01_refmath_sealed_hyphen_space_fold() -> None:
    """Reference sealed matcher folds hyphen and space variants per sealed-term-contract."""
    assert matches_sealed("SEALED RECORD detail", "sealed-record") is True


def test_clerkredact_sealedpg02_refmath_normalize_term_lowercase() -> None:
    """Reference normalize_term lowercases and collapses separators per sealed-term-contract."""
    assert normalize_term("Sealed-Record") == "sealed record"


def test_clerkredact_sealedpg03_refmath_docket_primary_wins() -> None:
    """Reference pick_primary_docket prefers primary_flag=true rows per docket-dedup-contract."""
    dockets = [
        {"number": "CV-99", "filed_at": "2024-04-20", "primary_flag": False},
        {"number": "CV-05", "filed_at": "2024-04-01", "primary_flag": True},
    ]
    assert pick_primary_docket(dockets) == "CV-05"


def test_clerkredact_sealedpg04_refmath_locate_line_returns_line_num() -> None:
    """Reference locate_line returns page and 1-based line numbers per provenance-contract."""
    page = {"page_num": 4, "lines": [
        {"line_num": 1, "text": "Header."},
        {"line_num": 7, "text": "protected deponent list here"},
    ]}
    pg, ln = locate_line(page, "protected deponent list")
    assert pg == 4
    assert ln == 7
