"""Hidden verifier manifests — independent failure modes."""

from __future__ import annotations

import json
import os
from pathlib import Path

from run_originctl import ATLAS_JSON, run_pipeline, wipe_state
from tariff_ref import reference_classifications

HIDDEN_ROOT = Path("/opt/verifier-fixtures/originctl")
def test_tbo_hidden_rvc_floor_trap() -> None:
    """regional value floor must gate preferential treatment per rvc-threshold-contract."""
    wipe_state()
    os.environ.pop("TB3_RVC_FLOOR_BPS", None)
    run_pipeline("hidden-rvc-floor-trap", fixture_root=HIDDEN_ROOT)
    ref = reference_classifications("hidden-rvc-floor-trap", HIDDEN_ROOT)
    body = json.loads(ATLAS_JSON.read_text(encoding="utf-8"))
    assert body["classifications"] == ref["classifications"]
def test_tbo_hidden_expiry_inclusive_trap() -> None:
    """hidden manifest must require inclusive certificate expiry day."""
    wipe_state()
    run_pipeline("hidden-expiry-inclusive", fixture_root=HIDDEN_ROOT)
    ref = reference_classifications("hidden-expiry-inclusive", HIDDEN_ROOT)
    body = json.loads(ATLAS_JSON.read_text(encoding="utf-8"))
    assert body["classifications"] == ref["classifications"]
def test_tbo_tb3_rvc_floor_override_env() -> None:
    """regional value floor must gate preferential treatment per rvc-threshold-contract."""
    wipe_state()
    os.environ["TB3_RVC_FLOOR_BPS"] = "5200"
    try:
        run_pipeline("hidden-rvc-floor-trap", fixture_root=HIDDEN_ROOT)
        ref = reference_classifications(
            "hidden-rvc-floor-trap", HIDDEN_ROOT, rvc_floor_override=5200
        )
        body = json.loads(ATLAS_JSON.read_text(encoding="utf-8"))
        assert body["classifications"] == ref["classifications"]
    finally:
        os.environ.pop("TB3_RVC_FLOOR_BPS", None)
def test_tbo_tb3_fixture_dir_hidden_manifests() -> None:
    """hidden manifests must live under verifier-fixtures originctl tree."""
    assert (HIDDEN_ROOT / "manifests" / "hidden-rvc-floor-trap.json").is_file()
