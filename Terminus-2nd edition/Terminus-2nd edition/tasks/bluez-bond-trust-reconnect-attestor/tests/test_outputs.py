"""Behavioral verifier for the bondattest BlueZ bond-trust reconnect attestor."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from bondattest_oracle import absorb as oracle_absorb
from bondattest_oracle import run_pipeline as oracle_run_pipeline
from bondattest_oracle import seal as oracle_seal

APP = Path("/app")
CLI = Path("/usr/local/bin/bondattest")
MIDSTATE = APP / "state" / "bondattest-midstate.json"
BUNDLE = APP / "output" / "bond-reconnect-attestation.json"
CFG = APP / "config" / "bondattest.json"
TRACES = APP / "fixtures" / "traces"
LIB = APP / "lib"
COMPLETE_LIB = Path("/tests/verifier_complete")
INCOMPLETE_LIB = Path("/tests/verifier_incomplete")
HIDDEN_OPT = Path("/opt/verifier-fixtures/bondattest_hidden")
HIDDEN_TESTS = Path("/tests/hidden_traces")


def _run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=False, capture_output=True, text=True, cwd=str(APP), **kw)


def reset_state() -> None:
    proc = _run(["bash", str(APP / "scripts" / "reset-state.sh")])
    assert proc.returncode == 0, proc.stderr


def rebuild() -> None:
    proc = _run(["bash", str(APP / "scripts" / "rebuild-bondattest.sh")])
    assert proc.returncode == 0, proc.stderr


def _restore_lib(modules: dict[str, Path]) -> dict[Path, Path]:
    backups: dict[Path, Path] = {}
    for name, src in modules.items():
        target = LIB / name
        backup = target.with_name(target.name + ".bak-test")
        shutil.copy2(target, backup)
        backups[target] = backup
        shutil.copy2(src, target)
    return backups


def _rollback_lib(backups: dict[Path, Path]) -> None:
    for target, backup in backups.items():
        shutil.move(str(backup), str(target))


def run_absorb(
    trace: str,
    seed: str,
    *,
    config: Path = CFG,
    midstate: Path | None = None,
) -> subprocess.CompletedProcess:
    cmd = [str(CLI), "absorb", "--trace", trace, "--config", str(config), "--seed", seed]
    if midstate is not None:
        cmd += ["--midstate", str(midstate)]
    return _run(cmd)


def run_seal(*, midstate: Path | None = None, bundle: Path | None = None) -> subprocess.CompletedProcess:
    cmd = [str(CLI), "seal"]
    if midstate is not None:
        cmd += ["--midstate", str(midstate)]
    if bundle is not None:
        cmd += ["--bundle", str(bundle)]
    return _run(cmd)


def run_pipeline(trace: str, seed: str) -> tuple[dict, dict]:
    proc_a = run_absorb(trace, seed)
    assert proc_a.returncode == 0, proc_a.stderr
    proc_s = run_seal()
    assert proc_s.returncode == 0, proc_s.stderr
    return json.loads(MIDSTATE.read_text(encoding="utf-8")), json.loads(BUNDLE.read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def _clean_env():
    reset_state()
    rebuild()
    os.environ.pop("TB3_TRACE_DIR", None)
    yield
    os.environ.pop("TB3_TRACE_DIR", None)


def test_te2a6e9_cli_exists():
    """Instruction requires /app/scripts/bondattest installed as /usr/local/bin/bondattest."""
    assert CLI.is_file()


def test_te2a6e9_absorb_writes_midstate():
    """Absorb must materialize a midstate snapshot with the documented schema fields."""
    proc = run_absorb(str(TRACES / "mixed-fleet-core.trace.jsonl"), "seed-absorb")
    assert proc.returncode == 0, proc.stderr
    assert MIDSTATE.is_file()
    doc = json.loads(MIDSTATE.read_text(encoding="utf-8"))
    assert doc["schema_version"] == 1
    assert "midstate_digest" in doc
    assert "ledger_rows" in doc


def test_te2a6e9_absorb_default_midstate_path_matches_instruction():
    """Absorb without --midstate must write the instruction default midstate path."""
    default_path = Path("/app/state/bondattest-midstate.json")
    assert default_path == MIDSTATE
    proc = run_absorb(str(TRACES / "mixed-fleet-core.trace.jsonl"), "seed-default-midstate")
    assert proc.returncode == 0, proc.stderr
    assert default_path.is_file()
    assert str(default_path) == "/app/state/bondattest-midstate.json"


def test_te2a6e9_seal_writes_bundle_default_path():
    """Seal without --bundle must write the instruction default bundle path."""
    default_path = Path("/app/output/bond-reconnect-attestation.json")
    assert default_path == BUNDLE
    run_absorb(str(TRACES / "mixed-fleet-core.trace.jsonl"), "seed-default-bundle")
    proc = run_seal()
    assert proc.returncode == 0, proc.stderr
    assert default_path.is_file()
    assert str(default_path) == "/app/output/bond-reconnect-attestation.json"


def test_te2a6e9_seal_bundle_seal_matches_oracle():
    """Full absorb+seal bundle_seal must equal the independent oracle for the mixed fixture."""
    trace = TRACES / "mixed-fleet-core.trace.jsonl"
    _, bundle = run_pipeline(str(trace), "seed-full-pipeline")
    ref_midstate, ref_bundle = oracle_run_pipeline(trace, CFG, "seed-full-pipeline")
    assert bundle["bundle_seal"] == ref_bundle["bundle_seal"]
    assert bundle == ref_bundle


def test_te2a6e9_pairing_required_on_addr_mismatch():
    """First mismatched connect must be rejected until pairing_confirm is recorded."""
    trace = TRACES / "pairing-mismatch.trace.jsonl"
    midstate, _ = run_pipeline(str(trace), "seed-pairing")
    ref = oracle_absorb(trace, CFG, "seed-pairing")
    events = [row["event"] for row in midstate["ledger_rows"]]
    assert events == ["seed_bond", "connect_rejected", "pairing_confirm", "connect"]
    assert midstate["pairing_confirms"] == 1
    assert midstate == ref


def test_te2a6e9_resume_cleared_on_bond_remove():
    """bond_remove on a device with a resume token must increment resume_tokens_cleared."""
    trace = TRACES / "bond-remove-resume.trace.jsonl"
    midstate, _ = run_pipeline(str(trace), "seed-resume")
    ref = oracle_absorb(trace, CFG, "seed-resume")
    assert midstate["resume_tokens_cleared"] == 1
    assert midstate == ref


def test_te2a6e9_disconnect_captures_power_before_off():
    """Disconnect ledger row must record adapter_power as of its own seq, not a later state change."""
    trace = TRACES / "power-disconnect-order.trace.jsonl"
    midstate, _ = run_pipeline(str(trace), "seed-power")
    ref = oracle_absorb(trace, CFG, "seed-power")
    assert midstate["disconnect_reasons"][0]["adapter_power"] == "on"
    assert midstate["adapter_power"] == "off"
    assert midstate == ref


def test_te2a6e9_gatt_dedupe():
    """Case-variant UUID rediscovery must not inflate gatt_resolve_count."""
    trace = TRACES / "gatt-uuid-dedupe.trace.jsonl"
    midstate, _ = run_pipeline(str(trace), "seed-gatt")
    ref = oracle_absorb(trace, CFG, "seed-gatt")
    assert midstate["gatt_resolve_count"] == 2
    assert midstate == ref


def test_te2a6e9_battery_debounce():
    """Battery probes inside the debounce window must be suppressed, not counted."""
    trace = TRACES / "battery-reconnect-storm.trace.jsonl"
    midstate, _ = run_pipeline(str(trace), "seed-battery")
    ref = oracle_absorb(trace, CFG, "seed-battery")
    assert midstate["reconnect_attempts"] == 2
    events = [row["event"] for row in midstate["ledger_rows"]]
    assert "reconnect_suppressed" in events
    assert midstate == ref


def test_te2a6e9_tb3_trace_dir():
    """TB3_TRACE_DIR must let a relative --trace resolve against a hidden verifier directory."""
    hidden = HIDDEN_OPT / "hidden-fleet-a.trace.jsonl"
    if not hidden.is_file():
        pytest.skip("hidden opt-verifier trace absent")
    os.environ["TB3_TRACE_DIR"] = str(HIDDEN_OPT)
    proc = run_absorb("hidden-fleet-a.trace.jsonl", "seed-tb3")
    assert proc.returncode == 0, proc.stderr
    midstate = json.loads(MIDSTATE.read_text(encoding="utf-8"))
    ref = oracle_absorb(hidden, CFG, "seed-tb3")
    assert midstate == ref
    assert midstate["resume_tokens_cleared"] == 1


def test_te2a6e9_decoy_absent():
    """Decoy mac_sort_v0 helper must not appear in midstate or bundle output."""
    _, bundle = run_pipeline(str(TRACES / "mixed-fleet-core.trace.jsonl"), "seed-decoy")
    raw_midstate = MIDSTATE.read_text(encoding="utf-8")
    raw_bundle = BUNDLE.read_text(encoding="utf-8")
    assert "mac_sort_v0" not in raw_midstate
    assert "mac_sort_v0" not in raw_bundle


def test_te2a6e9_idempotent_seal():
    """Re-sealing an unchanged midstate snapshot must produce byte-identical bundle output."""
    run_absorb(str(TRACES / "mixed-fleet-core.trace.jsonl"), "seed-idempotent")
    proc1 = run_seal()
    assert proc1.returncode == 0, proc1.stderr
    first = BUNDLE.read_bytes()
    proc2 = run_seal()
    assert proc2.returncode == 0, proc2.stderr
    second = BUNDLE.read_bytes()
    assert first == second


def test_te2a6e9_seed_recorded_in_midstate_and_bundle():
    """The seed passed to absorb must be carried through into both artifacts unchanged."""
    seed = "seed-carry-through"
    midstate, bundle = run_pipeline(str(TRACES / "mixed-fleet-core.trace.jsonl"), seed)
    assert midstate["seed"] == seed
    assert bundle["seed"] == seed


def test_te2a6e9_absorb_without_seal_does_not_satisfy_export_contract():
    """Absorb/ingest alone must not produce the sealed export attestation bundle."""
    if BUNDLE.is_file():
        BUNDLE.unlink()
    proc = run_absorb(str(TRACES / "mixed-fleet-core.trace.jsonl"), "seed-ingest-only")
    assert proc.returncode == 0, proc.stderr
    assert MIDSTATE.is_file()
    assert not BUNDLE.is_file()
    # Export path requires an explicit seal after ingest/absorb.
    seal_proc = run_seal()
    assert seal_proc.returncode == 0, seal_proc.stderr
    assert BUNDLE.is_file()


def test_te2a6e9_ledger_rows_match_reference_order():
    """ledger_rows must preserve trace absorb order, matching the oracle row-for-row."""
    trace = TRACES / "mixed-fleet-core.trace.jsonl"
    midstate, _ = run_pipeline(str(trace), "seed-ledger-order")
    ref = oracle_absorb(trace, CFG, "seed-ledger-order")
    assert midstate["ledger_rows"] == ref["ledger_rows"]


def test_te2a6e9_full_pipeline_matches_oracle_for_all_public_traces():
    """Every bundled trace must reproduce the oracle's midstate and bundle output exactly."""
    for name in [
        "pairing-mismatch",
        "bond-remove-resume",
        "power-disconnect-order",
        "gatt-uuid-dedupe",
        "battery-reconnect-storm",
        "mixed-fleet-core",
    ]:
        trace = TRACES / f"{name}.trace.jsonl"
        seed = f"seed-sweep-{name}"
        midstate, bundle = run_pipeline(str(trace), seed)
        ref_midstate, ref_bundle = oracle_run_pipeline(trace, CFG, seed)
        assert midstate == ref_midstate, name
        assert bundle == ref_bundle, name


