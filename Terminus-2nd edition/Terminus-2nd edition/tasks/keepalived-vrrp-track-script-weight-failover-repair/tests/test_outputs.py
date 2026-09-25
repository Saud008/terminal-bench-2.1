"""Verifier for keepalived VRRP track-script weight failover simulator."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest

from reference_vrrp import (
    build_seed_events,
    config_check,
    replay_events,
)

APP = Path("/app")
CONFIG = APP / "config" / "vrrp.json"
KEEPALIVED = APP / "config" / "keepalived.sample.conf"
EVENT_DIR = APP / "fixtures" / "events"
HIDDEN = Path("/opt/verifier-fixtures/events")
STATE = APP / "state"
OUTPUT = APP / "output"
GRAPH = OUTPUT / "vrrp-state.json"
SNAPSHOT = STATE / "staging-snapshot.json"
MANIFEST = STATE / "staging-manifest.json"
EXPORT_READY = STATE / "export-ready"
NOTIFY_DONE = STATE / "notify.done"
CLI = APP / "bin" / "kv-sim"

FIXTURES = sorted(EVENT_DIR.glob("*.jsonl"))


def run_replay(events: Path, output: Path = GRAPH) -> subprocess.CompletedProcess[str]:
    subprocess.run(["bash", str(APP / "scripts" / "reset-state.sh")], check=True)
    return subprocess.run(
        [
            "kv-sim",
            "replay",
            "--events",
            str(events),
            "--config",
            str(CONFIG),
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def run_config_check() -> subprocess.CompletedProcess[str]:
    subprocess.run(["bash", str(APP / "scripts" / "reset-state.sh")], check=True)
    return subprocess.run(
        [
            "kv-sim",
            "config-check",
            "--config",
            str(KEEPALIVED),
            "--vrrp-json",
            str(CONFIG),
            "--output",
            str(OUTPUT / "config-report.json"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


class TestVrrpAntiCheat:
    """Hidden and seeded inputs must match independent reference math."""

    def test_seed_matches_reference_not_catalog(self) -> None:
        """Seeded event stream must match reference replay, not bundled fixtures."""
        seed = os.environ.get("VERIFIER_SEED", "keepalived-vrrp-track-script-weight-failover-repair")
        with tempfile.TemporaryDirectory() as tmp:
            seed_path = Path(tmp) / "seed.jsonl"
            seed_path.write_text(build_seed_events(seed), encoding="utf-8")
            expected_snap, expected_graph = replay_events(seed_path, CONFIG)
            proc = run_replay(seed_path)
            assert proc.returncode == 0, proc.stderr + proc.stdout
            snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
            got = json.loads(GRAPH.read_text(encoding="utf-8"))
            assert snap == expected_snap
            assert got == expected_graph

    def test_hidden_dual_track_fixture(self) -> None:
        """Hidden fixture requires both simultaneous fall weights in config order."""
        hidden = HIDDEN / "hidden-dual-track.jsonl"
        assert hidden.is_file()
        expected_snap, expected_graph = replay_events(hidden, CONFIG)
        proc = run_replay(hidden)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        got = json.loads(GRAPH.read_text(encoding="utf-8"))
        assert snap == expected_snap
        assert got == expected_graph
        names = {w["track"] for w in got["active_weights"]}
        assert names == {"chk_nginx", "chk_redis"}


class TestKeepalivedVrrp:
    """Bundled fixtures and behavioral traps for kv-sim replay."""

    @pytest.mark.parametrize("fixture_path", FIXTURES, ids=lambda p: p.name)
    def test_fixture_matches_reference(self, fixture_path: Path) -> None:
        """Each catalog fixture must match independent reference staging and export."""
        expected_snap, expected_graph = replay_events(fixture_path, CONFIG)
        proc = run_replay(fixture_path)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        graph = json.loads(GRAPH.read_text(encoding="utf-8"))
        assert snap == expected_snap
        assert graph == expected_graph

    def test_missing_input_exits_nonzero(self) -> None:
        """Replay must fail when events file is missing."""
        proc = run_replay(APP / "fixtures" / "events" / "missing.jsonl")
        assert proc.returncode != 0

    def test_priority_floor_after_combined_weights(self) -> None:
        """002 combined weights must clamp at priority_floor after sum."""
        fixture = EVENT_DIR / "002-weight-floor.jsonl"
        expected_snap, _ = replay_events(fixture, CONFIG)
        proc = run_replay(fixture)
        assert proc.returncode == 0
        snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        assert snap["effective_priority"] == expected_snap["effective_priority"] == 90

    def test_advert_resets_on_master_demotion(self) -> None:
        """003 demotion from track fail must reset advert_seq to zero."""
        fixture = EVENT_DIR / "003-advert-reset.jsonl"
        expected_snap, expected_graph = replay_events(fixture, CONFIG)
        proc = run_replay(fixture)
        assert proc.returncode == 0
        snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        graph = json.loads(GRAPH.read_text(encoding="utf-8"))
        assert snap["advert_seq"] == expected_snap["advert_seq"] == 0
        assert graph["advert_seq"] == 0

    def test_notify_barrier_before_export(self) -> None:
        """004 role transition must complete notify before durable export."""
        fixture = EVENT_DIR / "004-notify-order.jsonl"
        proc = run_replay(fixture)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        assert NOTIFY_DONE.is_file(), "notify.done missing after transition"
        assert EXPORT_READY.is_file(), "export-ready marker missing"
        assert EXPORT_READY.read_text(encoding="utf-8").strip() == GRAPH.name

    def test_recovery_refreshes_effective_priority(self) -> None:
        """005 rise must clear weight and refresh effective_priority."""
        fixture = EVENT_DIR / "005-recovery.jsonl"
        expected_snap, _ = replay_events(fixture, CONFIG)
        proc = run_replay(fixture)
        assert proc.returncode == 0
        snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        assert snap["effective_priority"] == expected_snap["effective_priority"] == 100
        assert not snap["tracks"]["chk_redis"]["weight_active"]

    def test_dual_race_activates_both_tracks(self) -> None:
        """006 simultaneous fall must activate every qualifying track."""
        fixture = EVENT_DIR / "006-dual-race.jsonl"
        expected_snap, expected_graph = replay_events(fixture, CONFIG)
        proc = run_replay(fixture)
        assert proc.returncode == 0
        snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        graph = json.loads(GRAPH.read_text(encoding="utf-8"))
        assert len(graph["active_weights"]) == len(expected_graph["active_weights"]) == 2
        assert snap == expected_snap

    def test_replay_duplicate_event_id_idempotent(self) -> None:
        """007 duplicate event_id must not double-apply track weight."""
        fixture = EVENT_DIR / "007-replay-dup.jsonl"
        expected_snap, expected_graph = replay_events(fixture, CONFIG)
        proc = run_replay(fixture)
        assert proc.returncode == 0
        snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        graph = json.loads(GRAPH.read_text(encoding="utf-8"))
        assert snap == expected_snap
        assert graph == expected_graph
        assert len(snap["applied_event_ids"]) == 1

    def test_manifest_binds_input_bytes(self) -> None:
        """Staging manifest must hash raw input and snapshot bytes."""
        fixture = EVENT_DIR / "006-dual-race.jsonl"
        expected_snap, _ = replay_events(fixture, CONFIG)
        proc = run_replay(fixture)
        assert proc.returncode == 0
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        digest = hashlib.sha256(fixture.read_bytes()).hexdigest()
        assert manifest["input_sha256"] == digest
        snap_digest = hashlib.sha256(SNAPSHOT.read_bytes()).hexdigest()
        assert manifest["snapshot_sha256"] == snap_digest
        snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        assert snap == expected_snap

    def test_config_check_runs_track_scripts(self) -> None:
        """config-check must execute track scripts and report exit codes."""
        expected = config_check(KEEPALIVED, CONFIG)
        proc = run_config_check()
        assert proc.returncode == 0, proc.stderr + proc.stdout
        report = json.loads((OUTPUT / "config-report.json").read_text(encoding="utf-8"))
        assert report == expected
        assert report["all_scripts_ok"] is True
        assert len(report["scripts_run"]) == 3

    def test_export_no_tmp_sidecar(self) -> None:
        """Published graph must not leave vrrp-state.json.tmp behind after replay."""
        fixture = EVENT_DIR / "001-single-fail.jsonl"
        proc = run_replay(fixture)
        assert proc.returncode == 0
        assert GRAPH.is_file()
        assert not GRAPH.with_suffix(GRAPH.suffix + ".tmp").exists()
