"""Verifier tests for rust-avro-schema-evolution-compatibility-ledger."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from avro_compat_ref import (
    parsing_fingerprint,
    reference_migration_report,
    reference_pair_ledger,
)

APP = Path("/app")
ENV = APP / "environment"
BIN = ENV / "tools" / "avsccompat" / "avsccompat"
BUILD = ENV / "scripts" / "build_all.sh"
STATE = APP / "state" / "schema_pair_ledger.jsonl"
OUT = APP / "output" / "avro_migration_report.json"
DEFAULT_SCHEMA = ENV / "fixtures" / "schemas"
DEFAULT_PAIRS = ENV / "fixtures" / "schema_pairs.jsonl"
HIDDEN_ROOT = Path("/opt/verifier-fixtures/avro_hidden")


def schema_dir() -> Path:
    tb3 = os.environ.get("TB3_SCHEMA_DIR")
    return Path(tb3) if tb3 else DEFAULT_SCHEMA


def pairs_file() -> Path:
    tb3 = os.environ.get("TB3_PAIRS_FILE")
    return Path(tb3) if tb3 else DEFAULT_PAIRS


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)


def rebuild() -> None:
    run(["bash", str(BUILD)])


def run_compat_pipeline(schema: Path | None = None, pairs: Path | None = None) -> None:
    schema = schema or schema_dir()
    pairs = pairs or pairs_file()
    STATE.parent.mkdir(parents=True, exist_ok=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if STATE.exists():
        STATE.unlink()
    if OUT.exists():
        OUT.unlink()
    run([str(BIN), "ingest", "--schema-dir", str(schema), "--pairs", str(pairs), "--staging", str(STATE)])
    run([str(BIN), "export", "--staging", str(STATE), "--out", str(OUT)])


def load_report() -> dict:
    return json.loads(OUT.read_text(encoding="utf-8"))


def load_staging() -> list[dict]:
    return [json.loads(ln) for ln in STATE.read_text(encoding="utf-8").splitlines() if ln.strip()]


def load_schema(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_avsc_compat_release_build_ok():
    """Release rebuild must produce the avsccompat binary under tools/avsccompat."""
    rebuild()
    assert BIN.is_file()


def test_avsc_compat_cli_ingest_export_zero():
    """Ingest and export subprocesses must write the report to /app/output/avro_migration_report.json"""
    rebuild()
    run_compat_pipeline()
    assert OUT.is_file()


def test_avsc_compat_report_has_subjects_totals():
    """Migration report must expose subjects and totals sections per export contract."""
    rebuild()
    run_compat_pipeline()
    data = load_report()
    assert "subjects" in data and "totals" in data


def test_avsc_compat_totals_pair_count():
    """totals.pair_count must equal the number of evaluated subject rows."""
    rebuild()
    run_compat_pipeline()
    data = load_report()
    assert data["totals"]["pair_count"] == len(data["subjects"])


def test_avsc_compat_export_subject_order():
    """Export subjects must be sorted lexicographically by subject name."""
    rebuild()
    run_compat_pipeline()
    names = [s["subject"] for s in load_report()["subjects"]]
    assert names == sorted(names)


def test_avsc_compat_jsonl_staging_created():
    """Ingest must persist /app/state/schema_pair_ledger.jsonl before export."""
    rebuild()
    run_compat_pipeline()
    assert STATE.is_file()
    assert len(load_staging()) >= 4


def test_avsc_compat_jsonl_subject_order():
    """Staging JSONL rows must be sorted by subject after ingest."""
    rebuild()
    run_compat_pipeline()
    subjects = [r["subject"] for r in load_staging()]
    assert subjects == sorted(subjects)


def test_avsc_compat_user_reader_writer_ok():
    """User subject compatibility must match independent reference evaluation."""
    rebuild()
    run_compat_pipeline()
    row = next(r for r in load_staging() if r["subject"] == "User")
    ref = next(r for r in reference_pair_ledger(schema_dir(), pairs_file()) if r["subject"] == "User")
    assert row["compatible"] == ref["compatible"]
    assert row["checks"]["union_order_ok"] == ref["checks"]["union_order_ok"]


def test_avsc_compat_payment_reader_writer_ok():
    """Payment subject compatibility must match independent reference evaluation."""
    rebuild()
    run_compat_pipeline()
    row = next(r for r in load_staging() if r["subject"] == "Payment")
    ref = next(r for r in reference_pair_ledger(schema_dir(), pairs_file()) if r["subject"] == "Payment")
    assert row["compatible"] == ref["compatible"]
    assert row["writer_fingerprint"] == ref["writer_fingerprint"]


def test_avsc_compat_envelope_int_long_ok():
    """Envelope subject must stay compatible when payload promotes int to long."""
    rebuild()
    run_compat_pipeline()
    row = next(r for r in load_staging() if r["subject"] == "Envelope")
    ref = next(r for r in reference_pair_ledger(schema_dir(), pairs_file()) if r["subject"] == "Envelope")
    assert row["compatible"] == ref["compatible"]


def test_avsc_compat_metric_timestamp_millis():
    """Metric subject must pass logical type checks for timestamp-millis fields."""
    rebuild()
    run_compat_pipeline()
    row = next(r for r in load_staging() if r["subject"] == "Metric")
    assert row["checks"]["logical_types_ok"] is True


def test_avsc_compat_user_v1_fingerprint():
    """Writer fingerprint for user_v1 must match canonical parsing fingerprint rules."""
    rebuild()
    run_compat_pipeline()
    row = next(r for r in load_staging() if r["subject"] == "User")
    ref_fp = parsing_fingerprint(load_schema(schema_dir() / "user_v1.avsc"))
    assert row["writer_fingerprint"] == ref_fp


def test_avsc_compat_staging_rows_reference():
    """Every staged row must match reference_pair_ledger for bundled fixtures."""
    rebuild()
    run_compat_pipeline()
    got = load_staging()
    ref = reference_pair_ledger(schema_dir(), pairs_file())
    assert len(got) == len(ref)
    for g, r in zip(got, ref):
        assert g["subject"] == r["subject"]
        assert g["compatible"] == r["compatible"]
        assert g["writer_fingerprint"] == r["writer_fingerprint"]
        assert g["reader_fingerprint"] == r["reader_fingerprint"]
        assert g["checks"] == r["checks"]


def test_avsc_compat_report_totals_reference():
    """Report totals must match reference_migration_report aggregate counts."""
    rebuild()
    run_compat_pipeline()
    got = load_report()
    ref = reference_migration_report(schema_dir(), pairs_file())
    assert got["totals"]["pair_count"] == ref["totals"]["pair_count"]
    assert got["totals"]["compatible_count"] == ref["totals"]["compatible_count"]


def test_avsc_compat_compatible_risk_low():
    """Compatible pairs must export risk_level low per migration policy."""
    rebuild()
    run_compat_pipeline()
    for s in load_report()["subjects"]:
        if s["compatible"]:
            assert s["risk_level"] == "low"


def test_avsc_compat_report_subjects_reference():
    """Each export subject row must match reference migration report fields."""
    rebuild()
    run_compat_pipeline()
    got = {s["subject"]: s for s in load_report()["subjects"]}
    ref = {s["subject"]: s for s in reference_migration_report(schema_dir(), pairs_file())["subjects"]}
    for subj in ref:
        assert got[subj]["risk_level"] == ref[subj]["risk_level"]
        assert got[subj]["compatible"] == ref[subj]["compatible"]


def test_avsc_compat_repeat_export_bytes():
    """Repeated export with unchanged staging must produce identical report bytes."""
    rebuild()
    run_compat_pipeline()
    first = OUT.read_bytes()
    run_compat_pipeline()
    second = OUT.read_bytes()
    assert first == second


def test_avsc_compat_split_ingest_export():
    """Export-only stage must consume existing staging without re-ingesting."""
    rebuild()
    schema = schema_dir()
    pairs = pairs_file()
    alt_state = APP / "state" / "alt_staging.jsonl"
    alt_out = APP / "output" / "alt_report.json"
    run([str(BIN), "ingest", "--schema-dir", str(schema), "--pairs", str(pairs), "--staging", str(alt_state)])
    run([str(BIN), "export", "--staging", str(alt_state), "--out", str(alt_out)])
    data = json.loads(alt_out.read_text(encoding="utf-8"))
    assert data["totals"]["pair_count"] >= 4


def test_avsc_compat_user_namespace_alias():
    """User reader namespace alias resolution must pass namespace_alias check."""
    rebuild()
    run_compat_pipeline()
    row = next(r for r in load_staging() if r["subject"] == "User")
    assert row["checks"]["namespace_alias_ok"] is True


def test_avsc_compat_status_union_branches():
    """Union branch order differences must not break compatibility when sets match."""
    rebuild()
    run_compat_pipeline()
    row = next(r for r in load_staging() if r["subject"] == "User")
    assert row["checks"]["union_order_ok"] is True


def test_avsc_compat_decoy_not_in_report():
    """telemetry_decoy scaffolding must not appear in migration export output."""
    rebuild()
    run_compat_pipeline()
    raw = OUT.read_text(encoding="utf-8")
    assert "wrap_schema_bytes" not in raw


def test_avsc_compat_hidden_pair_reference():
    """TB3 hidden trap: alternate schema dir must evaluate Order pair compatibility."""
    if not HIDDEN_ROOT.is_dir():
        return
    hidden_schema = HIDDEN_ROOT / "schemas"
    hidden_pairs = HIDDEN_ROOT / "pairs.jsonl"
    if not hidden_schema.is_dir() or not hidden_pairs.is_file():
        return
    rebuild()
    os.environ["TB3_SCHEMA_DIR"] = str(hidden_schema)
    os.environ["TB3_PAIRS_FILE"] = str(hidden_pairs)
    try:
        run_compat_pipeline(hidden_schema, hidden_pairs)
        row = load_staging()[0]
        ref = reference_pair_ledger(hidden_schema, hidden_pairs)[0]
        assert row["subject"] == "Order"
        assert row["compatible"] == ref["compatible"]
        assert row["checks"]["defaults_ok"] == ref["checks"]["defaults_ok"]
    finally:
        os.environ.pop("TB3_SCHEMA_DIR", None)
        os.environ.pop("TB3_PAIRS_FILE", None)


def test_avsc_compat_hidden_schema_override():
    """TB3 schema directory override must drive ingest and export correctly."""
    if not HIDDEN_ROOT.is_dir():
        return
    hidden_schema = HIDDEN_ROOT / "schemas"
    hidden_pairs = HIDDEN_ROOT / "pairs.jsonl"
    if not hidden_schema.is_dir() or not hidden_pairs.is_file():
        return
    rebuild()
    os.environ["TB3_SCHEMA_DIR"] = str(hidden_schema)
    os.environ["TB3_PAIRS_FILE"] = str(hidden_pairs)
    try:
        run_compat_pipeline(hidden_schema, hidden_pairs)
        got = load_report()
        ref = reference_migration_report(hidden_schema, hidden_pairs)
        assert got["totals"]["pair_count"] == ref["totals"]["pair_count"]
        assert got["subjects"][0]["writer_fingerprint"] == ref["subjects"][0]["writer_fingerprint"]
    finally:
        os.environ.pop("TB3_SCHEMA_DIR", None)
        os.environ.pop("TB3_PAIRS_FILE", None)


def test_avsc_compat_subprocess_reference_cli():
    """Grading must invoke avsccompat via subprocess after rebuild, not inline logic."""
    rebuild()
    schema = schema_dir()
    pairs = pairs_file()
    staging = APP / "state" / "probe_staging.jsonl"
    out = APP / "output" / "probe_report.json"
    run([str(BIN), "ingest", "--schema-dir", str(schema), "--pairs", str(pairs), "--staging", str(staging)])
    run([str(BIN), "export", "--staging", str(staging), "--out", str(out)])
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["totals"]["pair_count"] >= 4


def test_avsc_compat_violation_count_field():
    """Each subject violation_count must equal len(violations) in export rows."""
    rebuild()
    run_compat_pipeline()
    for s in load_report()["subjects"]:
        assert s["violation_count"] == len(s["violations"])


def test_avsc_compat_instruction_paths_exist():
    """Verify instruction staging and export paths exist after the compatibility pipeline runs."""
    rebuild()
    run_compat_pipeline()
    assert Path("/app/state/schema_pair_ledger.jsonl").is_file()
    assert Path("/app/output/avro_migration_report.json").is_file()