def test_te2a6e9_subprocess_independent_alt_paths():
    """Custom --midstate/--bundle paths must work independently of the documented defaults."""
    alt_midstate = APP / "state" / "alt-midstate.json"
    alt_bundle = APP / "output" / "alt-bundle.json"
    assert str(alt_midstate) == "/app/state/alt-midstate.json"
    assert str(alt_bundle) == "/app/output/alt-bundle.json"
    proc_a = run_absorb(str(TRACES / "gatt-uuid-dedupe.trace.jsonl"), "seed-alt", midstate=alt_midstate)
    assert proc_a.returncode == 0, proc_a.stderr
    proc_s = run_seal(midstate=alt_midstate, bundle=alt_bundle)
    assert proc_s.returncode == 0, proc_s.stderr
    assert alt_midstate.is_file()
    assert alt_bundle.is_file()
    data = json.loads(alt_bundle.read_text(encoding="utf-8"))
    assert data["counts"]["gatt_resolve_count"] == 2
    assert not MIDSTATE.exists()
    assert not BUNDLE.exists()


def test_te2a6e9_incomplete_pairing_slice_still_misses_hidden_bond_remove():
    """Fixing the pairing gate alone must not satisfy the hidden bond-remove resume trap."""
    hidden = HIDDEN_TESTS / "e2a6e9a7_trap-bond-resume.trace.jsonl"
    if not hidden.is_file():
        pytest.skip("hidden trap trace absent")
    backups = _restore_lib(
        {
            "trustgate/pairing_gate.sh": INCOMPLETE_LIB / "pairing_gate.sh",
            "trustgate/resume_clear.sh": INCOMPLETE_LIB / "resume_clear.sh",
            "trustgate/gatt_identity.sh": INCOMPLETE_LIB / "gatt_identity.sh",
            "trustgate/battery_debounce.sh": INCOMPLETE_LIB / "battery_debounce.sh",
            "intake/pipeline.sh": INCOMPLETE_LIB / "pipeline.sh",
        }
    )
    backups.update(_restore_lib({"trustgate/pairing_gate.sh": COMPLETE_LIB / "pairing_gate.sh"}))
    try:
        rebuild()
        os.environ["TB3_TRACE_DIR"] = str(HIDDEN_TESTS)
        proc = run_absorb("e2a6e9a7_trap-bond-resume.trace.jsonl", "seed-partial-pairing")
        assert proc.returncode == 0, proc.stderr
        midstate = json.loads(MIDSTATE.read_text(encoding="utf-8"))
        ref = oracle_absorb(hidden, CFG, "seed-partial-pairing")
        assert ref["resume_tokens_cleared"] == 1
        assert midstate["resume_tokens_cleared"] == 0
        assert midstate != ref
    finally:
        _rollback_lib(backups)
        rebuild()


