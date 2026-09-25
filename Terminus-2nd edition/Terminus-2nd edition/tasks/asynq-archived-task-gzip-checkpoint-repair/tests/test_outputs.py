"""Behavioral verifier for archctl gzip archive / restore / purge pipeline."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
from pathlib import Path

import pytest
from reference_archive import (
    last_win_tasks,
    load_index,
    member_footer_valid,
    reference_manifest,
)

APP = Path("/app")
ARCHCTL = Path("/usr/local/bin/archctl")
RESET = APP / "scripts" / "reset-state.sh"
STAGING = APP / "state" / "archive-snapshot.json"
ARCHIVE_DIR = APP / "work" / "archives"
QUEUE_DB = APP / "work" / "queue.db"
SEEDS = json.loads((APP / "fixtures" / "seeds.json").read_text(encoding="utf-8"))[
    "seeds"
]
DEFAULT_HIDDEN = Path("/opt/verifier-fixtures/asynq")

SCENARIOS = [
    "baseline-tasks",
    "duplicate-ids",
    "priority-mismatch",
    "partial-member",
    "retention-skew",
]

PROTECTED_SHA256 = {
    "config/queue.json": "57c57999627ea193b3371e2206a99d54c14ade84ee20dc3b7c42854d5a377222",
    "docs/archive-format.md": "e5592aacd4db0984e05cedbb759ee622dff5f9bf16140f266f8ac4e9e8120fe4",
    "docs/checkpoint-index.md": "1ce03ef1d0aaaee9fd5b27c8b2664ff818134d6e309fd31f4d9c9e452d9d3e82",
    "docs/cli-surface.md": "2cbcdf3c28ec3203cca86c1bf5f6c322558fd664416ffd76d46796a542c2e1d2",
    "docs/fixture-catalog.md": "e3c2d0b96f165300b7ace9ebeaa99ff7eaeeda40a06fdd4d5b611b82c35c8244",
    "docs/queue-priority.md": "995d0e1c9e21e20f9fad0d8e5b9b0b843a90141e08e8b0307296257aebf7fc72",
    "docs/restore-import.md": "3c7ee9d20f511cc169403e3726a4bf7698c5fdd3fd756f7f48047761181c26b6",
    "docs/retention-purge.md": "bf3c77737fd6c53401bc7fe9c6784dcf5f95836175282f3a772089c2b03cc511",
}


def hidden_root() -> Path:
    override = os.environ.get("TB3_ARCHIVE_FIXTURES", "").strip()
    return Path(override) if override else DEFAULT_HIDDEN


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd, cwd=str(APP), capture_output=True, text=True, check=False
    )


def reset() -> None:
    proc = run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def seed_archive_restore(seed: str, scenario: str) -> Path:
    for step in (
        [str(ARCHCTL), "seed", "--seed", seed, "--scenario", scenario],
        [str(ARCHCTL), "archive", "--seed", seed, "--scenario", scenario],
        [str(ARCHCTL), "restore", "--seed", seed, "--scenario", scenario],
    ):
        proc = run(step)
        assert proc.returncode == 0, proc.stderr + proc.stdout
    out = APP / "output" / f"{seed}-{scenario}-manifest.json"
    proc = run(
        [
            str(ARCHCTL),
            "manifest",
            "--seed",
            seed,
            "--scenario",
            scenario,
            "--output",
            str(out),
        ]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return out


def install_hidden_scenario(name: str) -> Path:
    src = hidden_root() / "scenarios" / f"{name}.jsonl"
    if not src.is_file():
        pytest.skip(f"hidden fixture not mounted: {src}")
    dest = APP / "fixtures" / "scenarios" / f"{name}.jsonl"
    dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    return dest


def read_manifest(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def pending_rows() -> list[tuple]:
    conn = sqlite3.connect(QUEUE_DB)
    try:
        return conn.execute(
            "SELECT id, priority, retry FROM pending ORDER BY priority ASC, id ASC"
        ).fetchall()
    finally:
        conn.close()


def archived_count() -> int:
    conn = sqlite3.connect(QUEUE_DB)
    try:
        return conn.execute("SELECT COUNT(*) FROM archived").fetchone()[0]
    finally:
        conn.close()


class TestProtectedAssets:
    def test_protected_docs_and_config_unmodified(self) -> None:
        """Config and contract docs under /app must remain unchanged."""
        for rel, expected in PROTECTED_SHA256.items():
            path = APP / rel
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            assert digest == expected, rel


class TestBinarySurface:
    def test_archctl_binary_executable(self) -> None:
        """Verifier rebuild must leave an executable archctl on PATH."""
        assert ARCHCTL.is_file()
        assert os.access(ARCHCTL, os.X_OK)


class TestSeedQueue:
    def test_seed_loads_pending_rows(self) -> None:
        """Seed populates SQLite pending from scenario JSONL."""
        reset()
        seed = SEEDS[0]
        scenario = "baseline-tasks"
        proc = run([str(ARCHCTL), "seed", "--seed", seed, "--scenario", scenario])
        assert proc.returncode == 0, proc.stderr
        rows = pending_rows()
        assert len(rows) == 3
        assert all(r[0].startswith(f"{seed}:") for r in rows)


class TestStagingSnapshot:
    def test_archive_writes_staging_snapshot(self) -> None:
        """Archive must emit /app/state/archive-snapshot.json with ordered ids."""
        reset()
        seed = SEEDS[0]
        scenario = "baseline-tasks"
        proc = run([str(ARCHCTL), "seed", "--seed", seed, "--scenario", scenario])
        assert proc.returncode == 0
        proc = run([str(ARCHCTL), "archive", "--seed", seed, "--scenario", scenario])
        assert proc.returncode == 0
        snap = json.loads(STAGING.read_text(encoding="utf-8"))
        assert snap["seed"] == seed
        assert snap["scenario"] == scenario
        assert len(snap["ordered_ids"]) == 3

    def test_staging_ordered_ids_stable_across_archive_replay(self) -> None:
        """Re-running archive after reset+seed must persist the same ordered_ids sequence."""
        reset()
        seed = SEEDS[1]
        scenario = "baseline-tasks"
        run([str(ARCHCTL), "seed", "--seed", seed, "--scenario", scenario])
        run([str(ARCHCTL), "archive", "--seed", seed, "--scenario", scenario])
        first = json.loads(STAGING.read_text(encoding="utf-8"))["ordered_ids"]
        reset()
        run([str(ARCHCTL), "seed", "--seed", seed, "--scenario", scenario])
        run([str(ARCHCTL), "archive", "--seed", seed, "--scenario", scenario])
        second = json.loads(STAGING.read_text(encoding="utf-8"))["ordered_ids"]
        assert first == second


class TestArchiveArtifacts:
    def test_archive_creates_bundle_and_index(self) -> None:
        """Archive writes both .bundle and .idx.json sidecars."""
        reset()
        seed = SEEDS[0]
        scenario = "baseline-tasks"
        run([str(ARCHCTL), "seed", "--seed", seed, "--scenario", scenario])
        run([str(ARCHCTL), "archive", "--seed", seed, "--scenario", scenario])
        bundle = ARCHIVE_DIR / f"{seed}-{scenario}.bundle"
        idx = ARCHIVE_DIR / f"{seed}-{scenario}.idx.json"
        assert bundle.is_file() and bundle.stat().st_size > 0
        assert idx.is_file()
        data = load_index(idx)
        assert data.get("version") == 1
        assert data.get("members")

    def test_index_task_locs_cover_seeded_ids(self) -> None:
        """Index task locations must cover every staged ordered id."""
        reset()
        seed = SEEDS[2]
        scenario = "baseline-tasks"
        run([str(ARCHCTL), "seed", "--seed", seed, "--scenario", scenario])
        run([str(ARCHCTL), "archive", "--seed", seed, "--scenario", scenario])
        snap = json.loads(STAGING.read_text(encoding="utf-8"))
        idx = load_index(ARCHIVE_DIR / f"{seed}-{scenario}.idx.json")
        located = {t["id"] for t in idx.get("tasks", [])}
        assert set(snap["ordered_ids"]) <= located


class TestGzipFooterCheckpoint:
    def test_index_member_sizes_include_gzip_footer(self) -> None:
        """Each indexed gzip member must include a valid footer span."""
        reset()
        seed = SEEDS[1]
        scenario = "baseline-tasks"
        run([str(ARCHCTL), "seed", "--seed", seed, "--scenario", scenario])
        run([str(ARCHCTL), "archive", "--seed", seed, "--scenario", scenario])
        bundle = ARCHIVE_DIR / f"{seed}-{scenario}.bundle"
        idx = load_index(ARCHIVE_DIR / f"{seed}-{scenario}.idx.json")
        for member in idx["members"]:
            assert member_footer_valid(bundle, member), member


class TestRestoreDedupe:
    def test_restore_last_duplicate_id_wins_across_members(self) -> None:
        """Duplicate task ids across gzip members keep the last archived body."""
        reset()
        seed = "dupseed"
        scenario = "duplicate-ids"
        manifest_path = seed_archive_restore(seed, scenario)
        manifest = read_manifest(manifest_path)
        ns = f"{seed}:dup-1"
        assert manifest["priorities"][ns] == 50
        assert manifest["retries"][ns] == 0
        rows = pending_rows()
        ids = [r[0] for r in rows]
        assert ids.count(ns) == 1

    def test_restore_pending_count_matches_unique_ids(self) -> None:
        """After restore, pending row count equals unique last-win task ids."""
        reset()
        seed = "dupseed"
        scenario = "duplicate-ids"
        seed_archive_restore(seed, scenario)
        bundle = ARCHIVE_DIR / f"{seed}-{scenario}.bundle"
        idx = load_index(ARCHIVE_DIR / f"{seed}-{scenario}.idx.json")
        unique = last_win_tasks(bundle, idx)
        assert len(pending_rows()) == len(unique)


class TestPriorityRestore:
    def test_restore_preserves_priority_not_retry(self) -> None:
        """Restored pending priority must match archived priority field."""
        reset()
        seed = SEEDS[2]
        scenario = "priority-mismatch"
        manifest_path = seed_archive_restore(seed, scenario)
        manifest = read_manifest(manifest_path)
        for tid, priority in manifest["priorities"].items():
            retry = manifest["retries"][tid]
            if retry != priority:
                assert manifest["priorities"][tid] == priority
                conn = sqlite3.connect(QUEUE_DB)
                try:
                    row = conn.execute(
                        "SELECT priority, retry FROM pending WHERE id = ?", (tid,)
                    ).fetchone()
                finally:
                    conn.close()
                assert row[0] == priority
                assert row[0] != row[1] or priority == retry


class TestPartialMemberIndex:
    def test_partial_member_does_not_break_first_member_restore(self) -> None:
        """First complete gzip member remains readable when later member is partial."""
        reset()
        seed = "partial"
        scenario = "partial-member"
        run([str(ARCHCTL), "seed", "--seed", seed, "--scenario", scenario])
        run([str(ARCHCTL), "archive", "--seed", seed, "--scenario", scenario])
        bundle = ARCHIVE_DIR / f"{seed}-{scenario}.bundle"
        idx = load_index(ARCHIVE_DIR / f"{seed}-{scenario}.idx.json")
        assert idx["members"], "expected at least one indexed member"
        tasks = last_win_tasks(bundle, idx)
        assert len(tasks) >= 2
        proc = run([str(ARCHCTL), "restore", "--seed", seed, "--scenario", scenario])
        assert proc.returncode == 0, proc.stderr


class TestRetentionPurge:
    def test_purge_uses_utc_cutoff(self) -> None:
        """Purge drops archived rows strictly older than UTC cutoff."""
        reset()
        seed = "retain"
        scenario = "retention-skew"
        run([str(ARCHCTL), "seed", "--seed", seed, "--scenario", scenario])
        run([str(ARCHCTL), "archive", "--seed", seed, "--scenario", scenario])
        before = archived_count()
        assert before == 3
        proc = run(
            [
                str(ARCHCTL),
                "purge",
                "--before",
                "2025-01-01T00:00:00Z",
            ]
        )
        assert proc.returncode == 0, proc.stderr
        after = archived_count()
        assert after == 2

    def test_purge_far_future_cutoff_clears_all(self) -> None:
        """A far-future UTC cutoff must purge every archived row."""
        reset()
        seed = "retain"
        scenario = "retention-skew"
        run([str(ARCHCTL), "seed", "--seed", seed, "--scenario", scenario])
        run([str(ARCHCTL), "archive", "--seed", seed, "--scenario", scenario])
        proc = run([str(ARCHCTL), "purge", "--before", "2099-01-01T00:00:00Z"])
        assert proc.returncode == 0, proc.stderr
        assert archived_count() == 0


class TestManifestExport:
    def test_manifest_matches_reference_walker(self) -> None:
        """Exported manifest must match independent archive walker + staging snapshot."""
        reset()
        seed = SEEDS[0]
        scenario = "baseline-tasks"
        manifest_path = seed_archive_restore(seed, scenario)
        staging = json.loads(STAGING.read_text(encoding="utf-8"))
        bundle = ARCHIVE_DIR / f"{seed}-{scenario}.bundle"
        idx_path = ARCHIVE_DIR / f"{seed}-{scenario}.idx.json"
        expected = reference_manifest(staging, bundle, idx_path)
        actual = read_manifest(manifest_path)
        assert actual == expected

    def test_manifest_ordered_ids_match_staging_snapshot(self) -> None:
        """Manifest ordered_ids must follow the staging snapshot, not a live queue scan alone."""
        reset()
        seed = SEEDS[0]
        scenario = "baseline-tasks"
        manifest_path = seed_archive_restore(seed, scenario)
        staging = json.loads(STAGING.read_text(encoding="utf-8"))
        actual = read_manifest(manifest_path)
        assert actual["ordered_ids"] == staging["ordered_ids"]

    def test_manifest_export_idempotent_on_rerun(self) -> None:
        """Re-exporting the same manifest path must persist identical JSON."""
        reset()
        seed = SEEDS[1]
        scenario = "baseline-tasks"
        first = seed_archive_restore(seed, scenario)
        a = first.read_text(encoding="utf-8")
        proc = run(
            [
                str(ARCHCTL),
                "manifest",
                "--seed",
                seed,
                "--scenario",
                scenario,
                "--output",
                str(first),
            ]
        )
        assert proc.returncode == 0
        assert first.read_text(encoding="utf-8") == a


class TestDecoyModule:
    def test_decoy_wrap_module_present_off_hot_path(self) -> None:
        """Legacy decoy wrap module must exist but stay unused by archive export."""
        wrap = APP / "internal" / "decoy" / "wrap.go"
        assert wrap.is_file()
        body = wrap.read_text(encoding="utf-8")
        assert "package decoy" in body
        assert "WrapTasks" in body


class TestHiddenFixtures:
    def test_hidden_duplicate_members_restore(self) -> None:
        """Hidden /opt/verifier-fixtures duplicate ids across members restore with last win."""
        install_hidden_scenario("hidden-dup-members")
        reset()
        seed = "TB3H"
        scenario = "hidden-dup-members"
        manifest_path = seed_archive_restore(seed, scenario)
        manifest = read_manifest(manifest_path)
        ns = f"{seed}:hidden-dup"
        assert manifest["priorities"][ns] == 15
        assert manifest["retries"][ns] == 3

    def test_hidden_priority_trap_last_win(self) -> None:
        """Hidden /opt/verifier-fixtures priority trap keeps last archived priority/retry."""
        install_hidden_scenario("hidden-priority-trap")
        reset()
        seed = "TB3H"
        scenario = "hidden-priority-trap"
        manifest_path = seed_archive_restore(seed, scenario)
        manifest = read_manifest(manifest_path)
        ns = f"{seed}:trap-keep"
        assert manifest["priorities"][ns] == 9
        assert manifest["retries"][ns] == 7
        assert f"{seed}:trap-solo" in manifest["priorities"]
