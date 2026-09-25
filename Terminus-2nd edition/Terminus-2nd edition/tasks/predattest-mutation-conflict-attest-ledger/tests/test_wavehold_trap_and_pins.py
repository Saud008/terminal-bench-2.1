"""Hidden-trap coverage plus policy-pin integrity. The trap wave is not
shipped under /app; it interlocks several gates so a partial fix cannot
compile it to reference. Pin checks lock the shipped config bytes to the
verifier-side pinned copy and confirm reference math stays under /tests.
"""

from __future__ import annotations

import json
from pathlib import Path

import rollout_preview_support as support

TRAP_WAVE = str(support.HIDDEN_DIR / "wave-trap.jsonl")


def test_trap_wave_compiles_to_reference_under_agent_build():
    """The agent's /app build must compile the hidden trap wave to the
    reference computed by /tests/wavehold_math.py."""
    support.reset_state()
    assert support.run_preview(TRAP_WAVE, run_id="trap") == support.reference_atlas(TRAP_WAVE)


def test_shipped_config_is_byte_identical_to_verifier_pin():
    """/app/config/wavehold.json must match the verifier-side pinned copy."""
    shipped = (support.APP / "config" / "wavehold.json").read_bytes()
    pinned = support.PINNED_CONFIG_PATH.read_bytes()
    assert shipped == pinned


def test_hold_attrs_carry_the_exact_pinned_attrs():
    """The hold policy must list the pinned attrs and no near-miss."""
    with open(support.CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    assert "drain_token" in cfg["hold_attrs"]
    assert "raw_secret" in cfg["hold_attrs"]
    assert "drain_token_scope" not in cfg["hold_attrs"]


def test_reference_math_lives_under_tests_not_opt():
    """Independent reference math must stay under /tests, not agent-readable /opt."""
    math_path = support.MATH_MODULE_PATH.resolve()
    assert math_path.is_file()
    assert math_path.name == "wavehold_math.py"
    assert "tests" in math_path.parts
    assert not Path("/opt/verifier-wavehold-math/wavehold_math.py").exists()
    assert not Path("/opt/verifier-wavehold/wavehold.json").exists()
