"""Behavioral verifier for s3lc S3 lifecycle cost simulator."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from s3lc_verifier_oracle import reference_pipeline

APP = Path("/app")
CLI = Path("/usr/local/bin/s3lc")
STAGING = APP / "state" / "s3lc.stage.json"
REPORT = APP / "output" / "monthly-cost.json"
INV = APP / "fixtures" / "inventory" / "seed.jsonl"
RULES = APP / "fixtures" / "rules" / "default.json"
HOLDS = APP / "fixtures" / "holds" / "empty.json"
RATES = APP / "fixtures" / "rates" / "us-east-1.json"
HIDDEN = Path("/opt/verifier-fixtures/s3lc_hidden")
WIN_START = "2024-06-01"
WIN_END = "2024-06-30"


def _run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=False, capture_output=True, text=True, cwd=str(APP), **kw)


def reset_state() -> None:
    proc = _run(["bash", str(APP / "scripts" / "reset-state.sh")])
    assert proc.returncode == 0, proc.stderr


def rebuild() -> None:
    proc = _run(["bash", str(APP / "scripts" / "rebuild-s3lc.sh")])
    assert proc.returncode == 0, proc.stderr


def inventory_file() -> Path:
    tb3 = os.environ.get("TB3_INVENTORY_FILE")
    return Path(tb3) if tb3 else INV


def rules_file() -> Path:
    tb3 = os.environ.get("TB3_RULES_FILE")
    return Path(tb3) if tb3 else RULES


def run_ingest(staging: Path = STAGING) -> subprocess.CompletedProcess:
    return _run(
        [
            str(CLI),
            "ingest",
            "--inventory",
            str(inventory_file()),
            "--bucket",
            "finops-ledger",
            "--staging",
            str(staging),
        ]
    )


def run_simulate(staging: Path = STAGING) -> subprocess.CompletedProcess:
    holds = HOLDS
    if os.environ.get("TB3_HOLDS_FILE"):
        holds = Path(os.environ["TB3_HOLDS_FILE"])
    return _run(
        [
            str(CLI),
            "simulate",
            "--staging",
            str(staging),
            "--rules",
            str(rules_file()),
            "--holds",
            str(holds),
            "--window-start",
            WIN_START,
            "--window-end",
            WIN_END,
        ]
    )


def run_cost(staging: Path = STAGING, out: Path = REPORT) -> subprocess.CompletedProcess:
    return _run(
        [
            str(CLI),
            "cost-report",
            "--staging",
            str(staging),
            "--rates",
            str(RATES),
            "--out",
            str(out),
        ]
    )


def run_export(staging: Path = STAGING, out: Path = REPORT) -> subprocess.CompletedProcess:
    return run_cost(staging=staging, out=out)


def run_pipeline() -> None:
    reset_state()
    rebuild()
    assert run_ingest().returncode == 0
    assert run_simulate().returncode == 0
    assert run_cost().returncode == 0


@pytest.fixture(autouse=True)
def _clean_env():
    reset_state()
    rebuild()
    for k in ("TB3_INVENTORY_FILE", "TB3_RULES_FILE", "TB3_HOLDS_FILE"):
        os.environ.pop(k, None)
    yield
    for k in ("TB3_INVENTORY_FILE", "TB3_RULES_FILE", "TB3_HOLDS_FILE"):
        os.environ.pop(k, None)


def test_tce6388_cli_installed():
    """Instruction requires s3lc at /usr/local/bin/s3lc."""
    assert CLI.is_file()


def test_tce6388_ingest_writes_staging_schema():
    """Ingest must write schema_version 1 staging with inventory_fingerprint."""
    assert run_ingest().returncode == 0
    doc = json.loads(STAGING.read_text(encoding="utf-8"))
    assert doc["schema_version"] == 1
    assert doc["bucket"] == "finops-ledger"
    assert len(doc["inventory_fingerprint"]) == 64
    assert doc["simulation"] is None


def test_tce6388_simulate_populates_simulation_block():
    """Simulate must write window bounds and simulation_digest."""
    run_pipeline()
    sim = json.loads(STAGING.read_text(encoding="utf-8"))["simulation"]
    assert sim["window_start"] == WIN_START
    assert sim["window_end"] == WIN_END
    assert len(sim["simulation_digest"]) == 64


def test_tce6388_access_log_transitions_to_glacier():
    """access-log-tier rule transitions aged access logs to GLACIER at window end."""
    run_pipeline()
    doc = json.loads(STAGING.read_text(encoding="utf-8"))
    ref_staging, _ = reference_pipeline(
        inventory_file(), "finops-ledger", rules_file(), HOLDS, RATES, WIN_START, WIN_END
    )
    got = {
        (t["key"], t["version_id"], t["storage_class"])
        for t in doc["simulation"]["transitions_applied"]
    }
    exp = {
        (t["key"], t["version_id"], t["storage_class"])
        for t in ref_staging["simulation"]["transitions_applied"]
    }
    assert got == exp


def test_tce6388_legal_hold_suppresses_archive_key():
    """archive/report-Q1.pdf legal hold suppresses transitions for the whole key."""
    run_pipeline()
    doc = json.loads(STAGING.read_text(encoding="utf-8"))
    assert "archive/report-Q1.pdf" in doc["simulation"]["suppressed_keys"]


def test_tce6388_delete_marker_orphan_noncurrent_count():
    """Delete marker on drafts/tmp.txt leaves one orphan noncurrent version."""
    run_pipeline()
    doc = json.loads(STAGING.read_text(encoding="utf-8"))
    ref, _ = reference_pipeline(
        inventory_file(), "finops-ledger", rules_file(), HOLDS, RATES, WIN_START, WIN_END
    )
    assert doc["simulation"]["delete_marker_orphan_count"] == ref["simulation"]["delete_marker_orphan_count"]


def test_tce6388_debug_tag_expires_noncurrent_quickly():
    """debug-short rule expires noncurrent drafts/tmp v1 while delete marker is current."""
    run_pipeline()
    doc = json.loads(STAGING.read_text(encoding="utf-8"))
    expired = {(e["key"], e["version_id"]) for e in doc["simulation"]["expired_versions"]}
    assert ("drafts/tmp.txt", "d1") in expired


def test_tce6388_export_monthly_cost_report_matches_reference():
    """Export subcommand monthly cost report must match reference_pipeline math."""
    run_pipeline()
    got = json.loads(REPORT.read_text(encoding="utf-8"))
    _, ref_report = reference_pipeline(
        inventory_file(), "finops-ledger", rules_file(), HOLDS, RATES, WIN_START, WIN_END
    )
    assert got["total_usd"] == ref_report["total_usd"]
    assert got["report_digest"] == ref_report["report_digest"]


def test_tce6388_cost_report_matches_oracle_total():
    """Monthly cost report total_usd must match reference_pipeline math."""
    test_tce6388_export_monthly_cost_report_matches_reference()


def test_tce6388_cost_report_sorted_storage_classes():
    """by_storage_class keys must be sorted lexicographically in JSON output."""
    run_pipeline()
    raw = REPORT.read_text(encoding="utf-8")
    keys = list(json.loads(raw)["by_storage_class"].keys())
    assert keys == sorted(keys)


def test_tce6388_multipart_pending_usd_positive():
    """Incomplete MPU uploads/ chunky.bin contribute multipart_pending_usd."""
    run_pipeline()
    got = json.loads(REPORT.read_text(encoding="utf-8"))
    assert float(got["multipart_pending_usd"]) > 0


def test_tce6388_cost_report_refuses_without_simulation():
    """cost-report exits non-zero when simulation block missing."""
    run_ingest()
    proc = run_cost()
    assert proc.returncode != 0


def test_tce6388_tb3_hidden_prefix_legal_hold_suppression():
    """TB3 holds file suppresses legal/prefix/ keys from transitions."""
    os.environ["TB3_INVENTORY_FILE"] = str(HIDDEN / "inventory" / "tb3.jsonl")
    os.environ["TB3_HOLDS_FILE"] = str(HIDDEN / "holds" / "prefix-holds.json")
    run_pipeline()
    doc = json.loads(STAGING.read_text(encoding="utf-8"))
    assert "legal/prefix/secret.dat" in doc["simulation"]["suppressed_keys"]


def test_tce6388_tb3_high_priority_rule_wins():
    """TB3 rules with priority 500 beat priority 200 for matching access logs."""
    os.environ["TB3_RULES_FILE"] = str(HIDDEN / "rules" / "high-priority-ia.json")
    run_pipeline()
    doc = json.loads(STAGING.read_text(encoding="utf-8"))
    ref_rules = HIDDEN / "rules" / "high-priority-ia.json"
    ref_staging, _ = reference_pipeline(
        INV, "finops-ledger", ref_rules, HOLDS, RATES, WIN_START, WIN_END
    )
    got_cls = {
        t["storage_class"]
        for t in doc["simulation"]["transitions_applied"]
        if t["key"] == "logs/2024/access-01.json"
    }
    exp_cls = {
        t["storage_class"]
        for t in ref_staging["simulation"]["transitions_applied"]
        if t["key"] == "logs/2024/access-01.json"
    }
    assert got_cls == exp_cls


def test_tce6388_simulation_digest_stable_rerun():
    """Re-running simulate on unchanged staging yields identical simulation_digest."""
    run_pipeline()
    d1 = json.loads(STAGING.read_text(encoding="utf-8"))["simulation"]["simulation_digest"]
    assert run_simulate().returncode == 0
    d2 = json.loads(STAGING.read_text(encoding="utf-8"))["simulation"]["simulation_digest"]
    assert d1 == d2


def test_tce6388_ingest_duplicate_version_last_line_wins():
    """Duplicate version_id lines: last inventory line wins per docs."""
    dup = APP / "state" / "dup.jsonl"
    lines = [
        json.dumps(
            {
                "bucket": "b",
                "key": "solo",
                "version_id": "x",
                "is_delete_marker": False,
                "size_bytes": 10,
                "storage_class": "STANDARD",
                "last_modified": "2024-01-01T00:00:00Z",
                "tags": {},
                "legal_hold": False,
                "retention_mode": None,
                "retention_until": None,
                "multipart_id": None,
                "multipart_complete": True,
            }
        ),
        json.dumps(
            {
                "bucket": "b",
                "key": "solo",
                "version_id": "x",
                "is_delete_marker": False,
                "size_bytes": 99,
                "storage_class": "STANDARD",
                "last_modified": "2024-02-01T00:00:00Z",
                "tags": {},
                "legal_hold": False,
                "retention_mode": None,
                "retention_until": None,
                "multipart_id": None,
                "multipart_complete": True,
            }
        ),
    ]
    dup.write_text("\n".join(lines) + "\n", encoding="utf-8")
    out = APP / "state" / "dup.stage.json"
    proc = _run(
        [str(CLI), "ingest", "--inventory", str(dup), "--bucket", "b", "--staging", str(out)]
    )
    assert proc.returncode == 0
    obj = json.loads(out.read_text(encoding="utf-8"))["objects"]
    assert len(obj) == 1
    assert obj[0]["size_bytes"] == 99


def test_tce6388_suppressed_count_in_cost_report():
    """Cost report suppressed_by_legal_hold_count matches simulation suppressed_keys length."""
    run_pipeline()
    staging = json.loads(STAGING.read_text(encoding="utf-8"))
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["suppressed_by_legal_hold_count"] == len(staging["simulation"]["suppressed_keys"])


def test_tce6388_noncurrent_access_v1_expires_under_access_rule():
    """Noncurrent access log v1 expires under 30-day noncurrent_expiration."""
    run_pipeline()
    doc = json.loads(STAGING.read_text(encoding="utf-8"))
    expired = {(e["key"], e["version_id"]) for e in doc["simulation"]["expired_versions"]}
    assert ("logs/2024/access-01.json", "v1") in expired


def test_tce6388_staging_objects_have_current_version_flags():
    """After simulate, every object row includes current_version boolean."""
    run_pipeline()
    for row in json.loads(STAGING.read_text(encoding="utf-8"))["objects"]:
        assert "current_version" in row


def test_tce6388_decoy_not_sourced_by_simulator():
    """Decoy storage_class_sorter is not sourced by lifecycle_simulator."""
    sim = APP / "lib" / "zq7" / "m06.sh"
    text = sim.read_text(encoding="utf-8")
    assert "storage_class_sorter" not in text
