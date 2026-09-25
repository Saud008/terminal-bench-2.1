from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import uuid
from pathlib import Path

import pytest

from reference_drift import (
    expected_export_exit,
    expected_report,
    expected_stage,
    expected_stage_evaluated,
    load_json,
    make_random_readings,
    stage_path_for,
)

BIN = Path("/app/bin/icc-drift-bundler")
READINGS = Path("/app/fixtures/seed/readings.tsv")
PROFILE = Path("/app/fixtures/profiles/coated-gloss.json")
BAD_PROFILE = Path("/app/fixtures/profiles/bad-checksum-profile.json")
PAPER = Path("/app/fixtures/paper/batches.json")
POLICY = Path("/app/config/drift-policy.json")
TICKETS = Path("/app/fixtures/tickets/calibration.json")
OUTPUT = Path("/app/output")
STATE = Path("/app/state")
STAGING = stage_path_for(READINGS)
REPORT = OUTPUT / "drift-report.json"
AS_OF = 1722470400
LIB = Path("/app/lib")
BROKEN = Path("/opt/verifier-broken-icc")
GOLDEN = Path("/tests/golden_lib")
TB3_READINGS = Path("/opt/verifier-fixtures/icc/tb3-readings.tsv")
TB3_PROFILE = Path("/opt/verifier-fixtures/icc/tb3-profile.json")
TB3_PAPER = Path("/opt/verifier-fixtures/icc/tb3-paper.json")
TB3_TICKETS = Path("/opt/verifier-fixtures/icc/tb3-tickets.json")
TB3_META = Path("/opt/verifier-fixtures/icc/tb3-meta.json")
CAT = load_json(Path("/app/fixtures/catalog.json"))
MODULES = (
    "common",
    "parse_readings",
    "lab_delta",
    "paper_lineage",
    "intent_policy",
    "profile_checksum",
    "ticket_epoch",
    "staging",
    "export_report",
)


def _tool_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    merged = os.environ.copy()
    merged["PATH"] = "/app/bin:/opt/verifier-venv/bin:/usr/local/bin:" + merged.get("PATH", "")
    merged["APP_ROOT"] = "/app"
    if extra:
        merged.update(extra)
    return merged


def run(cmd: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd, cwd="/app", capture_output=True, text=True, check=False, env=_tool_env(env)
    )


def reset() -> None:
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    if STAGING.exists():
        STAGING.unlink()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    STATE.mkdir(parents=True, exist_ok=True)
    Path("/app/state/run-registry.json").write_text('{"runs":[]}\n', encoding="utf-8")


def ingest(
    readings: Path = READINGS,
    profile: Path = PROFILE,
    paper: Path = PAPER,
) -> subprocess.CompletedProcess[str]:
    return run([str(BIN), "ingest", "--readings", str(readings), "--profile", str(profile), "--paper", str(paper)])


def evaluate(
    readings: Path = READINGS,
    profile: Path = PROFILE,
    paper: Path = PAPER,
    policy: Path = POLICY,
    tickets: Path = TICKETS,
    as_of: int = AS_OF,
) -> subprocess.CompletedProcess[str]:
    return run(
        [
            str(BIN),
            "evaluate",
            "--readings",
            str(readings),
            "--profile",
            str(profile),
            "--paper",
            str(paper),
            "--policy",
            str(policy),
            "--tickets",
            str(tickets),
            "--as-of",
            str(as_of),
        ]
    )


def export_report(
    readings: Path = READINGS,
    out: Path = REPORT,
) -> subprocess.CompletedProcess[str]:
    return run([str(BIN), "export", "--readings", str(readings), "--out", str(out)])


def pipeline(
    readings: Path = READINGS,
    profile: Path = PROFILE,
    paper: Path = PAPER,
    policy: Path = POLICY,
    tickets: Path = TICKETS,
    as_of: int = AS_OF,
    out: Path = REPORT,
) -> subprocess.CompletedProcess[str]:
    proc = ingest(readings, profile, paper)
    if proc.returncode != 0:
        return proc
    proc = evaluate(readings, profile, paper, policy, tickets, as_of)
    if proc.returncode != 0:
        return proc
    return export_report(readings, out)


