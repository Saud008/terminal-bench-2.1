"""Behavioral verifier for crafting recipe catalyst cycle resolver repair."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
import tempfile
from pathlib import Path

import pytest

from reference_crafter import (
    apply,
    detect_cycles,
    overlay_book,
    overflow_batch,
    preview,
    smelt_batch_for_seed,
)

APP = Path("/app")
CLI = Path("/usr/local/bin/crafter")
DB = APP / "work" / "inventory.db"
EXPORT = APP / "output" / "inventory-export.json"
BASE_RECIPES = APP / "fixtures" / "recipes" / "base.json"
CYCLE_RECIPES = APP / "fixtures" / "recipes" / "cycle-trap.json"
CHAIN_RECIPES = APP / "fixtures" / "recipes" / "catalyst-chain.json"
DEFAULT_PROFILE = APP / "fixtures" / "profiles" / "default.json"
TIGHT_PROFILE = APP / "fixtures" / "profiles" / "tight-stacks.json"
SEED = os.environ.get("VERIFIER_SEED", "craft-cycle-seed-17")
EXTRA_SEEDS = ("craft-matrix-3", "craft-matrix-29", "craft-matrix-53")
PROTECTED_SHA256: dict[str, str] = {}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


for rel in (
    "config/crafter.json",
    "docs/crafter-contract.md",
    "docs/recipe-format.md",
    "docs/inventory-schema.md",
    "docs/cycle-detection.md",
    "docs/substitute-rules.md",
    "docs/export-schema.md",
    "docs/fixture-catalog.md",
    "fixtures/catalog.json",
    "fixtures/recipes/base.json",
    "fixtures/recipes/catalyst-chain.json",
    "fixtures/recipes/cycle-trap.json",
    "fixtures/profiles/default.json",
    "fixtures/profiles/tight-stacks.json",
    "crates/craft-cli/src/main.rs",
    "crates/craft-core/src/model.rs",
    "crates/inventory-db/src/schema.rs",
):
    PROTECTED_SHA256[rel] = _sha256(APP / rel)


def _build() -> None:
    proc = subprocess.run(
        ["bash", "/app/scripts/rebuild.sh"],
        cwd=APP,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout


def _reset() -> None:
    subprocess.run(["bash", "/app/scripts/reset-state.sh"], check=True)


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(CLI), *args],
        cwd=APP,
        capture_output=True,
        text=True,
    )


def _seed(profile: Path, db: Path | None = None) -> None:
    target = db or DB
    proc = _run(
        [
            "seed",
            "--seed",
            SEED,
            "--profile",
            str(profile),
            "--db",
            str(target),
        ]
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout


def _load_slots(db: Path = DB) -> list[dict]:
    conn = sqlite3.connect(db)
    rows = conn.execute("SELECT slot, item, qty FROM slots ORDER BY slot").fetchall()
    conn.close()
    return [{"slot": r[0], "item": r[1], "qty": r[2]} for r in rows]


def _catalyst_qty(db: Path = DB) -> int:
    conn = sqlite3.connect(db)
    row = conn.execute(
        "SELECT COALESCE(SUM(qty), 0) FROM slots WHERE item = 'forge_spark'"
    ).fetchone()
    conn.close()
    return int(row[0])


def _write_overlay_recipes(seed: str) -> Path:
    book = overlay_book(BASE_RECIPES, seed)
    tmp = Path(tempfile.mkdtemp(dir="/tmp"))
    path = tmp / "overlay.json"
    path.write_text(json.dumps(book), encoding="utf-8")
    return path


@pytest.fixture(scope="session", autouse=True)
def _session_build() -> None:
    _build()


@pytest.fixture(autouse=True)
def _isolate() -> None:
    _reset()
    yield
    _reset()


def test_protected_fixtures_unchanged() -> None:
    """Bundled docs and fixtures must remain immutable."""
    for rel, digest in PROTECTED_SHA256.items():
        assert _sha256(APP / rel) == digest, rel


def test_preview_preserves_catalyst_in_db() -> None:
    """Preview must not deduct non-consumed catalyst from SQLite inventory."""
    _seed(DEFAULT_PROFILE)
    before = _catalyst_qty()
    proc = _run(
        [
            "preview",
            "--seed",
            SEED,
            "--recipe",
            "smelt_iron",
            "--qty",
            "1",
            "--recipes",
            str(BASE_RECIPES),
            "--db",
            str(DB),
        ]
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    after = _catalyst_qty()
    assert after == before == 1


def test_substitute_scrap_smelt_matches_reference(seed: str = SEED) -> None:
    """Smelt with only scrap_iron inventory must succeed via substitute map."""
    overlay = _write_overlay_recipes(seed)
    _seed(DEFAULT_PROFILE)
    batch = smelt_batch_for_seed(seed)
    slots_before = _load_slots()
    book = json.loads(overlay.read_text(encoding="utf-8"))
    ref = apply(book, slots_before, "smelt_iron", batch)
    assert ref["ok"], ref

    proc = _run(
        [
            "apply",
            "--seed",
            seed,
            "--recipe",
            "smelt_iron",
            "--qty",
            str(batch),
            "--recipes",
            str(overlay),
            "--db",
            str(DB),
        ]
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    slots_after = _load_slots()
    assert slots_after == ref["slots"]


@pytest.mark.parametrize("seed", (SEED, *EXTRA_SEEDS))
def test_substitute_matrix(seed: str) -> None:
    """Seed-mutated substitute overlay still crafts via scrap_iron."""
    test_substitute_scrap_smelt_matches_reference(seed)


def test_cycle_trap_detected() -> None:
    """Catalyst edges must mark cycle-trap.json cyclic with exit 3."""
    ref = detect_cycles(json.loads(CYCLE_RECIPES.read_text(encoding="utf-8")))
    assert ref["cyclic"]
    proc = _run(["validate-graph", "--recipes", str(CYCLE_RECIPES)])
    assert proc.returncode == 3, proc.stdout
    report = json.loads(proc.stdout)
    assert report["cyclic"] is True
    assert report["edge_count"] >= ref["edge_count"]


def test_stack_overflow_rejects_without_mutation() -> None:
    """Near-full ingot stack must reject overflow craft with unchanged inventory."""
    _seed(TIGHT_PROFILE)
    before = _load_slots()
    batch = overflow_batch(SEED)
    book = json.loads(BASE_RECIPES.read_text(encoding="utf-8"))
    ref = apply(book, before, "smelt_iron", batch)
    assert not ref["ok"], "reference must reject overflow batch"
    proc = _run(
        [
            "apply",
            "--seed",
            SEED,
            "--recipe",
            "smelt_iron",
            "--qty",
            str(batch),
            "--recipes",
            str(BASE_RECIPES),
            "--db",
            str(DB),
        ]
    )
    assert proc.returncode != 0
    after = _load_slots()
    assert after == before


def test_failed_apply_rollback_inputs() -> None:
    """Rejected apply must not partially deduct inputs."""
    _seed(TIGHT_PROFILE)
    before = _load_slots()
    batch = overflow_batch(SEED)
    proc = _run(
        [
            "apply",
            "--seed",
            SEED,
            "--recipe",
            "smelt_iron",
            "--qty",
            str(batch),
            "--recipes",
            str(BASE_RECIPES),
            "--db",
            str(DB),
        ]
    )
    assert proc.returncode != 0
    assert _load_slots() == before


def test_consumed_catalyst_only_on_apply() -> None:
    """Consumed catalyst remains through preview but deducts on successful apply."""
    profile = {
        "slot_limit": 8,
        "slots": [
            {"slot": 1, "item": "elixir_base", "qty": 2},
            {"slot": 2, "item": "alchemy_vial", "qty": 2},
        ],
    }
    tmp = Path(tempfile.mkdtemp(dir="/tmp")) / "elixir.json"
    tmp.write_text(json.dumps(profile), encoding="utf-8")
    _seed(tmp)
    prev = _run(
        [
            "preview",
            "--seed",
            SEED,
            "--recipe",
            "brew_elixir",
            "--qty",
            "1",
            "--recipes",
            str(CHAIN_RECIPES),
            "--db",
            str(DB),
        ]
    )
    assert prev.returncode == 0
    conn = sqlite3.connect(DB)
    vial_prev = conn.execute(
        "SELECT COALESCE(SUM(qty),0) FROM slots WHERE item='alchemy_vial'"
    ).fetchone()[0]
    conn.close()
    assert vial_prev == 2

    apply_proc = _run(
        [
            "apply",
            "--seed",
            SEED,
            "--recipe",
            "brew_elixir",
            "--qty",
            "1",
            "--recipes",
            str(CHAIN_RECIPES),
            "--db",
            str(DB),
        ]
    )
    assert apply_proc.returncode == 0
    conn = sqlite3.connect(DB)
    vial_after = conn.execute(
        "SELECT COALESCE(SUM(qty),0) FROM slots WHERE item='alchemy_vial'"
    ).fetchone()[0]
    elixir = conn.execute(
        "SELECT COALESCE(SUM(qty),0) FROM slots WHERE item='potent_elixir'"
    ).fetchone()[0]
    conn.close()
    assert vial_after == 1
    assert elixir == 1


def test_export_after_craft() -> None:
    """Export reports committed craft and slot snapshot."""
    overlay = _write_overlay_recipes(SEED)
    _seed(DEFAULT_PROFILE)
    batch = 1
    proc = _run(
        [
            "apply",
            "--seed",
            SEED,
            "--recipe",
            "smelt_iron",
            "--qty",
            str(batch),
            "--recipes",
            str(overlay),
            "--db",
            str(DB),
        ]
    )
    assert proc.returncode == 0
    exp = _run(["export", "--db", str(DB), "--out", str(EXPORT)])
    assert exp.returncode == 0
    data = json.loads(EXPORT.read_text(encoding="utf-8"))
    assert data["last_craft"] == "smelt_iron"
    assert data["slots"] == _load_slots()


def test_reference_preview_agrees(seed: str = SEED) -> None:
    """CLI preview JSON must match independent reference planner."""
    overlay = _write_overlay_recipes(seed)
    _seed(DEFAULT_PROFILE)
    batch = smelt_batch_for_seed(seed)
    slots = _load_slots()
    book = json.loads(overlay.read_text(encoding="utf-8"))
    ref = preview(book, slots, "smelt_iron", batch)
    proc = _run(
        [
            "preview",
            "--seed",
            seed,
            "--recipe",
            "smelt_iron",
            "--qty",
            str(batch),
            "--recipes",
            str(overlay),
            "--db",
            str(DB),
        ]
    )
    assert proc.returncode == (0 if ref["ok"] else 2)
    body = json.loads(proc.stdout)
    assert body["ok"] == ref["ok"]
    if ref["ok"]:
        assert body["inputs"] == ref["inputs"]
