"""Behavioral verifier for bgpcut peer cutover auditor."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from bgpcut_support import FIXTURES, read_json, reset, witness
from cutover_contract_math import (
    apply_salt,
    expected_cutover,
    expected_report,
    load_fixture,
    reference_cutover,
)

CLI = Path("/usr/local/bin/bgpcut")
# Path strings must appear literally for static coverage checks.
DEFAULT_OUT = Path("/app/output/bgp_cutover_report.json")
LEDGER = Path("/app/state/cutover-ledger.json")
CONFIG = Path("/app/config/bgpcut.json")


def _run(scenario: str, run_id: str, out: Path, *, env=None):
    reset()
    proc = witness(scenario, out, run_id, env=env)
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return read_json(out)


def _expect(scenario: str, run_id: str):
    inv = load_fixture(FIXTURES / scenario / "inventory.json")
    return expected_report(reference_cutover(apply_salt(inv, ""), run_id))


def test_basic_wave_matches_expected(tmp_path: Path):
    """basic-wave operational sealed report matches expected atlas (origin accept, rewrite, MED clamp)."""
    assert _run("basic-wave", "run-basic", tmp_path / "b.json") == _expect("basic-wave", "run-basic")


def test_inherit_override_matches_expected(tmp_path: Path):
    """inherit-override: peer-local filter_id replaces group deny."""
    assert _run("inherit-override", "run-io", tmp_path / "i.json") == _expect("inherit-override", "run-io")


def test_transit_match_matches_expected(tmp_path: Path):
    """transit-match: transit mode matches ASN excluding origin."""
    assert _run("transit-match", "run-tr", tmp_path / "t.json") == _expect("transit-match", "run-tr")


def test_wave_tie_matches_expected(tmp_path: Path):
    """wave-tie full report matches expected atlas including peer_order."""
    assert _run("wave-tie", "run-wt", tmp_path / "w.json") == _expect("wave-tie", "run-wt")


def test_critical_abort_matches_expected(tmp_path: Path):
    """critical-abort sealed report matches expected atlas wave_aborted semantics."""
    assert _run("critical-abort", "run-ca", tmp_path / "c.json") == _expect("critical-abort", "run-ca")


def test_rewrite_wellknown_matches_expected(tmp_path: Path):
    """rewrite-wellknown sealed report matches expected atlas community exclusions."""
    assert _run("rewrite-wellknown", "run-wk", tmp_path / "r.json") == _expect(
        "rewrite-wellknown", "run-wk"
    )


def test_exact_path_matches_expected(tmp_path: Path):
    """exact-path sealed report matches expected atlas exact as_path equality."""
    assert _run("exact-path", "run-ex", tmp_path / "e.json") == _expect("exact-path", "run-ex")


def test_wave_tie_order(tmp_path: Path):
    """peer_order uses wave_rank then asn then peer_id."""
    got = _run("wave-tie", "tie", tmp_path / "tie.json")
    assert got["peer_order"] == ["a-peer", "m-peer", "z-peer"]


def test_critical_abort_restores_rib(tmp_path: Path):
    """Critical deny abort restores rib_after from the pre-evaluation checkpoint."""
    got = _run("critical-abort", "abort", tmp_path / "a.json")
    assert got["wave_aborted"] is True
    assert LEDGER.is_file()
    ledger = read_json(LEDGER)
    early = next(r for r in ledger["rib_after"] if r["peer_id"] == "early")
    assert early["communities"] == ["65001:1"]
    assert early["med"] == 9


def test_wellknown_communities_survive(tmp_path: Path):
    """ASN 0 and 65535 communities are never rewritten."""
    got = _run("rewrite-wellknown", "wk", tmp_path / "wk.json")
    assert got["rows"][0]["communities"] == ["0:99", "65535:1", "65040:4"]


def test_med_min_clamp(tmp_path: Path):
    """Accepted routes clamp med with the lesser of med and med_ceiling."""
    got = _run("basic-wave", "med", tmp_path / "m.json")
    assert got["rows"][0]["med"] == 40
    assert got["rows"][0]["communities"] == ["65010:9", "0:1"]


def test_witness_ledger_and_default_output_paths():
    """Operational staging snapshot at cutover-ledger.json then write sealed rollout report."""
    reset()
    proc = subprocess.run(
        [str(CLI), "cutover", "--scenario", "basic-wave"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert LEDGER.is_file(), "/app/state/cutover-ledger.json missing staging snapshot"
    assert DEFAULT_OUT.is_file(), "/app/output/bgp_cutover_report.json missing"
    ledger = read_json(LEDGER)
    report = read_json(DEFAULT_OUT)
    assert ledger["run_id"] == report["run_id"]
    assert report["audit_digest"]
    assert report["peer_order"] == ledger["peer_order"]


def test_missing_scenario_exit_2(tmp_path: Path):
    """Missing scenario inventory exits 2."""
    reset()
    proc = witness("missing", tmp_path / "x.json")
    assert proc.returncode == 2


def test_invalid_inventory_exit_3(tmp_path: Path):
    """Invalid inventory JSON exits 3."""
    bad_dir = FIXTURES / "invalid-json-trap"
    bad_dir.mkdir(parents=True, exist_ok=True)
    inv_path = bad_dir / "inventory.json"
    inv_path.write_text("{not-json", encoding="utf-8")
    try:
        reset()
        proc = witness("invalid-json-trap", tmp_path / "x.json")
        assert proc.returncode == 3
    finally:
        inv_path.unlink(missing_ok=True)
        bad_dir.rmdir()


def test_config_peer_id_salt_fallback(tmp_path: Path):
    """peer_id_salt from bgpcut.json when TB3_PEER_SALT is absent."""
    original = CONFIG.read_text(encoding="utf-8")
    cfg = read_json(CONFIG)
    cfg["peer_id_salt"] = "-cfg"
    try:
        CONFIG.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
        reset()
        proc = witness(
            "basic-wave",
            tmp_path / "cfg.json",
            "cfg-salt",
            env={"TB3_PEER_SALT": ""},
        )
        assert proc.returncode == 0, proc.stderr + proc.stdout
        inv = load_fixture(FIXTURES / "basic-wave" / "inventory.json")
        expected = expected_report(reference_cutover(apply_salt(inv, "-cfg"), "cfg-salt"))
        assert read_json(tmp_path / "cfg.json") == expected
    finally:
        CONFIG.write_text(original, encoding="utf-8")


def test_hidden_salt(tmp_path: Path):
    """Hidden salt wave: TB3_PEER_SALT appends peer ids."""
    src = Path("/opt/verifier-fixtures/bgpcut/hidden-salt-wave/inventory.json")
    if not src.exists():
        pytest.skip("hidden unavailable")
    dest = FIXTURES / "hidden-salt-wave"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "inventory.json").write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    inv = load_fixture(src)
    expected = expected_report(expected_cutover(apply_salt(inv, "-x"), "hs"))
    got = _run("hidden-salt-wave", "hs", tmp_path / "hs.json", env={"TB3_PEER_SALT": "-x"})
    assert got == expected


def test_hidden_inherit(tmp_path: Path):
    """Hidden inherit: peer replaces group deny on critical prefix."""
    src = Path("/opt/verifier-fixtures/bgpcut/hidden-inherit-priority/inventory.json")
    if not src.exists():
        pytest.skip("hidden unavailable")
    dest = FIXTURES / "hidden-inherit-priority"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "inventory.json").write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    inv = load_fixture(src)
    expected = expected_report(expected_cutover(apply_salt(inv, ""), "hi"))
    got = _run("hidden-inherit-priority", "hi", tmp_path / "hi.json")
    assert got["rows"][0]["action"] == "accept"
    assert got == expected


def test_cli_unknown_subcommand_exit_1():
    """Unknown subcommand exits 1."""
    proc = subprocess.run(
        [str(CLI), "not-a-verb"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 1