def install_modules(only_broken: set[str]) -> None:
    for mod in MODULES:
        src = BROKEN / f"{mod}.sh" if mod in only_broken else GOLDEN / f"{mod}.sh"
        shutil.copy2(src, LIB / f"{mod}.sh")
        os.chmod(LIB / f"{mod}.sh", 0o755)


@pytest.fixture(autouse=True)
def _reset() -> None:
    reset()


def test_catalog_lists_scenarios() -> None:
    """Fixture catalog exposes bundled ICC softproof scenarios."""
    assert len(CAT["scenarios"]) >= 1


def test_binary_exists() -> None:
    """icc-drift-bundler CLI is installed at /app/bin/icc-drift-bundler."""
    assert BIN.is_file()


def test_ingest_writes_expected_staging() -> None:
    """ingest writes icc.stage.json beside readings matching independent reference."""
    proc = ingest()
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert STAGING.is_file()
    assert load_json(STAGING) == expected_stage(READINGS, PROFILE, PAPER)


def test_ingest_does_not_write_report() -> None:
    """ingest alone must not create /app/output/drift-report.json."""
    proc = ingest()
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert STAGING.is_file()
    assert not REPORT.exists()


def test_staging_beside_readings_not_global_state(tmp_path: Path) -> None:
    """Staging snapshot path is dirname(readings)/icc.stage.json."""
    suffix = uuid.uuid4().hex[:8]
    work = tmp_path / f"work_{suffix}"
    work.mkdir()
    readings = work / "readings.tsv"
    shutil.copy2(READINGS, readings)
    stage = stage_path_for(readings)
    proc = ingest(readings)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert stage.is_file()
    assert stage.parent == readings.parent


def test_seed_pipeline_report() -> None:
    """Full pipeline writes drift report matching independent reference oracle."""
    stage = expected_stage_evaluated(READINGS, PROFILE, PAPER, POLICY, TICKETS, AS_OF)
    expected = expected_report(stage)
    proc = pipeline()
    assert proc.returncode == expected_export_exit(expected), proc.stderr or proc.stdout
    assert REPORT.is_file()
    assert load_json(REPORT) == expected


def test_p200_delta_e_drift_flag() -> None:
    """P-200 reading exceeds delta_e_threshold and receives DRIFT_DELTA_E."""
    stage = expected_stage_evaluated(READINGS, PROFILE, PAPER, POLICY, TICKETS, AS_OF)
    row = next(r for r in stage["evaluation"]["per_patch"] if r["patch_id"] == "P-200")
    assert "DRIFT_DELTA_E" in row["drift_flags"]
    assert row["delta_e"] > 2.0


def test_paper_lineage_inherited_gamma() -> None:
    """PB-CHILD inherits gamma_anchor 1.8 from PB-ROOT lineage."""
    stage = expected_stage_evaluated(READINGS, PROFILE, PAPER, POLICY, TICKETS, AS_OF)
    row = next(r for r in stage["evaluation"]["per_patch"] if r["patch_id"] == "P-100")
    assert row["effective_gamma"] == 1.8


def test_active_intent_perceptual() -> None:
    """Rendering intent precedence selects perceptual for coated gloss profile."""
    stage = expected_stage_evaluated(READINGS, PROFILE, PAPER, POLICY, TICKETS, AS_OF)
    intents = {r["patch_id"]: r["active_intent"] for r in stage["evaluation"]["per_patch"]}
    assert all(v == "perceptual" for v in intents.values())


def test_export_reads_staging_only() -> None:
    """export evaluates frozen staging and ignores later readings mutations."""
    proc = ingest()
    assert proc.returncode == 0
    scratch = OUTPUT / "mutated.tsv"
    shutil.copy2(READINGS, scratch)
    scratch.write_text("patch_id\tL\ta\tb\tbatch_id\nX\t0\t0\t0\tPB-ROOT\n", encoding="utf-8")
    proc_eval = evaluate()
    assert proc_eval.returncode == 0
    out = OUTPUT / "export-only.json"
    proc_export = export_report(out=out)
    report = expected_report(load_json(STAGING))
    assert proc_export.returncode == expected_export_exit(report)
    assert load_json(out) == report


