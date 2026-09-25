"""Behavioral verifier for syslog-ng filter graph replay pipeline."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from reference_syslog import evaluate


APP = Path("/app")
OUT = APP / "output"
STATE = APP / "state"
FIX_CFG = APP / "fixtures" / "configs" / "base"
FIX_MSG = APP / "fixtures" / "messages"


def _run_replay(
    config_dir: Path,
    messages: Path,
    seed: str,
    export_path: Path,
    reload: str = "full",
    reset: bool = True,
) -> tuple[dict, dict]:
    if reset:
        subprocess.run(["bash", "/app/scripts/reset-state.sh"], check=True)
    cmd = [
        "/app/bin/syslogctl",
        "replay",
        "--config-dir",
        str(config_dir),
        "--messages",
        str(messages),
        "--seed",
        seed,
        "--export",
        str(export_path),
        "--reload",
        reload,
    ]
    subprocess.run(cmd, check=True)
    report = json.loads(export_path.read_text(encoding="utf-8"))
    snapshot = json.loads((STATE / "routing-snapshot.json").read_text(encoding="utf-8"))
    return report, snapshot


def test_replay_matches_reference_on_base_fixture() -> None:
    """Primary fixture deliveries and snapshot must match independent evaluator."""
    messages = FIX_MSG / "base.log"
    export = OUT / "base-report.json"
    report, snapshot = _run_replay(FIX_CFG, messages, "seed-base", export)
    expected_report, expected_snapshot = evaluate(FIX_CFG, messages, "seed-base")
    assert report == expected_report
    assert snapshot == expected_snapshot


def test_and_or_precedence_without_extra_parens() -> None:
    """route_combo must treat AND as tighter binding than OR."""
    messages = FIX_MSG / "base.log"
    export = OUT / "nested-report.json"
    report, _ = _run_replay(FIX_CFG, messages, "seed-nested", export)
    expected, _ = evaluate(FIX_CFG, messages, "seed-nested")
    assert report["deliveries"] == expected["deliveries"]
    ops = next((d for d in report["deliveries"] if d["destination"] == "dest_ops"), None)
    expected_ops = next((d for d in expected["deliveries"] if d["destination"] == "dest_ops"), None)
    assert ops == expected_ops


def test_rewrite_runs_after_facility_gate() -> None:
    """Messages dropped at facility gate must not receive rewrite prefixes."""
    cfg = OUT / "gate-cfg"
    shutil.rmtree(cfg, ignore_errors=True)
    shutil.copytree(FIX_CFG, cfg)
    msg = OUT / "gate-msg.log"
    msg.write_text("x1,unknown,info,daemon,hostX,blocked\n", encoding="utf-8")
    export = OUT / "gate-report.json"
    report, _ = _run_replay(cfg, msg, "seed-gate", export)
    expected, _ = evaluate(cfg, msg, "seed-gate")
    assert report["dropped_at_facility_gate"] == 1
    assert report["rewrite_applied"] == 0
    assert report == expected


def test_prune_keeps_rewrite_referenced_dead_routes() -> None:
    """Dead routes whose filter_id is used by rewrites must stay in active_routes."""
    messages = FIX_MSG / "alt.log"
    export = OUT / "prune-report.json"
    _, snapshot = _run_replay(FIX_CFG, messages, "seed-prune", export)
    _, expected_snapshot = evaluate(FIX_CFG, messages, "seed-prune")
    assert "route_retired" in expected_snapshot["active_routes"]
    assert snapshot["active_routes"] == expected_snapshot["active_routes"]


def test_fallback_dead_route_is_retained() -> None:
    """fallback=1 routes must survive dead-branch pruning."""
    messages = FIX_MSG / "base.log"
    export = OUT / "fallback-report.json"
    _, snapshot = _run_replay(FIX_CFG, messages, "seed-fallback", export)
    _, expected_snapshot = evaluate(FIX_CFG, messages, "seed-fallback")
    assert "route_fallback" in expected_snapshot["active_routes"]
    assert snapshot["active_routes"] == expected_snapshot["active_routes"]


def test_partial_reload_invalidates_config_cache() -> None:
    """Partial reload after config edit must rebuild pruned graph, not reuse stale cache."""
    cfg = OUT / "reload-cfg"
    shutil.rmtree(cfg, ignore_errors=True)
    shutil.copytree(FIX_CFG, cfg)
    messages = FIX_MSG / "alt.log"
    export1 = OUT / "reload-1.json"
    _run_replay(cfg, messages, "seed-r1", export1, reload="full")
    (cfg / "filters.conf").write_text(
        (cfg / "filters.conf").read_text(encoding="utf-8")
        + "\nfac_extra|facility(uucp)\n",
        encoding="utf-8",
    )
    (cfg / "graph.conf").write_text(
        (cfg / "graph.conf").read_text(encoding="utf-8")
        + "\nroute_extra|fac_extra|dest_extra|0|0\n",
        encoding="utf-8",
    )
    export2 = OUT / "reload-2.json"
    report2, snapshot2 = _run_replay(cfg, messages, "seed-r2", export2, reload="partial", reset=False)
    expected2, expected_snapshot2 = evaluate(cfg, messages, "seed-r2", reload_mode="partial")
    assert "route_extra" in expected_snapshot2["active_routes"]
    assert snapshot2["active_routes"] == expected_snapshot2["active_routes"]
    assert report2 == expected2


def test_hidden_fixture_prevents_hardcoded_outputs() -> None:
    """Hidden config and messages must match independent evaluation."""
    hidden_cfg = Path("/tests/hidden_configs/hidden")
    hidden_msg = Path("/tests/hidden_messages/hidden.log")
    export = OUT / "hidden-report.json"
    report, snapshot = _run_replay(hidden_cfg, hidden_msg, "seed-hidden", export)
    expected_report, expected_snapshot = evaluate(hidden_cfg, hidden_msg, "seed-hidden")
    assert report == expected_report
    assert snapshot == expected_snapshot


def test_and_binds_tighter_than_or_without_parens() -> None:
    """Grouped OR must bind before AND; auth+info must not match warn-only group filter."""
    msg = OUT / "prec.log"
    msg.write_text("p1,auth,info,sshd,hostP,note\n", encoding="utf-8")
    export = OUT / "prec-report.json"
    report, _ = _run_replay(FIX_CFG, msg, "seed-prec", export)
    expected, _ = evaluate(FIX_CFG, msg, "seed-prec")
    assert report == expected
    group_hits = sum(d["count"] for d in report["deliveries"] if d["destination"] == "dest_group")
    assert group_hits == 0


def test_replay_is_deterministic_for_same_seed() -> None:
    """Repeated replay with identical inputs yields byte-identical export JSON."""
    messages = FIX_MSG / "alt.log"
    export1 = OUT / "det-1.json"
    export2 = OUT / "det-2.json"
    report1, _ = _run_replay(FIX_CFG, messages, "seed-det", export1)
    expected, _ = evaluate(FIX_CFG, messages, "seed-det")
    assert report1 == expected
    payload1 = export1.read_text(encoding="utf-8")
    _run_replay(FIX_CFG, messages, "seed-det", export2)
    payload2 = export2.read_text(encoding="utf-8")
    assert payload1 == payload2
