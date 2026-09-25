"""Hidden fixture overlays and environment overrides."""

from __future__ import annotations

from pathlib import Path

from closure_spec import reference_certificate
from plate_session import cert, reset, run_full

HIDDEN = Path("/opt/verifier-fixtures/platclosectl/scenarios")


def test_catalog_mask_bit_on_hidden_fixture() -> None:
    """Hidden scenario must exclude stars with catalog-only reject bit 0x04."""
    reset()
    env = {"TB3_FIXTURE_DIR": str(HIDDEN)}
    run_full("hidden-cat-mask-bit", env=env)
    body = cert("hidden-cat-mask-bit")
    exp = reference_certificate(HIDDEN / "hidden-cat-mask-bit.json")
    assert body == exp
    assert body["stars"] == ["S01"]


def test_epoch_nudge_with_match_override() -> None:
    """Hidden epoch scenario must close under TB3_MATCH_ARCSEC with correct nudge polarity."""
    reset()
    env = {"TB3_FIXTURE_DIR": str(HIDDEN), "TB3_MATCH_ARCSEC": "0.8"}
    run_full("hidden-epoch-reverse", env=env)
    body = cert("hidden-epoch-reverse")
    exp = reference_certificate(HIDDEN / "hidden-epoch-reverse.json", match_override=0.8)
    assert body == exp
    assert body["active_count"] == 2
