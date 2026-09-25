"""Behavioral verifier for monitctl program restart cycle repair."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from reference_monit import load_json, replay_reference

APP = Path("/app")
FIXTURES = APP / "fixtures"
CONFIGS = FIXTURES / "configs"
SCENARIOS = FIXTURES / "scenarios"
OUTPUT = APP / "output"
CLI = "/app/bin/monitctl"
RESET = APP / "scripts" / "reset-state.sh"
SNAPSHOT = APP / "state" / "cycle-snapshot.json"
BROKEN = Path("/opt/verifier-broken-monit/lib")
GOLDEN = next(
    (p for p in (Path("/solution"), Path("/oracle/solution")) if (p / "golden_timeout_driver.sh").exists()),
    None,
)

CATALOG = [
    ("001-stop-timeout", "worker_alpha.json", "001-stop-timeout.json"),
    ("002-cycle-failed-start", "worker_beta.json", "002-cycle-failed-start.json"),
    ("003-onreboot-delay", "worker_gamma.json", "003-onreboot-delay.json"),
    ("004-stale-pidfile", "worker_delta.json", "004-stale-pidfile.json"),
    ("005-notify-order", "worker_epsilon.json", "005-notify-order.json"),
    ("006-combined-chain", "worker_zeta.json", "006-combined-chain.json"),
]


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False)


@pytest.fixture(autouse=True)
def reset_state() -> None:
    run(["bash", str(RESET)])


def replay_cli(config_name: str, scenario_name: str) -> subprocess.CompletedProcess[str]:
    export_path = OUTPUT / f"{scenario_name.replace('.json', '')}-report.json"
    cfg = CONFIGS / config_name
    sc = SCENARIOS / scenario_name
    run(["bash", CLI, "ingest", "--config", str(cfg), "--scenario", str(sc)])
    return run(
        [
            "bash",
            CLI,
            "replay",
            "--config",
            str(cfg),
            "--scenario",
            str(sc),
            "--export",
            str(export_path),
        ]
    )


def read_export(scenario_name: str) -> dict:
    path = OUTPUT / f"{scenario_name.replace('.json', '')}-report.json"
    return json.loads(path.read_text(encoding="utf-8"))


def reference_for(config_name: str, scenario_name: str) -> dict:
    cfg_path = CONFIGS / config_name
    sc_path = SCENARIOS / scenario_name
    raw = sc_path.read_bytes()
    cfg = load_json(cfg_path)
    sc = load_json(sc_path)
    snap_sha = None
    if SNAPSHOT.is_file():
        snap_sha = json.loads(SNAPSHOT.read_text(encoding="utf-8")).get("snapshot_sha256")
    return replay_reference(cfg, sc, raw, snapshot_sha=snap_sha)


@pytest.mark.parametrize("case,config_name,scenario_name", CATALOG)
def test_catalog_replay_matches_reference(case: str, config_name: str, scenario_name: str) -> None:
    """Each bundled scenario export must match independent reference FSM."""
    proc = replay_cli(config_name, scenario_name)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = read_export(scenario_name)
    want = reference_for(config_name, scenario_name)
    for key in (
        "restart_cycles_used",
        "stop_timeout_respected",
        "notify_before_idfile",
        "pidfile_stale_at_start",
        "final_state",
    ):
        assert got[key] == want[key], f"{case} field {key}"


def test_catalog_export_timeline_and_snapshot_sha256() -> None:
    """Replay export must include timeline and snapshot_sha256 per cli-surface.md."""
    config_name = "worker_alpha.json"
    scenario_name = "001-stop-timeout.json"
    proc = replay_cli(config_name, scenario_name)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = read_export(scenario_name)
    want = reference_for(config_name, scenario_name)
    assert got["timeline"] == want["timeline"]
    assert got["snapshot_sha256"] == want["snapshot_sha256"]
    assert len(got["snapshot_sha256"]) == 64


def test_hidden_export_timeline_and_snapshot_sha256() -> None:
    """Hidden replay export must carry timeline and ingest snapshot_sha256."""
    cfg = CONFIGS / "worker_zeta.json"
    sc = Path("/opt/verifier-fixtures/hidden-cycle-cap.json")
    export_path = OUTPUT / "hidden-cycle-meta-report.json"
    run(["bash", CLI, "ingest", "--config", str(cfg), "--scenario", str(sc)])
    proc = run(
        [
            "bash",
            CLI,
            "replay",
            "--config",
            str(cfg),
            "--scenario",
            str(sc),
            "--export",
            str(export_path),
        ]
    )
    assert proc.returncode == 0, proc.stderr
    got = json.loads(export_path.read_text(encoding="utf-8"))
    raw = sc.read_bytes()
    snap_sha = json.loads(SNAPSHOT.read_text(encoding="utf-8")).get("snapshot_sha256")
    want = replay_reference(load_json(cfg), load_json(sc), raw, snapshot_sha=snap_sha)
    assert got["timeline"] == want["timeline"]
    assert got["snapshot_sha256"] == want["snapshot_sha256"]


def test_staging_snapshot_written_on_ingest() -> None:
    """ingest must populate cycle-snapshot.json per staging-snapshot.md."""
    cfg = CONFIGS / "worker_alpha.json"
    sc = SCENARIOS / "001-stop-timeout.json"
    cfg_obj = load_json(cfg)
    sc_obj = load_json(sc)
    proc = run(["bash", CLI, "ingest", "--config", str(cfg), "--scenario", str(sc)])
    assert proc.returncode == 0
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert snap["program"] == "worker_alpha"
    assert snap["stop_timeout_sec"] == cfg_obj["stop_timeout_sec"]
    assert snap["start_delay_sec"] == cfg_obj["start_delay_sec"]
    assert snap["restart_limit"] == cfg_obj["restart_limit"]
    assert snap["scenario"] == sc_obj["name"]
    assert snap["event_count"] == len(sc_obj["events"])
    assert snap["snapshot_sha256"] == hashlib.sha256(sc.read_bytes()).hexdigest()
    assert len(snap["snapshot_sha256"]) == 64


def test_stop_timeout_scenario_deferred_in_reference() -> None:
    """Reference expects restart deferred when stop timeout not elapsed."""
    ref = reference_for("worker_alpha.json", "001-stop-timeout.json")
    assert ref["stop_timeout_respected"] is False
    steps = [s["step"] for s in ref["timeline"]]
    assert "restart_deferred" in steps


def test_failed_start_does_not_consume_cycle_in_reference() -> None:
    """Reference counts only running transitions toward restart_cycles_used."""
    ref = reference_for("worker_beta.json", "002-cycle-failed-start.json")
    assert ref["restart_cycles_used"] == 1


def test_onreboot_skips_start_delay_in_reference() -> None:
    """Onreboot boot must not apply positive start delay."""
    ref = reference_for("worker_gamma.json", "003-onreboot-delay.json")
    running = [s for s in ref["timeline"] if s["step"] == "running"]
    assert running and running[0]["t"] == 0


def test_unclean_kill_clears_stale_pidfile_in_reference() -> None:
    """After unclean kill, restart must not leave pidfile_stale_at_start true."""
    ref = reference_for("worker_delta.json", "004-stale-pidfile.json")
    assert ref["pidfile_stale_at_start"] is False


def test_notify_idfile_order_in_reference() -> None:
    """Notify must not precede idfile write."""
    ref = reference_for("worker_epsilon.json", "005-notify-order.json")
    assert ref["notify_before_idfile"] is False


def test_hidden_rapid_restart_matches_reference() -> None:
    """Hidden fixture under /opt/verifier-fixtures must match reference."""
    cfg = CONFIGS / "worker_alpha.json"
    sc = Path("/opt/verifier-fixtures/hidden-rapid-restart.json")
    export_path = OUTPUT / "hidden-rapid-report.json"
    run(["bash", CLI, "ingest", "--config", str(cfg), "--scenario", str(sc)])
    proc = run(
        [
            "bash",
            CLI,
            "replay",
            "--config",
            str(cfg),
            "--scenario",
            str(sc),
            "--export",
            str(export_path),
        ]
    )
    assert proc.returncode == 0, proc.stderr
    got = json.loads(export_path.read_text(encoding="utf-8"))
    raw = sc.read_bytes()
    want = replay_reference(load_json(cfg), load_json(sc), raw)
    for key in (
        "restart_cycles_used",
        "stop_timeout_respected",
        "notify_before_idfile",
        "pidfile_stale_at_start",
        "final_state",
    ):
        assert got[key] == want[key], f"hidden rapid field {key}"


def test_hidden_cycle_cap_matches_reference() -> None:
    """Hidden cycle cap scenario must exhaust restart limit correctly."""
    cfg = CONFIGS / "worker_zeta.json"
    sc = Path("/opt/verifier-fixtures/hidden-cycle-cap.json")
    export_path = OUTPUT / "hidden-cycle-report.json"
    run(["bash", CLI, "ingest", "--config", str(cfg), "--scenario", str(sc)])
    proc = run(
        [
            "bash",
            CLI,
            "replay",
            "--config",
            str(cfg),
            "--scenario",
            str(sc),
            "--export",
            str(export_path),
        ]
    )
    assert proc.returncode == 0, proc.stderr
    got = json.loads(export_path.read_text(encoding="utf-8"))
    raw = sc.read_bytes()
    want = replay_reference(load_json(cfg), load_json(sc), raw)
    for key in (
        "restart_cycles_used",
        "stop_timeout_respected",
        "notify_before_idfile",
        "pidfile_stale_at_start",
        "final_state",
    ):
        assert got[key] == want[key], f"hidden cycle cap field {key}"


def test_tb3_scenario_dir_override() -> None:
    """TB3_SCENARIO_DIR replaces bundled scenario lookup root."""
    tb3 = Path(tempfile.mkdtemp(prefix="tb3-monit-"))
    try:
        sc_src = SCENARIOS / "003-onreboot-delay.json"
        shutil.copy2(sc_src, tb3 / "003-onreboot-delay.json")
        os.environ["TB3_SCENARIO_DIR"] = str(tb3)
        cfg = CONFIGS / "worker_gamma.json"
        export_path = OUTPUT / "tb3-onreboot-report.json"
        run(["bash", CLI, "ingest", "--config", str(cfg), "--scenario", "003-onreboot-delay.json"])
        proc = run(
            [
                "bash",
                CLI,
                "replay",
                "--config",
                str(cfg),
                "--scenario",
                "003-onreboot-delay.json",
                "--export",
                str(export_path),
            ]
        )
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = json.loads(export_path.read_text(encoding="utf-8"))
        want = reference_for("worker_gamma.json", "003-onreboot-delay.json")
        assert got["final_state"] == want["final_state"]
        assert got["final_state"] == "running"
    finally:
        os.environ.pop("TB3_SCENARIO_DIR", None)
        shutil.rmtree(tb3, ignore_errors=True)


def test_single_timeout_patch_insufficient() -> None:
    """Fixing timeout_driver alone must not pass full catalog."""
    if not GOLDEN or not BROKEN.is_dir():
        pytest.skip("oracle golden or broken lib snapshot not mounted")
    lib = APP / "lib"
    tmp = Path(tempfile.mkdtemp())
    backed: dict[str, Path] = {}
    try:
        for src in lib.glob("*.sh"):
            bak = tmp / src.name
            shutil.copy2(src, bak)
            backed[src.name] = bak
        for src in BROKEN.glob("*.sh"):
            shutil.copy2(src, lib / src.name)
        shutil.copy2(GOLDEN / "golden_timeout_driver.sh", lib / "timeout_driver.sh")
        failed = 0
        for _, config_name, scenario_name in CATALOG:
            proc = replay_cli(config_name, scenario_name)
            if proc.returncode != 0:
                failed += 1
                continue
            got = read_export(scenario_name)
            want = reference_for(config_name, scenario_name)
            if any(got[k] != want[k] for k in (
                "restart_cycles_used",
                "stop_timeout_respected",
                "notify_before_idfile",
                "pidfile_stale_at_start",
                "final_state",
            )):
                failed += 1
        assert failed >= 4
    finally:
        for name, bak in backed.items():
            shutil.copy2(bak, lib / name)
        shutil.rmtree(tmp, ignore_errors=True)


def test_decoy_check_syntax_patch_insufficient() -> None:
    """Patching check_syntax decoy must not fix replay exports."""
    if not BROKEN.is_dir():
        pytest.skip("broken lib snapshot missing")
    lib = APP / "lib"
    tmp = Path(tempfile.mkdtemp())
    backed: dict[str, Path] = {}
    try:
        for src in lib.glob("*.sh"):
            bak = tmp / src.name
            shutil.copy2(src, bak)
            backed[src.name] = bak
        for src in BROKEN.glob("*.sh"):
            shutil.copy2(src, lib / src.name)
        # Agent only "fixes" the decoy module — hot-path policy hooks stay broken.
        (lib / "check_syntax.sh").write_text(
            "#!/usr/bin/env bash\nmonit_parse_check_line() { echo ok; }\n",
            encoding="utf-8",
        )
        proc = replay_cli("worker_alpha.json", "001-stop-timeout.json")
        assert proc.returncode == 0
        got = read_export("001-stop-timeout.json")
        want = reference_for("worker_alpha.json", "001-stop-timeout.json")
        assert got != want
    finally:
        for name, bak in backed.items():
            shutil.copy2(bak, lib / name)
        shutil.rmtree(tmp, ignore_errors=True)