def test_export_exit_code_two_on_drift() -> None:
    """export exits 2 when summary.drift_count is greater than zero."""
    proc = pipeline()
    report = load_json(REPORT)
    if report["summary"]["drift_count"] > 0:
        assert proc.returncode == 2


def test_report_carries_staging_digests() -> None:
    """Report copies readings and profile digests from staging."""
    pipeline()
    stage = load_json(STAGING)
    report = load_json(REPORT)
    assert report["readings_digest"] == stage["readings_digest"]
    assert report["profile_digest"] == stage["profile_digest"]


def test_duplicate_patch_last_line_wins(tmp_path: Path) -> None:
    """Duplicate patch_id lines keep the last occurrence in file order."""
    suffix = uuid.uuid4().hex[:10]
    readings = tmp_path / f"dup_{suffix}.tsv"
    readings.write_text(
        f"patch_id\tL\ta\tb\tbatch_id\n"
        f"DUP-{suffix}\t40.0\t1.0\t1.0\tPB-ROOT\n"
        f"DUP-{suffix}\t50.0\t10.0\t5.0\tPB-CHILD\n",
        encoding="utf-8",
    )
    proc = ingest(readings)
    assert proc.returncode == 0
    got = load_json(stage_path_for(readings))
    row = next(r for r in got["patches"] if r["patch_id"] == f"DUP-{suffix}")
    assert row["L"] == 50.0
    assert row["batch_id"] == "PB-CHILD"


def test_random_patch_ids_independent_oracle(tmp_path: Path) -> None:
    """Randomized patch ids and LAB values match reference oracle."""
    suffix = uuid.uuid4().hex[:12]
    readings = tmp_path / f"rand_{suffix}.tsv"
    readings.write_text(make_random_readings(suffix), encoding="utf-8")
    out = tmp_path / "report.json"
    stage = expected_stage_evaluated(readings, PROFILE, PAPER, POLICY, TICKETS, AS_OF)
    expected = expected_report(stage)
    proc = pipeline(readings=readings, out=out)
    assert proc.returncode == expected_export_exit(expected)
    assert load_json(out) == expected


def test_bad_checksum_profile_flags(tmp_path: Path) -> None:
    """Invalid profile checksum adds PROFILE_CHECKSUM_MISMATCH to every patch."""
    suffix = uuid.uuid4().hex[:8]
    readings = tmp_path / f"chk_{suffix}.tsv"
    readings.write_text(
        f"patch_id\tL\ta\tb\tbatch_id\nCHK-{suffix}\t50.0\t10.0\t5.0\tPB-ROOT\n",
        encoding="utf-8",
    )
    stage = expected_stage_evaluated(readings, BAD_PROFILE, PAPER, POLICY, TICKETS, AS_OF)
    assert all(
        "PROFILE_CHECKSUM_MISMATCH" in row["drift_flags"] for row in stage["evaluation"]["per_patch"]
    )
    out = tmp_path / "bad.json"
    pipeline(readings=readings, profile=BAD_PROFILE, out=out)
    report = load_json(out)
    assert report["summary"]["checksum_fail_count"] >= 1


def test_ticket_valid_from_boundary_inclusive(tmp_path: Path) -> None:
    """Calibration ticket valid_from_epoch boundary is inclusive."""
    suffix = uuid.uuid4().hex[:8]
    readings = tmp_path / f"tkt_{suffix}.tsv"
    readings.write_text(
        f"patch_id\tL\ta\tb\tbatch_id\nTKT-{suffix}\t50.0\t10.0\t5.0\tPB-CHILD\n",
        encoding="utf-8",
    )
    as_of = 1717200000
    stage = expected_stage_evaluated(readings, PROFILE, PAPER, POLICY, TICKETS, as_of)
    row = stage["evaluation"]["per_patch"][0]
    assert "TICKET_EPOCH_INVALID" not in row["drift_flags"]
    assert row["ticket_id"] == "CT-2024-Q3"


