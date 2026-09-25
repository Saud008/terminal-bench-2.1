"""SIP CDR contract tests (manifest + hidden fixture catalog)."""

from __future__ import annotations

import json
from pathlib import Path

from sip_transcript_runner import MANIFEST_SLUGS, TB3_FIXTURE_DIR

MANIFEST = json.loads(Path(__file__).with_name("sip_cdr_manifest.json").read_text(encoding="utf-8"))


def test_sipcdr_manifest_lists_carrier_scenarios() -> None:
    """sip_cdr_manifest.json bundled slugs align with transcript runner catalog."""
    for slug in MANIFEST["bundled"]:
        assert slug in MANIFEST_SLUGS


def test_sipcdr_hidden_catalog_names_poison_slug() -> None:
    """Hidden catalog references TB3 fixture root for off-catalog poison scenarios."""
    assert "hidden-cancel-poison" in MANIFEST["hidden"]
    assert str(TB3_FIXTURE_DIR).startswith("/opt/verifier-fixtures")
    assert TB3_FIXTURE_DIR.name == "sipcdrctl"
