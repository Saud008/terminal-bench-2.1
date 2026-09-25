"""Unified pytest entrypoint for edl-conform-audit verifier."""

from __future__ import annotations

import subprocess

from conform_frame_oracle import (
    oracle_publish_atlas as _oracle_publish_atlas,
    oracle_stage_snapshot as _oracle_stage_snapshot,
    tc_to_frames,
)

from test_stage_publish_contract import *  # noqa: F403
from test_timecode_rules import *  # noqa: F403
from test_verifier_traps import *  # noqa: F403


def reference_stage_snapshot(manifest: dict) -> dict:
    """Independent subprocess-free SMPTE conform stage oracle."""
    return _oracle_stage_snapshot(manifest)


def reference_publish_atlas(manifest: dict, sealed: dict) -> dict:
    """Independent conform atlas oracle from sealed snapshot."""
    return _oracle_publish_atlas(manifest, sealed)


__all__ = [
    "reference_publish_atlas",
    "reference_stage_snapshot",
    "tc_to_frames",
    "subprocess",
]
