"""Behavioral tests for qasmenv shot-noise calibration envelope."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from reference_eb9951dd_qasm import (
    build_provenance_chain,
    count_gates,
    normalize_histogram,
    normalize_row,
    provenance_digest,
    reference_compute,
    reference_digest_from_export,
    reference_export,
    select_matrix,
)

QASMENV = "/app/bin/qasmenv"
STAGING = Path("/app/state/cal-staging.json")
LEDGER = Path("/app/state/envelope-ledger.json")
ENVELOPE = Path("/app/output/shot-noise-envelope.json")
DIGEST = Path("/app/output/envelope-digest.txt")
CAL_DIR = Path("/app/data")
MANIFEST = CAL_DIR / "seed_manifest.json"
QASM = CAL_DIR / "experiment.qasm"
HIDDEN_FIXTURE_DIR = Path("/opt/verifier-fixtures/qasmenv")


def _run(cmd: list[str], *, env: dict | None = None, check: bool = True) -> subprocess.CompletedProcess:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(cmd, check=check, capture_output=True, text=True, env=merged)


def _fresh() -> None:
    for p in (STAGING, LEDGER, ENVELOPE, DIGEST):
        if p.exists():
            p.unlink()


def _ingest(cal_dir: Path, manifest: Path, qasm: Path) -> None:
    _run(
        [
            QASMENV,
            "stage",
            "ingest",
            "--cal-dir",
            str(cal_dir),
            "--qasm",
            str(qasm),
            "--manifest",
            str(manifest),
        ]
    )


def _compute(*, env: dict | None = None) -> None:
    _run([QASMENV, "envelope", "compute"], env=env)


def _export() -> None:
    _run([QASMENV, "report", "export"])


def _pipeline(cal_dir: Path, manifest: Path, qasm: Path, *, env: dict | None = None) -> None:
    _fresh()
    _ingest(cal_dir, manifest, qasm)
    _compute(env=env)
    _export()


def _load_staging() -> dict:
    return json.loads(STAGING.read_text(encoding="utf-8"))


def _load_ledger() -> dict:
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def _tb3_cal_dir() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="tb3-cal-"))
    shutil.copy(HIDDEN_FIXTURE_DIR / "tb3_histogram.json", tmp / "histogram.json")
    shutil.copy(HIDDEN_FIXTURE_DIR / "tb3_mitigation_matrices.json", tmp / "mitigation_matrices.json")
    shutil.copy(HIDDEN_FIXTURE_DIR / "tb3_readout_drift.json", tmp / "readout_drift.json")
    return tmp


@pytest.fixture(autouse=True)
def clean_state():
    _fresh()
    yield
    _fresh()


def test_teb9951_qasmenv_binary_exists():
    """Instruction requires /app/bin/qasmenv built from workspace."""
    assert Path(QASMENV).is_file()


def test_teb9951_bundled_data_directory():
    """Instruction cites bundled fixtures under /app/data/."""
    assert CAL_DIR.is_dir()
    assert (CAL_DIR / "histogram.json").is_file()
    assert (CAL_DIR / "mitigation_matrices.json").is_file()
    assert (CAL_DIR / "experiment.qasm").is_file()


def test_teb9951_stage_ingest_writes_staging():
    """Stage ingest must write cal-staging.json."""
    _ingest(CAL_DIR, MANIFEST, QASM)
    assert STAGING.is_file()
    staging = _load_staging()
    assert staging["manifest"]["experiment_id"] == "bell-readout-v2"


def test_teb9951_ingest_increments_seq():
    """Repeated ingest bumps ingest_seq."""
    _ingest(CAL_DIR, MANIFEST, QASM)
    first = _load_staging()["ingest_seq"]
    _ingest(CAL_DIR, MANIFEST, QASM)
    second = _load_staging()["ingest_seq"]
    assert second == first + 1


def test_teb9951_ingest_records_gate_count():
    """Staging records parsed qasm gate count."""
    _ingest(CAL_DIR, MANIFEST, QASM)
    staging = _load_staging()
    qasm_text = QASM.read_text(encoding="utf-8")
    assert staging["qasm_gate_count"] == count_gates(qasm_text)


def test_teb9951_staging_path_contract():
    """Instruction staging path /app/state/cal-staging.json is honored."""
    _ingest(CAL_DIR, MANIFEST, QASM)
    assert STAGING == Path("/app/state/cal-staging.json")


def test_teb9951_histogram_row_normalization_reference():
    """shot-histogram-normalization.md requires per-row normalization."""
    _ingest(CAL_DIR, MANIFEST, QASM)
    _compute()
    ledger = _load_ledger()
    staging = _load_staging()
    ref = normalize_histogram(staging["histogram"]["rows"])
    for qubit, probs in ref.items():
        assert ledger["normalized_probs"][qubit] == pytest.approx(probs, abs=1e-9)
        assert sum(probs) == pytest.approx(1.0, abs=1e-9)


def test_teb9951_matrix_selection_seed_tiebreak():
    """mitigation-matrix-selection.md tie-break selects M_alpha for bundled data."""
    _ingest(CAL_DIR, MANIFEST, QASM)
    _compute()
    ledger = _load_ledger()
    staging = _load_staging()
    selected = select_matrix(
        staging["mitigation"]["candidates"],
        len(staging["histogram"]["qubits"]),
        staging["manifest"]["seed_hash"],
    )
    assert ledger["selected_matrix_id"] == selected["id"]
    assert ledger["selected_matrix_id"] == "M_alpha"


def test_teb9951_provenance_chain_sorted():
    """seed-manifest-provenance.md requires alphabetically sorted chain."""
    _ingest(CAL_DIR, MANIFEST, QASM)
    _compute()
    ledger = _load_ledger()
    chain = ledger["provenance"]["chain"]
    assert chain == sorted(chain)
    ref_chain = build_provenance_chain(
        _load_staging()["manifest"]["calibration_ids"],
        _load_staging()["manifest"]["experiment_id"],
        ledger["selected_matrix_id"],
    )
    assert chain == ref_chain


def test_teb9951_provenance_digest_matches_chain():
    """Provenance digest binds sorted chain per seed-manifest-provenance.md."""
    _ingest(CAL_DIR, MANIFEST, QASM)
    _compute()
    ledger = _load_ledger()
    assert ledger["provenance"]["digest"] == provenance_digest(ledger["provenance"]["chain"])


def test_teb9951_drift_multiplicative_not_additive():
    """qubit-readout-drift.md applies multiplicative drift correction."""
    _ingest(CAL_DIR, MANIFEST, QASM)
    _compute()
    ledger = _load_ledger()
    ref = reference_compute(_load_staging())
    for qubit in ref["drift_corrected"]:
        assert ledger["drift_corrected"][qubit] == pytest.approx(
            ref["drift_corrected"][qubit], abs=1e-9
        )


def test_teb9951_envelope_compute_writes_ledger():
    """envelope compute writes /app/state/envelope-ledger.json"""
    _ingest(CAL_DIR, MANIFEST, QASM)
    _compute()
    assert LEDGER.is_file()


def test_teb9951_mitigated_envelopes_match_reference():
    """Mitigated probabilities agree with independent reference compute."""
    _pipeline(CAL_DIR, MANIFEST, QASM)
    ledger = _load_ledger()
    ref = reference_compute(_load_staging())
    for qubit, env in ref["envelopes"].items():
        assert ledger["envelopes"][qubit]["mitigated"] == pytest.approx(
            env["mitigated"], abs=1e-9
        )


def test_teb9951_wilson_intervals_use_mitigated_probs():
    """uncertainty-interval-export.md Wilson intervals use mitigated probabilities."""
    _pipeline(CAL_DIR, MANIFEST, QASM)
    ledger = _load_ledger()
    ref = reference_compute(_load_staging())
    for qubit, env in ref["envelopes"].items():
        got = ledger["envelopes"][qubit]["intervals"]
        assert got == env["intervals"]


def test_teb9951_report_export_paths():
    """Instruction output paths are honored."""
    _pipeline(CAL_DIR, MANIFEST, QASM)
    assert ENVELOPE.is_file()
    assert DIGEST.is_file()
    assert str(ENVELOPE) == "/app/output/shot-noise-envelope.json"
    assert str(DIGEST) == "/app/output/envelope-digest.txt"


def test_teb9951_export_includes_provenance_block():
    """Exported JSON includes full provenance block."""
    _pipeline(CAL_DIR, MANIFEST, QASM)
    exported = json.loads(ENVELOPE.read_text(encoding="utf-8"))
    ledger = _load_ledger()
    assert exported["provenance"] == ledger["provenance"]


def test_teb9951_digest_matches_reference():
    """envelope-digest.txt matches canonical export payload hash."""
    _pipeline(CAL_DIR, MANIFEST, QASM)
    exported = json.loads(ENVELOPE.read_text(encoding="utf-8"))
    digest = DIGEST.read_text(encoding="utf-8").strip()
    assert digest == reference_digest_from_export(exported)
    assert len(digest) == 64


def test_teb9951_subprocess_cli_roundtrip():
    """Independent reference agrees after subprocess ingest compute export."""
    _pipeline(CAL_DIR, MANIFEST, QASM)
    exported = json.loads(ENVELOPE.read_text(encoding="utf-8"))
    ledger = _load_ledger()
    assert exported == reference_export(ledger)


def test_teb9951_normalize_row_independent():
    """Per-qubit row sums to unity under reference normalization."""
    row = {"qubit": "q0", "counts": [400, 600]}
    probs = normalize_row(row["counts"])
    assert probs == pytest.approx([0.4, 0.6], abs=1e-9)


def test_teb9951_tb3_hidden_qubit_labels():
    """Hidden tb3 fixtures use non-q0/q1 qubit labels and 3x3 matrices."""
    cal = _tb3_cal_dir()
    try:
        _pipeline(
            cal,
            HIDDEN_FIXTURE_DIR / "tb3_seed_manifest.json",
            HIDDEN_FIXTURE_DIR / "tb3_experiment.qasm",
        )
        ledger = _load_ledger()
        ref = reference_compute(_load_staging())
        assert set(ledger["envelopes"].keys()) == {"phi_a", "phi_b", "phi_c"}
        for qubit in ref["envelopes"]:
            assert ledger["envelopes"][qubit]["mitigated"] == pytest.approx(
                ref["envelopes"][qubit]["mitigated"], abs=1e-9
            )
    finally:
        shutil.rmtree(cal, ignore_errors=True)


def test_teb9951_tb3_seed_offset_env():
    """TB3_SEED_OFFSET adjusts matrix tie-break prefix for hidden fixtures."""
    cal = _tb3_cal_dir()
    try:
        _fresh()
        _ingest(
            cal,
            HIDDEN_FIXTURE_DIR / "tb3_seed_manifest.json",
            HIDDEN_FIXTURE_DIR / "tb3_experiment.qasm",
        )
        _compute(env={"TB3_SEED_OFFSET": "3"})
        _export()
        staging = _load_staging()
        ref = reference_compute(staging, seed_offset=3)
        ledger = _load_ledger()
        assert ledger["selected_matrix_id"] == ref["selected_matrix_id"]
        assert ledger["envelopes"]["phi_a"]["mitigated"] == pytest.approx(
            ref["envelopes"]["phi_a"]["mitigated"], abs=1e-9
        )
    finally:
        shutil.rmtree(cal, ignore_errors=True)


def test_teb9951_tb3_hidden_digest():
    """Hidden fixture export digest matches canonical export payload hash."""
    cal = _tb3_cal_dir()
    try:
        _pipeline(
            cal,
            HIDDEN_FIXTURE_DIR / "tb3_seed_manifest.json",
            HIDDEN_FIXTURE_DIR / "tb3_experiment.qasm",
        )
        exported = json.loads(ENVELOPE.read_text(encoding="utf-8"))
        digest = DIGEST.read_text(encoding="utf-8").strip()
        assert digest == reference_digest_from_export(exported)
    finally:
        shutil.rmtree(cal, ignore_errors=True)


def test_teb9951_instruction_data_paths_exercised():
    """Instruction paths /app/data/ and state files are exercised."""
    assert list(CAL_DIR.glob("*.json"))
    _pipeline(CAL_DIR, MANIFEST, QASM)
    assert json.loads(ENVELOPE.read_text(encoding="utf-8"))["experiment_id"] == "bell-readout-v2"


def test_teb9951_ledger_retains_total_shots():
    """Each envelope records total shot count from histogram row."""
    _pipeline(CAL_DIR, MANIFEST, QASM)
    ledger = _load_ledger()
    staging = _load_staging()
    for row in staging["histogram"]["rows"]:
        qubit = row["qubit"]
        assert ledger["envelopes"][qubit]["total_shots"] == sum(row["counts"])
