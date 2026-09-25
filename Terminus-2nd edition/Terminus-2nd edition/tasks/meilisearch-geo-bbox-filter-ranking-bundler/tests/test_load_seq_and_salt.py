"""Load-level generation counters and pin salt mutation."""

from __future__ import annotations

import json
import os
from pathlib import Path

from geobox_cli import geobox, wipe_runtime


def test_load_seq_grows_across_relevels() -> None:
    """Re-loading the same level must advance load_seq for playtest replay."""
    wipe_runtime()
    assert geobox("load-level", "--level", "paris-core", "--run-id", "s1").returncode == 0
    first = json.loads(Path("/app/state/level-roster.json").read_text())["load_seq"]
    assert geobox("load-level", "--level", "paris-core", "--run-id", "s2").returncode == 0
    second = json.loads(Path("/app/state/level-roster.json").read_text())["load_seq"]
    assert (first, second) == (1, 2)


def test_pin_salt_env_mutates_filter_pins() -> None:
    """TB3_PLAY_SALT must append to filter pin names during load-level."""
    wipe_runtime()
    env = os.environ.copy()
    env["TB3_PLAY_SALT"] = "-Z"
    assert (
        geobox("load-level", "--level", "pin-hold", "--run-id", "salt", env=env).returncode
        == 0
    )
    inv = json.loads(Path("/app/state/level-roster.json").read_text())
    held = next(d for d in inv["documents"] if d["doc_id"] == "HELD-1")
    assert held["filter_pins"] == ["ops-pin-Z"]
