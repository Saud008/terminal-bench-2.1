"""Behavioral tests for tufctl delegation threshold rotation verifier."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest
from reference_tuf import (
    load_staging,
    reference_rejected_lines,
    reference_report,
    reference_verify,
)

TUFCTL = "/app/bin/tufctl"
STAGING = Path("/app/state/tuf-staging.json")
VERIFY = Path("/app/state/verify-result.json")
REPORT = Path("/app/output/delegation-report.json")
REJECTED = Path("/app/output/rejected-targets.jsonl")
METADATA = Path("/app/data/metadata")
TB3_META = Path("/tests/verifier-fixtures/tb3-metadata")
REUSE_META = Path("/tests/verifier-fixtures/reuse-metadata")


def _run(cmd: list[str], *, env: dict | None = None, check: bool = True) -> subprocess.CompletedProcess:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(cmd, check=check, capture_output=True, text=True, env=merged)


def _fresh() -> None:
    for p in (STAGING, VERIFY, REPORT, REJECTED):
        if p.exists():
            p.unlink()


def _ingest(meta_dir: Path) -> None:
    _run([TUFCTL, "ingest", str(meta_dir)])


def _verify(epoch: int, *, env: dict | None = None) -> None:
    _run([TUFCTL, "verify", "rotation", "--epoch", str(epoch)], env=env)


def _export() -> None:
    _run([TUFCTL, "export", "report"])


def _pipeline(meta_dir: Path, epoch: int, *, env: dict | None = None) -> None:
    _fresh()
    _ingest(meta_dir)
    _verify(epoch, env=env)
    _export()


@pytest.fixture(autouse=True)
def clean_state():
    _fresh()
    yield
    _fresh()


def test_tufctl_binary_exists():
    """Instruction requires /app/bin/tufctl built from the workspace."""
    assert Path(TUFCTL).is_file()


def test_bundled_metadata_directory():
    """Instruction cites bundled metadata under /app/data/metadata."""
    assert METADATA.is_dir()
    assert (METADATA / "root.json").is_file()
    assert (METADATA / "targets.json").is_file()
    assert (METADATA / "snapshot.json").is_file()


def test_ingest_writes_staging_snapshot():
    """Ingest must write normalized staging at /app/state/tuf-staging.json."""
    _ingest(METADATA)
    assert STAGING.is_file()
    staging = load_staging(STAGING)
    assert staging["targets_version"] == 3
    assert len(staging["delegations"]) == 2


def test_ingest_increments_seq():
    """Repeated ingest bumps ingest_seq monotonically."""
    _ingest(METADATA)
    first = load_staging(STAGING)["ingest_seq"]
    _ingest(METADATA)
    second = load_staging(STAGING)["ingest_seq"]
    assert second == first + 1


def test_staging_path_contract():
    """Instruction staging path /app/state/tuf-staging.json is honored."""
    _ingest(METADATA)
    assert STAGING == Path("/app/state/tuf-staging.json")


def test_verify_writes_result_at_epoch_40():
    """verify rotation writes /app/state/verify-result.json with epoch."""
    _ingest(METADATA)
    _verify(40)
    assert VERIFY.is_file()
    data = json.loads(VERIFY.read_text(encoding="utf-8"))
    assert data["epoch"] == 40


def test_rotation_ok_bundled_epoch_40():
    """Bundled metadata passes rotation at epoch 40 per reference verifier."""
    _ingest(METADATA)
    _verify(40)
    got = json.loads(VERIFY.read_text(encoding="utf-8"))
    ref = reference_verify(METADATA, load_staging(STAGING), 40)
    assert got["rotation_ok"] == ref["rotation_ok"]
    assert got["rotation_ok"] is True


def test_snapshot_linkage_matches_reference():
    """snapshot-version-link.md coupling matches independent reference."""
    _ingest(METADATA)
    _verify(40)
    got = json.loads(VERIFY.read_text(encoding="utf-8"))
    ref = reference_verify(METADATA, load_staging(STAGING), 40)
    assert got["snapshot_link_ok"] == ref["snapshot_link_ok"]


def test_threshold_metadata_matches_reference():
    """threshold-signatures.md quorum outcomes match reference."""
    _ingest(METADATA)
    _verify(40)
    got = json.loads(VERIFY.read_text(encoding="utf-8"))
    ref = reference_verify(METADATA, load_staging(STAGING), 40)
    assert got["metadata"] == ref["metadata"]


def test_epoch_50_fails_when_root_key_expires():
    """key-expiry-epochs.md strict less-than fails rotation at epoch 50."""
    _ingest(METADATA)
    _verify(50)
    got = json.loads(VERIFY.read_text(encoding="utf-8"))
    ref = reference_verify(METADATA, load_staging(STAGING), 50)
    assert got == ref
    assert got["rotation_ok"] is False


def test_export_report_paths():
    """export report writes delegation-report.json output path."""
    _pipeline(METADATA, 40)
    assert REPORT.is_file()
    assert str(REPORT) == "/app/output/delegation-report.json"


def test_rejected_targets_jsonl_path():
    """export report writes rejected-target evidence at /app/output/rejected-targets.jsonl."""
    _pipeline(METADATA, 40)
    assert REJECTED.is_file()
    assert str(REJECTED) == "/app/output/rejected-targets.jsonl"
    assert REJECTED.read_text(encoding="utf-8").strip()


def test_delegation_report_matches_reference():
    """delegation-report-schema.md report body matches independent reference."""
    _pipeline(METADATA, 40)
    got = json.loads(REPORT.read_text(encoding="utf-8"))
    verify = json.loads(VERIFY.read_text(encoding="utf-8"))
    ref = reference_report(load_staging(STAGING), verify)
    assert got == ref


def test_public_readme_rejected_no_delegation():
    """delegation-paths.md rejects targets outside any delegation scope."""
    _pipeline(METADATA, 40)
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    row = next(r for r in report["decisions"] if r["path"] == "public/readme.txt")
    assert row["allowed"] is False
    assert row["reason"] == "no_delegation"


def test_release_targets_allowed():
    """release/* delegation allows single-segment release paths."""
    _pipeline(METADATA, 40)
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    paths = {r["path"]: r for r in report["decisions"]}
    assert paths["release/app-v1.tar.gz"]["allowed"] is True
    assert paths["release/patch-v2.bin"]["delegation"] == "release"


def test_internal_glob_matches_nested_path():
    """internal/** delegation allows multi-segment internal paths."""
    _pipeline(METADATA, 40)
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    row = next(r for r in report["decisions"] if r["path"] == "internal/tools/debug.zip")
    assert row["allowed"] is True
    assert row["delegation"] == "internal"


def test_rejected_targets_jsonl_matches_reference():
    """rejected-targets.jsonl lines match reference rejection ledger."""
    _pipeline(METADATA, 40)
    lines = [ln for ln in REJECTED.read_text(encoding="utf-8").splitlines() if ln.strip()]
    verify = json.loads(VERIFY.read_text(encoding="utf-8"))
    ref = reference_report(load_staging(STAGING), verify)
    assert lines == reference_rejected_lines(ref)


def test_audit_digest_matches_reference():
    """audit_digest uses canonical JSON of decisions per report schema."""
    _pipeline(METADATA, 40)
    got = json.loads(REPORT.read_text(encoding="utf-8"))["audit_digest"]
    verify = json.loads(VERIFY.read_text(encoding="utf-8"))
    ref = reference_report(load_staging(STAGING), verify)["audit_digest"]
    assert got == ref
    assert len(got) == 64


def test_subprocess_cli_roundtrip():
    """Independent reference agrees after subprocess ingest verify export."""
    _pipeline(METADATA, 40)
    verify = json.loads(VERIFY.read_text(encoding="utf-8"))
    ref_verify = reference_verify(METADATA, load_staging(STAGING), 40)
    assert verify == ref_verify


def test_instruction_metadata_paths_exercised():
    """Instruction paths /app/data/metadata are exercised end-to-end."""
    assert list(METADATA.glob("*.json"))
    _pipeline(METADATA, 40)
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["rotation_ok"] is True


def _tb3_dir() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="tb3-meta-"))
    for name in ("root.json", "targets.json", "snapshot.json"):
        shutil.copy(TB3_META / name, tmp / name)
    return tmp


def _reuse_dir() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="reuse-meta-"))
    for name in ("root.json", "targets.json", "snapshot.json"):
        shutil.copy(REUSE_META / name, tmp / name)
    return tmp


def test_reuse_violation_fails_rotation():
    """key-reuse-ban.md ignores root keyids on targets signatures."""
    meta = _reuse_dir()
    try:
        _ingest(meta)
        _verify(40)
        got = json.loads(VERIFY.read_text(encoding="utf-8"))
        ref = reference_verify(meta, load_staging(STAGING), 40)
        assert got == ref
        targets_row = next(m for m in got["metadata"] if m["role"] == "targets")
        assert targets_row["reuse_violations"] == ["f9ecab9dca0ed718"]
        assert targets_row["valid_signatures"] == 1
        assert targets_row["threshold_met"] is False
        assert got["rotation_ok"] is False
    finally:
        shutil.rmtree(meta, ignore_errors=True)


def test_tb3_hidden_delegation_narrow_wins():
    """Hidden tb3 metadata picks staging-narrow by literal pattern score."""
    meta = _tb3_dir()
    try:
        _pipeline(meta, 40)
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        row = next(r for r in report["decisions"] if r["path"] == "staging/artifacts/pkg-9.tgz")
        assert row["delegation"] == "staging-narrow"
        verify = json.loads(VERIFY.read_text(encoding="utf-8"))
        ref = reference_report(load_staging(STAGING), verify)
        assert report["decisions"] == ref["decisions"]
    finally:
        shutil.rmtree(meta, ignore_errors=True)


def test_tb3_hidden_staging_logs_broader_delegation():
    """Hidden tb3 path staging/logs uses broader staging delegation."""
    meta = _tb3_dir()
    try:
        _pipeline(meta, 40)
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        row = next(r for r in report["decisions"] if r["path"] == "staging/logs/trace.log")
        assert row["delegation"] == "staging"
        assert row["allowed"] is True
    finally:
        shutil.rmtree(meta, ignore_errors=True)


def test_tb3_epoch_bias_env():
    """TB3_EPOCH_BIAS offsets verification epoch for hidden fixtures."""
    meta = _tb3_dir()
    try:
        _fresh()
        _ingest(meta)
        bias = 80
        _verify(40, env={"TB3_EPOCH_BIAS": str(bias)})
        effective = 40 + bias
        got = json.loads(VERIFY.read_text(encoding="utf-8"))
        ref = reference_verify(meta, load_staging(STAGING), effective)
        assert got == ref
        assert got["rotation_ok"] is False
    finally:
        shutil.rmtree(meta, ignore_errors=True)


def test_tb3_hidden_report_digest():
    """Hidden fixture audit_digest matches reference canonical digest."""
    meta = _tb3_dir()
    try:
        _pipeline(meta, 40)
        got = json.loads(REPORT.read_text(encoding="utf-8"))
        verify = json.loads(VERIFY.read_text(encoding="utf-8"))
        ref = reference_report(load_staging(STAGING), verify)
        assert got["audit_digest"] == ref["audit_digest"]
    finally:
        shutil.rmtree(meta, ignore_errors=True)


def test_decisions_sorted_by_path():
    """delegation-report-schema.md requires decisions sorted by path."""
    _pipeline(METADATA, 40)
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    paths = [r["path"] for r in report["decisions"]]
    assert paths == sorted(paths)
