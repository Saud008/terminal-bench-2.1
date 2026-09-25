"""TB3 hidden fixture traps for whslot crew and capacity rules."""
from __future__ import annotations

import json
import os
from pathlib import Path

from whslot_refmath import expected_atlas_body, expected_wave_assignments
from whslot_driver import ATLAS_JSON, run_pipeline, wipe_state

HIDDEN_ROOT = Path("/opt/verifier-fixtures/whslot")


def test_tb3_shift_end_inclusive_trap() -> None:
    """TB3 hidden bundle requires inclusive shift_end minute for crew-bind acceptance."""
    wipe_state()
    os.environ["TB3_FIXTURE_DIR"] = str(HIDDEN_ROOT)
    try:
        run_pipeline("hidden-shift-end-trap", fixture_root=HIDDEN_ROOT)
        body = json.loads(ATLAS_JSON.read_text(encoding="utf-8"))
        ref = expected_atlas_body(HIDDEN_ROOT, "hidden-shift-end-trap")
        assert body["assignments"] == ref["assignments"]
    finally:
        os.environ.pop("TB3_FIXTURE_DIR", None)


def test_tb3_headroom_margin_trap() -> None:
    """TB3 hidden bundle applies larger headroom_margin than bundled capacity scenarios."""
    wipe_state()
    os.environ["TB3_FIXTURE_DIR"] = str(HIDDEN_ROOT)
    try:
        run_pipeline("hidden-headroom-trap", fixture_root=HIDDEN_ROOT)
        body = json.loads(ATLAS_JSON.read_text(encoding="utf-8"))
        assert body["assignments"] == expected_wave_assignments(HIDDEN_ROOT, "hidden-headroom-trap")
    finally:
        os.environ.pop("TB3_FIXTURE_DIR", None)
