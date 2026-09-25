"""Behavioral verifier for hitreplay tick-ledger staging and export."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path

import pytest
from reference_collision import (
    mutate_invuln,
    mutate_keyframe_timing,
    reference_replay,
    reference_tick_ledger,
)

APP = Path("/app")
CLI = "/usr/local/bin/hitreplay"
COLLISION_REPORT = "/app/output/collision-report.json"
TICK_LEDGER = "/app/state/tick-ledger.jsonl"
REPLAY_MANIFEST = "/app/state/replay-manifest.json"
ENTITIES = APP / "fixtures" / "entities" / "alpha_entities.json"
ANIMATION = APP / "fixtures" / "animations" / "alpha.jsonl"
REPORT = Path(COLLISION_REPORT)
LEDGER = Path(TICK_LEDGER)
MANIFEST = Path(REPLAY_MANIFEST)
RESET = APP / "scripts" / "reset-state.sh"
TB3_ENTITIES = Path("/opt/verifier-fixtures/hitbox-beta/entities/beta_entities.json")
TB3_ANIMATION = Path("/opt/verifier-fixtures/hitbox-beta/animations/beta.jsonl")
CATALOG = json.loads((APP / "fixtures" / "catalog.json").read_text(encoding="utf-8"))
SEEDS = CATALOG["seeds"]
MAX_TICK = CATALOG["max_tick"]
TICK_RATE = CATALOG["tick_rate"]
FPS = CATALOG["anim_fps"]
CORE = APP / "crates" / "hitbox-core" / "src"
PATCHES = Path(__file__).resolve().parent / "patches"

PATCH_TARGETS = {
    "frame": CORE / "frame.rs",
    "interpolate": CORE / "interpolate.rs",
    "hurtbox": CORE / "hurtbox.rs",
    "collision": CORE / "collision.rs",
    "export": CORE / "export.rs",
    "ledger": CORE / "ledger.rs",
}
PATCH_MODULES = tuple(PATCH_TARGETS.keys())
# Image ships sampling modules correct; only ledger/export are agent-broken.
SHIPPING_GOLDEN = ["frame", "interpolate", "hurtbox", "collision"]
SHIPPING_BROKEN = ["ledger", "export"]
SAMPLING_MODULES = ["frame", "interpolate", "hurtbox", "collision", "ledger"]

PROTECTED = [
    "fixtures/catalog.json",
    "fixtures/entities/alpha_entities.json",
    "fixtures/animations/alpha.jsonl",
    "docs/keyframe-format.md",
    "docs/hurtbox-window.md",
    "docs/frame-index.md",
    "docs/hit-event-dedup.md",
    "docs/collision-report-schema.md",
    "docs/replay-export.md",
    "docs/tick-ledger-schema.md",
    "docs/replay-manifest.md",
]


def _sha256(rel: str) -> str:
    return hashlib.sha256((APP / rel).read_bytes()).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


PROTECTED_SHA256 = {rel: _sha256(rel) for rel in PROTECTED}


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False)


def reset() -> None:
    proc = run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def rebuild_cli() -> None:
    proc = run(["cargo", "build", "--release", "--locked", "-p", "hitreplay"])
    assert proc.returncode == 0, proc.stderr or proc.stdout
    proc = run(["install", "-m", "0755", "/app/target/release/hitreplay", CLI])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def sample_cli(
    *,
    entities: Path = ENTITIES,
    animation: Path = ANIMATION,
    max_tick: int = MAX_TICK,
) -> subprocess.CompletedProcess[str]:
    return run(
        [
            CLI,
            "sample",
            "--entities",
            str(entities),
            "--animation",
            str(animation),
            "--tick-rate",
            str(TICK_RATE),
            "--fps",
            str(FPS),
            "--max-tick",
            str(max_tick),
        ]
    )


def export_cli(
    *,
    entities: Path = ENTITIES,
    animation: Path = ANIMATION,
    report: Path = REPORT,
) -> subprocess.CompletedProcess[str]:
    return run(
        [
            CLI,
            "export",
            "--entities",
            str(entities),
            "--animation",
            str(animation),
            "--export",
            str(report),
        ]
    )


def replay_cli(
    *,
    entities: Path = ENTITIES,
    animation: Path = ANIMATION,
    report: Path = REPORT,
    max_tick: int = MAX_TICK,
) -> subprocess.CompletedProcess[str]:
    return run(
        [
            CLI,
            "replay",
            "--entities",
            str(entities),
            "--animation",
            str(animation),
            "--export",
            str(report),
            "--tick-rate",
            str(TICK_RATE),
            "--fps",
            str(FPS),
            "--max-tick",
            str(max_tick),
        ]
    )


def read_tick_ledger() -> list[dict]:
    assert LEDGER.is_file(), "tick-ledger.jsonl was not written"
    rows: list[dict] = []
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("_kind") == "header":
            continue
        rows.append(row)
    return rows


def read_ledger_header() -> dict:
    first = LEDGER.read_text(encoding="utf-8").splitlines()[0]
    return json.loads(first)


def read_manifest() -> dict:
    assert MANIFEST.is_file(), "replay-manifest.json was not written"
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def restore_shipping_modules() -> None:
    for name in SHIPPING_GOLDEN:
        shutil.copy(PATCHES / f"golden_{name}.rs", PATCH_TARGETS[name])
    for name in SHIPPING_BROKEN:
        shutil.copy(PATCHES / f"broken_{name}.rs", PATCH_TARGETS[name])


def restore_all_broken_modules() -> None:
    """Baseline for partial/isolation probes: every graded module starts broken."""
    for name in PATCH_MODULES:
        shutil.copy(PATCHES / f"broken_{name}.rs", PATCH_TARGETS[name])


@contextmanager
def patched_modules(names: list[str]):
    originals = {mod: PATCH_TARGETS[mod].read_text(encoding="utf-8") for mod in PATCH_MODULES}
    try:
        # Partial fixes must be measured against an all-broken stack so collision
        # (and other sampling bugs) stay broken when only ledger/export are golden.
        restore_all_broken_modules()
        for name in names:
            shutil.copy(PATCHES / f"golden_{name}.rs", PATCH_TARGETS[name])
        rebuild_cli()
        yield
    finally:
        for mod, content in originals.items():
            PATCH_TARGETS[mod].write_text(content, encoding="utf-8")
        rebuild_cli()


@contextmanager
def patched_module(name: str):
    originals = {mod: PATCH_TARGETS[mod].read_text(encoding="utf-8") for mod in PATCH_MODULES}
    try:
        # Isolation checks require siblings broken; shipping already ships several
        # sampling modules golden, which would otherwise make tick-77 appear.
        restore_all_broken_modules()
        shutil.copy(PATCHES / f"golden_{name}.rs", PATCH_TARGETS[name])
        rebuild_cli()
        yield
    finally:
        for mod, content in originals.items():
            PATCH_TARGETS[mod].write_text(content, encoding="utf-8")
        rebuild_cli()


@pytest.fixture(autouse=True)
def _reset_state() -> None:
    reset()


def test_fixture_integrity() -> None:
    """Protected docs and fixture bytes must remain unchanged."""
    for rel, expected in PROTECTED_SHA256.items():
        assert _sha256(rel) == expected


def test_output_artifact_paths_written() -> None:
    """Instruction output paths exist after a successful replay run."""
    proc = replay_cli()
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert REPORT.is_file(), "collision-report.json missing"
    assert MANIFEST.is_file(), "replay-manifest.json missing"
    assert LEDGER.is_file(), "tick-ledger.jsonl missing"


def test_replay_exit_success() -> None:
    """Replay exits 0 and writes collision report."""
    proc = replay_cli()
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert REPORT.is_file()


def test_sample_writes_manifest_and_ledger_header() -> None:
    """Sample stage writes manifest bindings and a sealed ledger header."""
    proc = sample_cli()
    assert proc.returncode == 0, proc.stderr or proc.stdout
    manifest = read_manifest()
    header = read_ledger_header()
    assert manifest["entities_sha256"] == file_sha256(ENTITIES)
    assert manifest["animation_sha256"] == file_sha256(ANIMATION)
    assert manifest["row_count"] == MAX_TICK + 1
    assert header["epoch"] == manifest["epoch"]
    assert header["row_count"] == manifest["row_count"]


def test_tick_ledger_matches_reference() -> None:
    """Per-tick staging ledger matches independent sampling reference."""
    expected_rows = reference_tick_ledger(
        ENTITIES, ANIMATION, tick_rate=TICK_RATE, fps=FPS, max_tick=MAX_TICK
    )
    proc = replay_cli()
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert read_tick_ledger() == expected_rows


def test_partial_sampling_ledger_matches_export_still_wrong() -> None:
    """Correct sampling stages write a good ledger while export sort stays broken."""
    with patched_modules(SAMPLING_MODULES):
        reset()
        expected_rows = reference_tick_ledger(
            ENTITIES, ANIMATION, tick_rate=TICK_RATE, fps=FPS, max_tick=MAX_TICK
        )
        expected_report = reference_replay(
            ENTITIES, ANIMATION, tick_rate=TICK_RATE, fps=FPS, max_tick=MAX_TICK
        )
        proc = replay_cli()
        assert proc.returncode == 0, proc.stderr or proc.stdout
        assert read_tick_ledger() == expected_rows
        actual = json.loads(REPORT.read_text(encoding="utf-8"))
        assert actual != expected_report


def test_partial_export_reads_ledger_collision_still_broken() -> None:
    """Export that reads the ledger still fails when collision dedup stays broken."""
    with patched_modules(["export", "ledger"]):
        reset()
        expected_report = reference_replay(
            ENTITIES, ANIMATION, tick_rate=TICK_RATE, fps=FPS, max_tick=MAX_TICK
        )
        proc = replay_cli()
        assert proc.returncode == 0, proc.stderr or proc.stdout
        actual = json.loads(REPORT.read_text(encoding="utf-8"))
        assert actual != expected_report
        keys = [
            (h["tick"], h["attacker_id"], h["defender_id"], h["instance_id"])
            for h in actual["hits"]
        ]
        assert len(keys) != len(set(keys))


def test_stale_manifest_epoch_blocks_export() -> None:
    """Export rejects a manifest whose epoch no longer matches the ledger header."""
    proc = sample_cli()
    assert proc.returncode == 0, proc.stderr or proc.stdout
    manifest = read_manifest()
    manifest["epoch"] = manifest["epoch"] + 99
    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    proc = export_cli()
    assert proc.returncode != 0, proc.stderr or proc.stdout


def test_tb3_export_rejects_mismatched_entity_binding() -> None:
    """Hidden fixture export must validate manifest entity hash against export inputs."""
    assert TB3_ENTITIES.is_file(), "TB3 entities fixture missing"
    proc = sample_cli()
    assert proc.returncode == 0, proc.stderr or proc.stdout
    proc = export_cli(entities=TB3_ENTITIES, animation=TB3_ANIMATION)
    assert proc.returncode != 0, proc.stderr or proc.stdout


def test_tb3_hidden_fixture_matches_reference_when_sealed() -> None:
    """Hidden beta entities replay matches reference when sample and export are both correct."""
    assert TB3_ENTITIES.is_file(), "TB3 entities fixture missing"
    expected = reference_replay(
        TB3_ENTITIES, TB3_ANIMATION, tick_rate=TICK_RATE, fps=FPS, max_tick=MAX_TICK
    )
    proc = replay_cli(entities=TB3_ENTITIES, animation=TB3_ANIMATION)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    actual = json.loads(REPORT.read_text(encoding="utf-8"))
    assert actual == expected


def test_decoy_blend_not_on_export_hot_path() -> None:
    """decoy.rs is off the export hot path; decoy edits must not change collision output."""
    decoy_path = CORE / "decoy.rs"
    original = decoy_path.read_text(encoding="utf-8")
    decoy = original + "\npub fn export_merge(report_hits: usize) -> usize { report_hits + 99 }\n"
    decoy_path.write_text(decoy, encoding="utf-8")
    rebuild_cli()
    try:
        expected = reference_replay(ENTITIES, ANIMATION, tick_rate=TICK_RATE, fps=FPS, max_tick=MAX_TICK)
        proc = replay_cli()
        assert proc.returncode == 0, proc.stderr or proc.stdout
        actual = json.loads(REPORT.read_text(encoding="utf-8"))
        assert actual == expected
    finally:
        decoy_path.write_text(original, encoding="utf-8")
        rebuild_cli()


def test_report_matches_reference() -> None:
    """Collision report matches independent reference replay."""
    expected = reference_replay(ENTITIES, ANIMATION, tick_rate=TICK_RATE, fps=FPS, max_tick=MAX_TICK)
    proc = replay_cli()
    assert proc.returncode == 0, proc.stderr or proc.stdout
    actual = json.loads(REPORT.read_text(encoding="utf-8"))
    assert actual == expected


def test_frame_index_round_half_up() -> None:
    """Report frames follow round-half-up tick mapping at overlap ticks."""
    expected = reference_replay(ENTITIES, ANIMATION, tick_rate=TICK_RATE, fps=FPS, max_tick=MAX_TICK)
    proc = replay_cli()
    assert proc.returncode == 0, proc.stderr or proc.stdout
    actual = json.loads(REPORT.read_text(encoding="utf-8"))
    assert actual["hits"] == expected["hits"]
    if expected["hits"]:
        sample = expected["hits"][0]
        assert sample["frame"] == (sample["tick"] * FPS + TICK_RATE // 2) // TICK_RATE


def test_invuln_window_excludes_early_frames() -> None:
    """Hits appear only after invuln-adjusted hurtbox start."""
    expected = reference_replay(ENTITIES, ANIMATION, tick_rate=TICK_RATE, fps=FPS, max_tick=MAX_TICK)
    proc = replay_cli()
    assert proc.returncode == 0, proc.stderr or proc.stdout
    actual = json.loads(REPORT.read_text(encoding="utf-8"))
    assert actual["hits"] == expected["hits"]
    for hit in actual["hits"]:
        assert hit["frame"] >= 22


def test_hit_deduplication_by_instance() -> None:
    """Duplicate same-tick instance collisions collapse to one hit row."""
    expected = reference_replay(ENTITIES, ANIMATION, tick_rate=TICK_RATE, fps=FPS, max_tick=MAX_TICK)
    proc = replay_cli()
    assert proc.returncode == 0, proc.stderr or proc.stdout
    actual = json.loads(REPORT.read_text(encoding="utf-8"))
    keys = [(h["tick"], h["attacker_id"], h["defender_id"], h["instance_id"]) for h in actual["hits"]]
    assert len(keys) == len(set(keys))
    assert actual["hits"] == expected["hits"]


def test_export_sort_order() -> None:
    """Events and hits are sorted by tick then entity keys, not timestamp alone."""
    expected = reference_replay(ENTITIES, ANIMATION, tick_rate=TICK_RATE, fps=FPS, max_tick=MAX_TICK)
    proc = replay_cli()
    assert proc.returncode == 0, proc.stderr or proc.stdout
    actual = json.loads(REPORT.read_text(encoding="utf-8"))
    assert actual["events"] == expected["events"]
    assert actual["hits"] == expected["hits"]
    assert actual["events"] == sorted(actual["events"], key=lambda e: (e["tick"], e["entity_id"]))


def test_slerp_rotation_affects_hit_window() -> None:
    """Hit count and ticks align with reference slerp sampling, not euler shortcuts."""
    expected = reference_replay(ENTITIES, ANIMATION, tick_rate=TICK_RATE, fps=FPS, max_tick=MAX_TICK)
    proc = replay_cli()
    assert proc.returncode == 0, proc.stderr or proc.stdout
    actual = json.loads(REPORT.read_text(encoding="utf-8"))
    assert len(actual["hits"]) == len(expected["hits"])
    assert {h["tick"] for h in actual["hits"]} == {h["tick"] for h in expected["hits"]}


@pytest.mark.parametrize("seed", SEEDS)
def test_seed_mutated_invuln_matches_reference(seed: str) -> None:
    """Mutated invuln length per seed prevents hardcoded hit lists."""
    entities = json.loads(ENTITIES.read_text(encoding="utf-8"))
    mutated = mutate_invuln(entities, seed)
    with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
        tmp_path = Path(tmp)
        ent_path = tmp_path / "entities.json"
        ent_path.write_text(json.dumps(mutated), encoding="utf-8")
        expected = reference_replay(ent_path, ANIMATION, tick_rate=TICK_RATE, fps=FPS, max_tick=MAX_TICK)
        proc = replay_cli(entities=ent_path)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        actual = json.loads(REPORT.read_text(encoding="utf-8"))
        assert actual == expected


@pytest.mark.parametrize("seed", SEEDS)
def test_seed_mutated_keyframes_matches_reference(seed: str) -> None:
    """Mutated keyframe timing per seed blocks static collision output."""
    keyframes = [
        json.loads(line)
        for line in ANIMATION.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    mutated = mutate_keyframe_timing(keyframes, seed)
    with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
        tmp_path = Path(tmp)
        anim_path = tmp_path / "anim.jsonl"
        anim_path.write_text("\n".join(json.dumps(k) for k in mutated) + "\n", encoding="utf-8")
        expected = reference_replay(ENTITIES, anim_path, tick_rate=TICK_RATE, fps=FPS, max_tick=MAX_TICK)
        proc = replay_cli(animation=anim_path)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        actual = json.loads(REPORT.read_text(encoding="utf-8"))
        assert actual == expected


@pytest.mark.parametrize("module_name", PATCH_MODULES)
def test_isolated_module_fix_required(module_name: str) -> None:
    """Golden module patch must satisfy module-specific replay checks."""
    with patched_module(module_name):
        reset()
        expected = reference_replay(ENTITIES, ANIMATION, tick_rate=TICK_RATE, fps=FPS, max_tick=MAX_TICK)
        proc = replay_cli()
        assert proc.returncode == 0, proc.stderr or proc.stdout
        actual = json.loads(REPORT.read_text(encoding="utf-8"))
        if module_name == "export":
            event_keys = [(e["tick"], e["entity_id"]) for e in actual["events"]]
            assert event_keys == sorted(event_keys)
            hit_keys = [
                (h["tick"], h["defender_id"], h["instance_id"], h["attacker_id"])
                for h in actual["hits"]
            ]
            assert hit_keys == sorted(hit_keys)
        elif module_name == "ledger":
            manifest = read_manifest()
            header = read_ledger_header()
            assert manifest["entities_sha256"] == file_sha256(ENTITIES)
            assert manifest["animation_sha256"] == file_sha256(ANIMATION)
            assert header["epoch"] == manifest["epoch"]
            assert header["row_count"] == manifest["row_count"]
        elif module_name == "collision":
            keys = [
                (h["tick"], h["attacker_id"], h["defender_id"], h["instance_id"])
                for h in actual["hits"]
            ]
            assert len(keys) == len(set(keys))
        elif module_name == "frame":
            for hit in actual["hits"]:
                expected_frame = (hit["tick"] * FPS + TICK_RATE // 2) // TICK_RATE
                assert hit["frame"] == expected_frame
            for event in actual["events"]:
                expected_frame = (event["tick"] * FPS + TICK_RATE // 2) // TICK_RATE
                assert event["frame"] == expected_frame
        elif module_name == "hurtbox":
            assert actual["hits"]
            assert all(hit["frame"] >= 22 for hit in actual["hits"])
        elif module_name == "interpolate":
            expected = reference_replay(ENTITIES, ANIMATION, tick_rate=TICK_RATE, fps=FPS, max_tick=MAX_TICK)
            ref_ticks = {h["tick"] for h in expected["hits"]}
            ticks = {h["tick"] for h in actual["hits"]}
            interpolate_src = PATCH_TARGETS["interpolate"].read_text(encoding="utf-8")
            assert "quat_to_euler" not in interpolate_src
            assert 77 in ref_ticks
            assert 77 not in ticks
        else:
            assert actual["hits"] == expected["hits"]