def test_te2a6e9_incomplete_without_battery_debounce_still_misses_storm():
    """A module slice that omits battery_debounce must still miss the debounce fixture."""
    backups = _restore_lib(
        {
            "trustgate/pairing_gate.sh": INCOMPLETE_LIB / "pairing_gate.sh",
            "trustgate/resume_clear.sh": INCOMPLETE_LIB / "resume_clear.sh",
            "trustgate/gatt_identity.sh": INCOMPLETE_LIB / "gatt_identity.sh",
            "trustgate/battery_debounce.sh": INCOMPLETE_LIB / "battery_debounce.sh",
            "intake/pipeline.sh": INCOMPLETE_LIB / "pipeline.sh",
        }
    )
    backups.update(
        _restore_lib(
            {
                "trustgate/pairing_gate.sh": COMPLETE_LIB / "pairing_gate.sh",
                "trustgate/resume_clear.sh": COMPLETE_LIB / "resume_clear.sh",
                "trustgate/gatt_identity.sh": COMPLETE_LIB / "gatt_identity.sh",
                "intake/pipeline.sh": COMPLETE_LIB / "pipeline.sh",
            }
        )
    )
    try:
        rebuild()
        trace = TRACES / "battery-reconnect-storm.trace.jsonl"
        midstate, _ = run_pipeline(str(trace), "seed-partial-battery")
        ref = oracle_absorb(trace, CFG, "seed-partial-battery")
        assert ref["reconnect_attempts"] == 2
        assert midstate["reconnect_attempts"] == 3
        assert midstate != ref
    finally:
        _rollback_lib(backups)
        rebuild()


def test_te2a6e9_seal_formula_matches_oracle_ledger_fingerprint():
    """bundle_emit ledger_fingerprint must match the documented row-order digest formula."""
    trace = TRACES / "mixed-fleet-core.trace.jsonl"
    midstate, bundle = run_pipeline(str(trace), "seed-fingerprint")
    ref_bundle = oracle_seal(json.loads(MIDSTATE.read_text(encoding="utf-8")))
    assert bundle["ledger_fingerprint"] == ref_bundle["ledger_fingerprint"]
    assert bundle["bundle_seal"] == ref_bundle["bundle_seal"]
