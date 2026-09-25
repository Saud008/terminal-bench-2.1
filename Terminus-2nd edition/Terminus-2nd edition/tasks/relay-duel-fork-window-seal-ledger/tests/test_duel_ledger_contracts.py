"""duel ledger contract tests (manifest + hidden fixture catalog)."""

from __future__ import annotations

import json
from pathlib import Path

from duel_admit_runner import MANIFEST_SLUGS, TB3_FIXTURE_DIR

MANIFEST = json.loads(Path(__file__).with_name("duel_ledger_manifest.json").read_text(encoding="utf-8"))


def test_duelctl_manifest_lists_arena_scenarios() -> None:
    """duel_ledger_manifest.json bundled slugs align with admit-log runner catalog."""
    for slug in MANIFEST["bundled"]:
        assert slug in MANIFEST_SLUGS


def test_duelctl_hidden_catalog_names_poison_slug() -> None:
    """Hidden catalog references TB3 fixture root for off-catalog poison scenarios."""
    assert "hidden-forfeit-poison" in MANIFEST["hidden"]
    assert str(TB3_FIXTURE_DIR).startswith("/opt/verifier-fixtures")
    assert TB3_FIXTURE_DIR.name == "duelctl"