def test_run_registry_tracks_readings_digest() -> None:
    """ingest updates /app/state/run-registry.json with readings digest."""
    proc = ingest()
    assert proc.returncode == 0
    digest = hashlib.sha256(READINGS.read_bytes()).hexdigest()
    registry = load_json(STATE / "run-registry.json")
    assert registry["runs"][-1]["readings_digest"] == digest


def test_decoy_not_on_hot_path() -> None:
    """legacy_gamut decoy exists but pipeline still passes with golden modules."""
    decoy = Path("/app/lib/decoy/legacy_gamut.sh")
    assert decoy.is_file()
    proc = pipeline()
    stage = expected_stage_evaluated(READINGS, PROFILE, PAPER, POLICY, TICKETS, AS_OF)
    expected = expected_report(stage)
    assert proc.returncode == expected_export_exit(expected)


def test_patches_sorted_lexicographically() -> None:
    """Report patch rows sort by patch_id ascending."""
    pipeline()
    report = load_json(REPORT)
    ids = [row["patch_id"] for row in report["patches"]]
    assert ids == sorted(ids)


@pytest.mark.skipif(not TB3_READINGS.is_file(), reason="TB3 fixtures not mounted")
def test_tb3_random_patches_require_full_pipeline() -> None:
    """TB3 seeded readings use random patch ids requiring full drift pipeline."""
    meta = load_json(TB3_META)
    suffix = meta["suffix"]
    proc = pipeline(
        readings=TB3_READINGS,
        profile=TB3_PROFILE,
        paper=TB3_PAPER,
        tickets=TB3_TICKETS,
        out=OUTPUT / "tb3.json",
    )
    stage = expected_stage_evaluated(TB3_READINGS, TB3_PROFILE, TB3_PAPER, POLICY, TB3_TICKETS, AS_OF)
    expected = expected_report(stage)
    assert proc.returncode == expected_export_exit(expected)
    assert any(f"TB3-{suffix}" in row["patch_id"] for row in load_json(OUTPUT / "tb3.json")["patches"])


@pytest.mark.skipif(not TB3_READINGS.is_file(), reason="TB3 fixtures not mounted")
def test_tb3_hidden_not_in_catalog() -> None:
    """Hidden TB3 readings are not listed in bundled catalog."""
    meta = load_json(TB3_META)
    assert meta["suffix"]
    assert not any(s["id"] == f"tb3_{meta['suffix']}" for s in CAT["scenarios"])


def test_partial_staging_eval_stub_zeros_delta() -> None:
    """Staging-only partial fix leaves zero delta_e on known drift patch P-200."""
    install_modules({"staging"})
    try:
        proc = ingest()
        assert proc.returncode == 0
        proc = evaluate()
        assert proc.returncode == 0
        stage = load_json(STAGING)
        row = next(r for r in stage["evaluation"]["per_patch"] if r["patch_id"] == "P-200")
        assert row["delta_e"] == 0.0
        assert row["drift_flags"] == []
    finally:
        install_modules(set())


def test_partial_parse_first_line_wins_duplicate(tmp_path: Path) -> None:
    """Parse-only partial fix keeps first duplicate patch line instead of last."""
    install_modules({"parse_readings"})
    try:
        suffix = uuid.uuid4().hex[:8]
        readings = tmp_path / f"pdup_{suffix}.tsv"
        readings.write_text(
            f"patch_id\tL\ta\tb\tbatch_id\n"
            f"DUP-{suffix}\t40.0\t1.0\t1.0\tPB-ROOT\n"
            f"DUP-{suffix}\t50.0\t10.0\t5.0\tPB-CHILD\n",
            encoding="utf-8",
        )
        proc = ingest(readings)
        assert proc.returncode == 0
        got = load_json(stage_path_for(readings))
        row = next(r for r in got["patches"] if r["patch_id"] == f"DUP-{suffix}")
        assert row["L"] == 40.0
    finally:
        install_modules(set())


def test_partial_export_only_fix_zeros_drift() -> None:
    """Export-only partial fix emits zero drift_count despite evaluation."""
    install_modules({"export_report"})
    try:
        ingest()
        evaluate()
        out = OUTPUT / "partial.json"
        export_report(out=out)
        report = load_json(out)
        assert report["summary"]["drift_count"] == 0
    finally:
        install_modules(set())
