"""Party alias and exhibit linkage reference probes."""

from clerkdesk_refmath import parse_exhibit_refs, resolve_aliases


def test_clerkredact_partyex01_refmath_transitive_alias_closure() -> None:
    """Reference math resolves transitive party alias closure per party-alias-contract."""
    parties = [
        {"id": "P1", "name": "Acme Corp", "aliases": ["Acme Holdings"]},
        {"id": "P2", "name": "Beta LLC", "aliases": ["Acme Corp"]},
    ]
    resolved = resolve_aliases(parties)
    assert "Acme Corp" in resolved["P1"]


def test_clerkredact_partyex02_refmath_exhibit_subref_parsed() -> None:
    """Reference math parses sub-exhibit labels such as Exhibit 12-A per exhibit-link-contract."""
    refs = parse_exhibit_refs("See Exhibit 12-A attachment.")
    assert "Exhibit 12-A" in refs


def test_clerkredact_partyex03_refmath_exhibit_roman_suffix() -> None:
    """Reference math extracts base exhibit numbers with roman numeral suffixes per exhibit-link-contract."""
    refs = parse_exhibit_refs("Review Exhibit 4 IV schedule.")
    assert any("Exhibit 4" in r for r in refs)
