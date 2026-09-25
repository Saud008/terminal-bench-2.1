"""Behavioral verifier for ROS2 bag QoS gap fill and deadline export."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from reference_audit import (
    expected_message_rows,
    expected_miss_rows,
    fill_gaps,
    find_deadline_misses,
    load_bag,
    payload_hash,
    publish_ns_monotonic_per_topic,
    read_sqlite,
)

APP = Path("/app")
BAGS = APP / "fixtures/bags"
CATALOG = json.loads((APP / "fixtures/catalog.json").read_text(encoding="utf-8"))
SEEDS = json.loads((APP / "fixtures/seeds.json").read_text(encoding="utf-8"))["seeds"]
OUTPUT = APP / "output"
SRC = APP / "crates/bag-audit/src"
BROKEN = Path("/opt/verifier-broken-bag")
GOLDEN = Path(__file__).resolve().parent / "golden_modules"

MODULES = {
    "read": SRC / "bag/read.rs",
    "gap": SRC / "bag/gap.rs",
    "deadline": SRC / "qos/deadline.rs",
    "sqlite": SRC / "export/sqlite.rs",
}

GOLDEN_FILES = {
    "read": "golden_read.rs",
    "gap": "golden_gap.rs",
    "deadline": "golden_deadline.rs",
    "sqlite": "golden_sqlite.rs",
}

ALL_BAGS = CATALOG["bags"]
GAP_TRAP_BAGS = [
    "gap-monotonic",
    "gap-dense",
    "multi-topic-gap",
    "payload-chain",
    "combo-stack",
]
DEADLINE_TRAP_BAGS = [
    ("deadline-publish", 1.0, 7),
    ("twin-deadline", 1.0, 3),
    ("seed-ladder", 1.0, 3),
    ("combo-stack", 1.0, 0),
    ("speed-factor", 2.0, 7),
]
READ_TRAP_BAGS = ["remap-legacy", "combo-stack"]
SQLITE_TRAP_BAGS = ["gap-monotonic", "gap-dense"]

SPEED_MATRIX = {
    "speed-factor": [(1.0, 0), (2.0, 1)],
    "seed-ladder": [(1.0, None), (2.0, None)],
}


def _env() -> dict[str, str]:
    return {
        **os.environ,
        "PATH": "/usr/local/cargo/bin:/opt/verifier-venv/bin:/usr/local/bin:"
        + os.environ.get("PATH", ""),
        "CARGO_INCREMENTAL": "0",
    }


def reset() -> None:
    proc = subprocess.run(
        ["bash", str(APP / "scripts/reset-state.sh")],
        capture_output=True,
        text=True,
        env=_env(),
    )
    assert proc.returncode == 0, proc.stderr


def snapshot_sources() -> dict[str, bytes]:
    return {name: path.read_bytes() for name, path in MODULES.items()}


def restore_sources(saved: dict[str, bytes]) -> None:
    for name, data in saved.items():
        MODULES[name].write_bytes(data)
        os.utime(MODULES[name], None)


def restore_broken_sources() -> None:
    shutil.copyfile(BROKEN / "read.rs", MODULES["read"])
    shutil.copyfile(BROKEN / "gap.rs", MODULES["gap"])
    shutil.copyfile(BROKEN / "deadline.rs", MODULES["deadline"])
    shutil.copyfile(BROKEN / "sqlite.rs", MODULES["sqlite"])
    for path in MODULES.values():
        os.utime(path, None)


def install_golden_except(*broken: str) -> None:
    restore_broken_sources()
    broken_set = set(broken)
    for name, golden_name in GOLDEN_FILES.items():
        if name in broken_set:
            continue
        shutil.copyfile(GOLDEN / golden_name, MODULES[name])
        os.utime(MODULES[name], None)


def rebuild() -> None:
    proc = subprocess.run(
        ["cargo", "build", "--release", "--locked", "-p", "bag-audit"],
        cwd=str(APP),
        capture_output=True,
        text=True,
        env=_env(),
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    subprocess.run(
        ["install", "-m", "0755", str(APP / "target/release/bag-audit"), "/usr/local/bin/bag-audit"],
        check=True,
        env=_env(),
    )


def run_audit(bag_id: str, seed: int, speed: float, export: Path) -> subprocess.CompletedProcess[str]:
    export.parent.mkdir(parents=True, exist_ok=True)
    if export.exists():
        export.unlink()
    return subprocess.run(
        [
            "/usr/local/bin/bag-audit",
            "audit",
            "--bag",
            str(BAGS / bag_id),
            "--seed",
            str(seed),
            "--speed",
            str(speed),
            "--export",
            str(export),
        ],
        capture_output=True,
        text=True,
        cwd=str(APP),
        env=_env(),
    )


def assert_export_matches_reference(
    bag_id: str, seed: int, speed: float, export: Path
) -> None:
    meta, raw = load_bag(BAGS / bag_id)
    filled = fill_gaps(raw, seed)
    want_misses = find_deadline_misses(meta, filled, speed, seed)
    got_msgs, got_misses = read_sqlite(export)
    assert got_msgs == expected_message_rows(filled)
    assert got_misses == expected_miss_rows(want_misses)


@pytest.fixture(autouse=True)
def _restore_sources_after_partial() -> None:
    saved = snapshot_sources()
    yield
    restore_sources(saved)


class TestHardReferenceParity:
    @pytest.mark.parametrize("bag_id", ALL_BAGS)
    @pytest.mark.parametrize("seed", SEEDS)
    def test_bag_export_matches_reference(self, bag_id: str, seed: int) -> None:
        """Every catalog bag and seed must match independent reference export rows."""
        reset()
        export = OUTPUT / f"hard-{bag_id}-{seed}.sqlite"
        proc = run_audit(bag_id, seed, 1.0, export)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        assert publish_ns_monotonic_per_topic(export)
        assert_export_matches_reference(bag_id, seed, 1.0, export)

    @pytest.mark.parametrize("seed", SEEDS)
    def test_speed_factor_deadline_matrix(self, seed: int) -> None:
        """Replay speed must divide the deadline threshold for speed-factor."""
        reset()
        for speed, expect_misses in SPEED_MATRIX["speed-factor"]:
            export = OUTPUT / f"speed-factor-{speed}-{seed}.sqlite"
            proc = run_audit("speed-factor", seed, speed, export)
            assert proc.returncode == 0, proc.stderr
            assert_export_matches_reference("speed-factor", seed, speed, export)
            _, got_misses = read_sqlite(export)
            assert len(got_misses) == expect_misses

    @pytest.mark.parametrize("seed", SEEDS)
    def test_seed_ladder_matches_reference(self, seed: int) -> None:
        """seed-ladder effective deadline must follow qos-deadline seed adjustment."""
        reset()
        export = OUTPUT / f"seed-ladder-{seed}.sqlite"
        proc = run_audit("seed-ladder", seed, 1.0, export)
        assert proc.returncode == 0, proc.stderr
        assert_export_matches_reference("seed-ladder", seed, 1.0, export)

    def test_seed_ladder_miss_count_varies_by_seed(self) -> None:
        """Different seeds must not all produce identical deadline miss counts."""
        reset()
        counts: list[int] = []
        for seed in SEEDS:
            export = OUTPUT / f"seed-ladder-vary-{seed}.sqlite"
            proc = run_audit("seed-ladder", seed, 1.0, export)
            assert proc.returncode == 0, proc.stderr
            _, got_misses = read_sqlite(export)
            counts.append(len(got_misses))
        assert len(set(counts)) > 1


class TestHardIntegration:
    def setup_method(self) -> None:
        reset()

    def test_gap_dense_synthetic_payload_inheritance(self) -> None:
        """Six synthetic rows must inherit the lower neighbor payload before the payload switch."""
        seed = SEEDS[0]
        export = OUTPUT / "gap-dense-check.sqlite"
        proc = run_audit("gap-dense", seed, 1.0, export)
        assert proc.returncode == 0, proc.stderr
        meta, raw = load_bag(BAGS / "gap-dense")
        expected = fill_gaps(raw, seed)
        got_msgs, _ = read_sqlite(export)
        assert got_msgs == expected_message_rows(expected)
        synth = [row for row in got_msgs if int(row[5]) == 1]
        assert len(synth) == 6
        want_hash = payload_hash(bytes.fromhex("aa"))
        assert all(row[4] == want_hash for row in synth)

    def test_multi_topic_gap_isolated_per_topic(self) -> None:
        """Gap fill must run independently per canonical topic."""
        seed = SEEDS[2]
        export = OUTPUT / "multi-topic-gap.sqlite"
        proc = run_audit("multi-topic-gap", seed, 1.0, export)
        assert proc.returncode == 0, proc.stderr
        assert_export_matches_reference("multi-topic-gap", seed, 1.0, export)
        got_msgs, _ = read_sqlite(export)
        alpha = [row for row in got_msgs if row[0] == "/alpha"]
        beta = [row for row in got_msgs if row[0] == "/beta"]
        assert len(alpha) == 5
        assert len(beta) == 4
        assert payload_hash(bytes.fromhex("aa")) in {row[4] for row in alpha if int(row[5]) == 1}
        assert payload_hash(bytes.fromhex("0101")) in {row[4] for row in beta if int(row[5]) == 1}

    def test_payload_chain_long_gap_run(self) -> None:
        """A long missing seq run must keep the prior payload for every synthetic row."""
        seed = SEEDS[1]
        export = OUTPUT / "payload-chain.sqlite"
        proc = run_audit("payload-chain", seed, 1.0, export)
        assert proc.returncode == 0, proc.stderr
        got_msgs, _ = read_sqlite(export)
        want_hash = payload_hash(bytes.fromhex("aaaa"))
        synth = [row for row in got_msgs if int(row[5]) == 1]
        assert len(synth) == 6
        assert {row[4] for row in synth} == {want_hash}

    def test_combo_stack_remap_gap_deadline(self) -> None:
        """Remap decode, gap fill, and deadline detection must compose on one bag."""
        seed = SEEDS[0]
        export = OUTPUT / "combo-stack.sqlite"
        proc = run_audit("combo-stack", seed, 1.0, export)
        assert proc.returncode == 0, proc.stderr
        assert_export_matches_reference("combo-stack", seed, 1.0, export)
        got_msgs, got_misses = read_sqlite(export)
        topics = {row[0] for row in got_msgs}
        assert topics == {"/robot/cmd"}
        synth = [row for row in got_msgs if int(row[5]) == 1]
        assert len(synth) == 2
        assert len(got_misses) >= 1
        assert got_misses[0][0] == "/robot/cmd"

    def test_twin_deadline_topic_isolation(self) -> None:
        """Deadline misses must be evaluated per topic profile."""
        seed = SEEDS[3]
        export = OUTPUT / "twin-deadline.sqlite"
        proc = run_audit("twin-deadline", seed, 1.0, export)
        assert proc.returncode == 0, proc.stderr
        assert_export_matches_reference("twin-deadline", seed, 1.0, export)
        _, got_misses = read_sqlite(export)
        assert len(got_misses) == 1
        assert got_misses[0][0] == "/cmd"

    def test_dedupe_keeps_distinct_sequences(self) -> None:
        """Equal payload hash with different seq must persist both rows."""
        seed = SEEDS[2]
        export = OUTPUT / "dedupe.sqlite"
        proc = run_audit("dedupe-seq", seed, 1.0, export)
        assert proc.returncode == 0, proc.stderr
        assert_export_matches_reference("dedupe-seq", seed, 1.0, export)


class TestPartialFixTraps:
    def setup_method(self) -> None:
        reset()
        restore_broken_sources()
        rebuild()

    def test_partial_golden_without_gap_fails_payload_traps(self) -> None:
        """Correct read, deadline, and export cannot pass gap payload inheritance traps."""
        install_golden_except("gap")
        rebuild()
        for bag_id in GAP_TRAP_BAGS:
            export = OUTPUT / f"partial-gap-{bag_id}.sqlite"
            proc = run_audit(bag_id, SEEDS[0], 1.0, export)
            assert proc.returncode == 0, proc.stderr
            meta, raw = load_bag(BAGS / bag_id)
            want_rows = expected_message_rows(fill_gaps(raw, SEEDS[0]))
            got_msgs, _ = read_sqlite(export)
            assert got_msgs != want_rows, bag_id

    def test_partial_golden_without_deadline_fails_miss_traps(self) -> None:
        """Correct gap fill and export cannot pass deadline scheduling traps."""
        install_golden_except("deadline")
        rebuild()
        for bag_id, speed, seed in DEADLINE_TRAP_BAGS:
            export = OUTPUT / f"partial-deadline-{bag_id}.sqlite"
            proc = run_audit(bag_id, seed, speed, export)
            assert proc.returncode == 0, proc.stderr
            meta, raw = load_bag(BAGS / bag_id)
            filled = fill_gaps(raw, seed)
            want_misses = expected_miss_rows(find_deadline_misses(meta, filled, speed, seed))
            _, got_misses = read_sqlite(export)
            assert got_misses != want_misses, bag_id

    def test_partial_golden_without_read_fails_remap_traps(self) -> None:
        """Payload decode must use the raw topic before remap."""
        install_golden_except("read")
        rebuild()
        for bag_id in READ_TRAP_BAGS:
            export = OUTPUT / f"partial-read-{bag_id}.sqlite"
            proc = run_audit(bag_id, SEEDS[0], 1.0, export)
            assert proc.returncode == 0, proc.stderr
            meta, raw = load_bag(BAGS / bag_id)
            want_rows = expected_message_rows(fill_gaps(raw, SEEDS[0]))
            got_msgs, _ = read_sqlite(export)
            assert got_msgs != want_rows, bag_id

    def test_partial_golden_without_sqlite_fails_synthetic_flag(self) -> None:
        """Synthetic rows must be flagged in SQLite export."""
        install_golden_except("sqlite")
        rebuild()
        for bag_id in SQLITE_TRAP_BAGS:
            export = OUTPUT / f"partial-sqlite-{bag_id}.sqlite"
            proc = run_audit(bag_id, SEEDS[0], 1.0, export)
            assert proc.returncode == 0, proc.stderr
            meta, raw = load_bag(BAGS / bag_id)
            filled = fill_gaps(raw, SEEDS[0])
            expect_synth = sum(1 for msg in filled if msg.synthetic)
            got_msgs, _ = read_sqlite(export)
            got_synth = sum(1 for row in got_msgs if int(row[5]) == 1)
            assert expect_synth > 0
            assert got_synth == 0, bag_id


class TestCliAndFixtures:
    def setup_method(self) -> None:
        reset()

    def test_catalog_lists_bags(self) -> None:
        """Fixture catalog enumerates required bag ids."""
        assert set(CATALOG["bags"]) == set(ALL_BAGS)
        assert len(ALL_BAGS) == 11

    def test_rebuild_from_source(self) -> None:
        """cargo rebuild restores bag-audit and audit still succeeds."""
        rebuild()
        export = OUTPUT / "rebuild.sqlite"
        proc = run_audit("combo-stack", SEEDS[0], 1.0, export)
        assert proc.returncode == 0, proc.stderr
        assert_export_matches_reference("combo-stack", SEEDS[0], 1.0, export)

    def test_golden_modules_pass_full_matrix(self) -> None:
        """Oracle-equivalent modules must satisfy the full bag x seed matrix."""
        restore_broken_sources()
        install_golden_except()
        rebuild()
        for bag_id in ALL_BAGS:
            export = OUTPUT / f"golden-{bag_id}.sqlite"
            proc = run_audit(bag_id, SEEDS[0], 1.0, export)
            assert proc.returncode == 0, proc.stderr
            assert_export_matches_reference(bag_id, SEEDS[0], 1.0, export)
