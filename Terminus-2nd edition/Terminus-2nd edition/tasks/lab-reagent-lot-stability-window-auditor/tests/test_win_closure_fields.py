"""Closure export field and summary tests."""

from __future__ import annotations

import json
from pathlib import Path

from reagentwin_validate import reference_closure
from win_session_cli import CLI_BIN, SESSION_POOL, invoke, run_closure_pipeline, wipe

APP = Path("/app")
FIXTURE_DIR = APP / "fixtures" / "lab_sessions"


def test_closure_rows_carry_cert_digest() -> None:
    """stability-closure-atlas.md requires cert_digest on every closure row."""
    wipe()
    sid, bundle = SESSION_POOL[0], "dual-lot-basic"
    out = run_closure_pipeline(sid, bundle)
    body = json.loads(out.read_text(encoding="utf-8"))
    assert all(r["cert_digest"] for r in body["rows"])


def test_summary_quarantined_lte_total() -> None:
    """Summary quarantined count cannot exceed total_lots in closure report."""
    wipe()
    sid, bundle = SESSION_POOL[1], "excursion-boundary"
    out = run_closure_pipeline(sid, bundle)
    s = json.loads(out.read_text(encoding="utf-8"))["summary"]
    assert s["quarantined"] <= s["total_lots"]


def test_extended_expiry_iso_format() -> None:
    """extended_expiry must remain ISO YYYY-MM-DD in closure rows."""
    wipe()
    sid, bundle = SESSION_POOL[2], "cumulative-extension"
    out = run_closure_pipeline(sid, bundle)
    row = json.loads(out.read_text(encoding="utf-8"))["rows"][0]
    assert len(row["extended_expiry"]) == 10


def test_severity_nonnegative() -> None:
    """Severity scores published in closure rows must be non-negative."""
    wipe()
    sid, bundle = SESSION_POOL[0], "severity-ladder"
    out = run_closure_pipeline(sid, bundle)
    rows = json.loads(out.read_text(encoding="utf-8"))["rows"]
    assert all(r["severity"] >= 0 for r in rows)


def test_excursion_events_count() -> None:
    """summary.excursion_events must match independent reference for severity-ladder bundle."""
    wipe()
    sid, bundle = SESSION_POOL[0], "severity-ladder"
    out = run_closure_pipeline(sid, bundle)
    body = json.loads(out.read_text(encoding="utf-8"))
    exp = reference_closure(sid, bundle, FIXTURE_DIR / f"{bundle}.json")
    assert body["summary"]["excursion_events"] == exp["summary"]["excursion_events"]


def test_publish_closure_custom_output_path() -> None:
    """publish-closure --output must write closure JSON to the caller-provided path."""
    wipe()
    sid, bundle = SESSION_POOL[0], "dual-lot-basic"
    invoke([str(CLI_BIN), "correlate", "--session", sid, "--bundle", bundle])
    custom = APP / "output" / "custom-closure.json"
    proc = invoke(
        [str(CLI_BIN), "publish-closure", "--session", sid, "--output", str(custom)]
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert custom.exists()
    assert json.loads(custom.read_text(encoding="utf-8"))["bundle"] == bundle
