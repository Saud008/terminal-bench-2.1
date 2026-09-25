"""Hidden radar stitch traps under VRST_FIXTURE_ROOT."""

from __future__ import annotations

import json
import os
from pathlib import Path

from stitch_volume_verifier import (
    HIDDEN_OFFSET_TRAP,
    HIDDEN_PHASE_TRAP,
    HIDDEN_TRAP_ROOT,
    assert_report_matches,
    reference_from_bundle_dir,
    run_stitch,
)


def test_hidden_phase_wrap_report():
    """Hidden phase-wrap bundle azimuth coverage under /opt/verifier-fixtures/vrst."""
    os.environ["VRST_FIXTURE_ROOT"] = HIDDEN_TRAP_ROOT
    hidden = Path(HIDDEN_PHASE_TRAP)
    body = json.loads(run_stitch("phase-wrap-trap", "hid-pw").read_text(encoding="utf-8"))
    ref = reference_from_bundle_dir(hidden, "hid-pw")
    assert body["azimuth_coverage_centideg"] == 250
    assert_report_matches(body, ref)


def test_hidden_channel_offset_report():
    """Hidden offset-channel trap under /opt/verifier-fixtures/vrst per channel offsets."""
    os.environ["VRST_FIXTURE_ROOT"] = HIDDEN_TRAP_ROOT
    hidden = Path(HIDDEN_OFFSET_TRAP)
    body = json.loads(run_stitch("offset-channel-trap", "hid-ch").read_text(encoding="utf-8"))
    ref = reference_from_bundle_dir(hidden, "hid-ch")
    assert_report_matches(body, ref)
