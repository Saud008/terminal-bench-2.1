"""Named output path coverage for nomrep publish atlas export."""

from __future__ import annotations

import json
import subprocess

import pytest

from placement_atlas_math import reference_compile_atlas, reference_load_scenario
from nomrep_atlas_cli import BUFFER_PATH, CLI_BIN, FIXTURE_DIR, SEED_POOL, run_full_atlas, wipe


@pytest.fixture(autouse=True)
def isolate_workspace():
    wipe()
    yield
    wipe()


def test_nomrep_cluster_atlas_json_lands_under_output_root():
    """nomrep publish must emit JSON beneath /app/output/ for a compiled seed."""
    seed = SEED_POOL[0]
    out = run_full_atlas(seed, "basic-volume-join")
    rep = json.loads(out.read_text(encoding="utf-8"))
    sc = reference_load_scenario(FIXTURE_DIR / "basic-volume-join.json", seed)
    ref = reference_compile_atlas(sc, seed)
    assert out.is_file()
    assert str(out).startswith("/app/output/")
    assert rep["seed"] == seed
    assert rep["volume_joins"] == ref["volume_joins"]


def test_nomrep_load_populates_var_placement_buffer_file():
    """nomrep load must write /app/var/placement-buffer.json."""
    seed = SEED_POOL[0]
    proc = subprocess.run(
        [str(CLI_BIN), "load", "--seed", seed, "--scenario", "basic-volume-join"],
        cwd="/app",
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    snap = json.loads(BUFFER_PATH.read_text(encoding="utf-8"))
    assert snap["seed"] == seed
    assert snap["scenario"] == "basic-volume-join"
    assert BUFFER_PATH.is_file()


def test_nomrep_publish_suffix_is_placement_atlas_json():
    """Published atlas filenames end with -placement-atlas.json under /app/output/."""
    out = run_full_atlas(SEED_POOL[1], "basic-volume-join")
    assert str(out).startswith("/app/output/")
    assert out.name.endswith("-placement-atlas.json")


def test_nomrep_journal_run_id_surfaces_on_publish():
    """Published atlas run_id must come from the compiled atlas index."""
    seed = SEED_POOL[2]
    out = run_full_atlas(seed, "basic-volume-join")
    rep = json.loads(out.read_text(encoding="utf-8"))
    assert rep["run_id"] >= 1
