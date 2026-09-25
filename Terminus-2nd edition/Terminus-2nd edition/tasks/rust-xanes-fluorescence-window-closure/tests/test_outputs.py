"""Behavioral verifier for xanesctl close."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from reference_xanes import XanesRefError, reference_close

APP = Path("/app")
CLI = "/usr/local/bin/xanesctl"
FIXTURES = APP / "fixtures"
OUTPUT = APP / "output"
CATALOG = json.loads((FIXTURES / "catalog.json").read_text(encoding="utf-8"))
SEEDS = json.loads((FIXTURES / "seeds.json").read_text(encoding="utf-8"))["seeds"]
RESET = APP / "scripts" / "reset-state.sh"
CORE = APP / "crates/xanes-core/src"
BROKEN = Path("/opt/verifier-broken-xanes")
ORACLE_DIR = Path("/tests/golden_modules")
MODULES = ("victoreen_fit", "edge_ordinal", "mu_window_seal")
ORACLE = {
    "victoreen_fit": "oracle_victoreen_fit.rs",
    "edge_ordinal": "oracle_edge_ordinal.rs",
    "mu_window_seal": "oracle_mu_window_seal.rs",
}


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False)


def rebuild() -> None:
    for mod in MODULES:
        (CORE / f"{mod}.rs").touch()
    proc = run(
        [
            "bash",
            "-lc",
            "cargo build --locked --release --bin xanesctl && install -m 0755 target/release/xanesctl /usr/local/bin/xanesctl",
        ]
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout


def restore_broken() -> None:
    for mod in MODULES:
        shutil.copy2(BROKEN / f"{mod}.rs", CORE / f"{mod}.rs")


def restore_golden() -> None:
    for mod in MODULES:
        shutil.copy2(ORACLE_DIR / ORACLE[mod], CORE / f"{mod}.rs")


def install_modules(only_broken: set[str]) -> None:
    for mod in MODULES:
        dest = CORE / f"{mod}.rs"
        if mod in only_broken:
            shutil.copy2(BROKEN / f"{mod}.rs", dest)
        else:
            shutil.copy2(ORACLE_DIR / ORACLE[mod], dest)


def reset() -> None:
    proc = run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def paths(name: str) -> tuple[Path, Path]:
    entry = next(s for s in CATALOG["scenarios"] if s["name"] == name)
    return FIXTURES / entry["trace"], FIXTURES / entry["windows"]


def close_cli(name: str, seed: str = "") -> subprocess.CompletedProcess[str]:
    trace, windows = paths(name)
    export_path = OUTPUT / f"{name}-{seed or 'base'}.json"
    cmd = [CLI, "close", "--trace", str(trace), "--windows", str(windows), "--export", str(export_path)]
    if seed:
        cmd.extend(["--seed", seed])
    return run(cmd)


def load_export(name: str, seed: str = "") -> dict:
    return json.loads((OUTPUT / f"{name}-{seed or 'base'}.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def _reset_output() -> None:
    reset()


@pytest.mark.parametrize("seed", [""] + SEEDS)
@pytest.mark.parametrize("scenario_name", [s["name"] for s in CATALOG["scenarios"]])
def test_beamline_mu_digest_oracle_parity(scenario_name: str, seed: str) -> None:
    """Each catalog trace/windows pair must match the independent μ(E) oracle digest."""
    entry = next(s for s in CATALOG["scenarios"] if s["name"] == scenario_name)
    trace, windows = paths(scenario_name)
    proc = close_cli(scenario_name, seed)
    if entry["expect_error"]:
        assert proc.returncode == 1
        with pytest.raises(XanesRefError):
            reference_close(trace, windows, seed)
        return
    assert proc.returncode == 0, proc.stderr or proc.stdout
    exp = load_export(scenario_name, seed)
    ref = reference_close(trace, windows, seed)
    assert exp["status"] == "ok"
    assert exp["closure_digest"] == ref["closure_digest"]
    assert exp["all_channels_sorted"] == ref["all_channels_sorted"]


def test_question_mark_edge_refuses_export() -> None:
    """Windows declaring ?edge_code must exit non-zero per scope-stack.md."""
    proc = close_cli("undeclared-edge")
    assert proc.returncode == 1
    exp = load_export("undeclared-edge")
    assert exp["status"] == "error"


def test_oracle_sha256_without_subprocess() -> None:
    """Python oracle must emit a stable 64-hex digest without invoking xanesctl."""
    trace, windows = paths("k-edge-simple")
    ref = reference_close(trace, windows, "")
    assert len(ref["closure_digest"]) == 64
    assert ref["closure_digest"] != "0" * 64


def test_victoreen_calibration_baseline_trap() -> None:
    """Broken victoreen_fit staging snapshot must diverge from reference digests."""
    try:
        install_modules({"victoreen_fit"})
        rebuild()
        proc = close_cli("k-edge-simple")
        assert proc.returncode == 0
        exp = load_export("k-edge-simple")
        trace, windows = paths("k-edge-simple")
        ref = reference_close(trace, windows, "")
        assert exp["closure_digest"] != ref["closure_digest"]
    finally:
        restore_broken()
        rebuild()


def test_ordinal_lex_only_trap() -> None:
    """Broken edge_ordinal staging snapshot must diverge from reference channel order."""
    try:
        install_modules({"edge_ordinal"})
        rebuild()
        proc = close_cli("channel-rank-mix")
        assert proc.returncode == 0
        exp = load_export("channel-rank-mix")
        trace, windows = paths("channel-rank-mix")
        ref = reference_close(trace, windows, "")
        assert exp["all_channels_sorted"] != ref["all_channels_sorted"]
    finally:
        restore_broken()
        rebuild()


def test_monochromator_seed_bin_trap() -> None:
    """Broken mu_window_seal staging snapshot must diverge on seeded deep-nest digests."""
    try:
        install_modules({"mu_window_seal"})
        rebuild()
        seed = SEEDS[2]
        proc = close_cli("deep-nest-seed", seed)
        assert proc.returncode == 0
        exp = load_export("deep-nest-seed", seed)
        trace, windows = paths("deep-nest-seed")
        ref = reference_close(trace, windows, seed)
        assert exp["closure_digest"] != ref["closure_digest"]
    finally:
        restore_broken()
        rebuild()


def test_undeclared_edge_ok_trap() -> None:
    """Broken mu_window_seal staging snapshot must not refuse ?edge exports."""
    try:
        install_modules({"mu_window_seal"})
        rebuild()
        proc = close_cli("undeclared-edge")
        assert proc.returncode == 0 or load_export("undeclared-edge").get("status") == "ok"
    finally:
        restore_broken()
        rebuild()


def test_closure_digest_k_edge_contract() -> None:
    """k-edge-simple closure digest and all_channels_sorted per closure-schema.md."""
    proc = close_cli("k-edge-simple")
    assert proc.returncode == 0
    body = load_export("k-edge-simple")
    assert "closure_digest" in body and "all_channels_sorted" in body


def test_oracle_nested_children_parity() -> None:
    """nested-children scenario digest must match reference_close oracle."""
    restore_golden()
    rebuild()
    trace, windows = paths("nested-children")
    proc = close_cli("nested-children")
    assert proc.returncode == 0
    body = load_export("nested-children")
    ref = reference_close(trace, windows, "")
    assert body["closure_digest"] == ref["closure_digest"]


def test_oracle_overlapping_siblings_parity() -> None:
    """overlapping-siblings integrals must match independent oracle export math."""
    restore_golden()
    rebuild()
    trace, windows = paths("overlapping-siblings")
    proc = close_cli("overlapping-siblings")
    assert proc.returncode == 0
    body = load_export("overlapping-siblings")
    ref = reference_close(trace, windows, "")
    assert body["closure_digest"] == ref["closure_digest"]


def test_oracle_m_edge_mix_parity() -> None:
    """m-edge-mix uranium windows must match oracle digest after ingest+bind."""
    restore_golden()
    rebuild()
    trace, windows = paths("m-edge-mix")
    proc = close_cli("m-edge-mix")
    assert proc.returncode == 0
    body = load_export("m-edge-mix")
    ref = reference_close(trace, windows, "")
    assert body["closure_digest"] == ref["closure_digest"]


def test_oracle_sparse_preedge_parity() -> None:
    """sparse-preedge Victoreen fit must still close per victoreen-baseline.md."""
    restore_golden()
    rebuild()
    trace, windows = paths("sparse-preedge")
    proc = close_cli("sparse-preedge")
    assert proc.returncode == 0
    body = load_export("sparse-preedge")
    ref = reference_close(trace, windows, "")
    assert body["closure_digest"] == ref["closure_digest"]


def test_cross_run_reset_idempotent_close() -> None:
    """reset-state.sh must make repeated close exports deterministic (cross-run idempotence)."""
    proc1 = close_cli("k-edge-simple")
    assert proc1.returncode == 0
    d1 = load_export("k-edge-simple")["closure_digest"]
    reset()
    proc2 = close_cli("k-edge-simple")
    assert proc2.returncode == 0
    d2 = load_export("k-edge-simple")["closure_digest"]
    assert d1 == d2
