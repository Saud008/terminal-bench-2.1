"""Core reagentwin correlate and closure contract tests.

Session bundle ingest via correlate writes a correlation snapshot artifact.
Closure export via publish-closure reads the snapshot only.
"""

from __future__ import annotations

import json
from pathlib import Path

from reagentwin_validate import (
    extended_expiry as reference_extended_expiry,
    lot_cert_digest as reference_cert_digest,
    reference_closure,
)
from win_session_cli import CLI_BIN, FIXTURE_DIR, SESSION_POOL, correlation_path, invoke, run_closure_pipeline, wipe

APP = Path("/app")


def test_win_binary_installed() -> None:
    """Instruction requires reagentwin at /app/bin/reagentwin after cargo build."""
    assert CLI_BIN.is_file()


def test_correlate_emits_artifact() -> None:
    """correlate must write /app/work/stability-correlation/<session-id>.json with generation 1."""
    wipe()
    sid, bundle = SESSION_POOL[0], "dual-lot-basic"
    proc = invoke([str(CLI_BIN), "correlate", "--session", sid, "--bundle", bundle])
    assert proc.returncode == 0, proc.stderr + proc.stdout
    body = json.loads(correlation_path(sid).read_text(encoding="utf-8"))
    assert body["correlate_generation"] == 1
    assert body["session_id"] == sid
    assert body["bundle"] == bundle


def test_correlate_generation_advances_on_recorrelate() -> None:
    """correlation-artifact-schema.md requires correlate_generation to increment on each correlate."""
    wipe()
    sid = SESSION_POOL[1]
    for bundle in ("dual-lot-basic", "excursion-boundary"):
        proc = invoke([str(CLI_BIN), "correlate", "--session", sid, "--bundle", bundle])
        assert proc.returncode == 0, proc.stderr + proc.stdout
    body = json.loads(correlation_path(sid).read_text(encoding="utf-8"))
    assert body["correlate_generation"] == 2


def test_publish_closure_reads_correlation_only() -> None:
    """publish-closure must succeed after correlate writes the correlated artifact."""
    wipe()
    sid, bundle = SESSION_POOL[0], "dual-lot-basic"
    run_closure_pipeline(sid, bundle)
    assert correlation_path(sid).exists()


def test_dual_lot_basic_closure_matches_reference() -> None:
    """Closure rows, summary, and closure_digest must match independent reference math."""
    wipe()
    sid, bundle = SESSION_POOL[0], "dual-lot-basic"
    out = run_closure_pipeline(sid, bundle)
    got = json.loads(out.read_text(encoding="utf-8"))
    exp = reference_closure(sid, bundle, FIXTURE_DIR / f"{bundle}.json")
    assert got["rows"] == exp["rows"]
    assert got["summary"] == exp["summary"]
    assert got["closure_digest"] == exp["closure_digest"]


def test_provenance_digest_field_order() -> None:
    """provenance-digest-contract.md defines lot_id:as_of_date:assay_code digest field order."""
    wipe()
    sid, bundle = SESSION_POOL[0], "dual-lot-basic"
    invoke([str(CLI_BIN), "correlate", "--session", sid, "--bundle", bundle])
    snap = json.loads(correlation_path(sid).read_text(encoding="utf-8"))
    lot = snap["lots"][0]
    assert lot["cert_digest"] == reference_cert_digest(lot["lot_id"], snap["as_of_date"], lot["assay_code"])


def test_excursion_integral_inclusive_boundary() -> None:
    """chrono-excursion-integral.md treats minute_index equal to excursion_limit_minutes as qualifying."""
    wipe()
    sid, bundle = SESSION_POOL[2], "excursion-boundary"
    out = run_closure_pipeline(sid, bundle)
    rows = json.loads(out.read_text(encoding="utf-8"))["rows"]
    assert rows[0]["excursion_minutes"] == 120
    assert rows[0]["quarantine"] is True


def test_assay_coupling_case_insensitive() -> None:
    """assay-lot-coupling.md binds telemetry aliases with case-insensitive lot matching."""
    wipe()
    sid, bundle = SESSION_POOL[1], "alias-case-mix"
    out = run_closure_pipeline(sid, bundle)
    rows = json.loads(out.read_text(encoding="utf-8"))["rows"]
    assert rows[0]["excursion_minutes"] > 0


def test_calendar_extension_cumulative_days() -> None:
    """calendar-extension-policy.md adds cold_chain_days plus stability_bonus_days cumulatively."""
    wipe()
    sid, bundle = SESSION_POOL[3], "cumulative-extension"
    out = run_closure_pipeline(sid, bundle)
    row = json.loads(out.read_text(encoding="utf-8"))["rows"][0]
    lot = json.loads((FIXTURE_DIR / f"{bundle}.json").read_text(encoding="utf-8"))["lots"][0]
    expected = reference_extended_expiry(
        lot["base_expiry"], lot["cold_chain_days"], lot["stability_bonus_days"]
    )
    assert row["extended_expiry"] == expected


def test_closure_rows_ranked_by_severity() -> None:
    """stability-closure-atlas.md ranks rows by severity descending then lot_id ascending."""
    wipe()
    sid, bundle = SESSION_POOL[0], "severity-ladder"
    out = run_closure_pipeline(sid, bundle)
    rows = json.loads(out.read_text(encoding="utf-8"))["rows"]
    severities = [r["severity"] for r in rows]
    assert severities == sorted(severities, reverse=True)


def test_closure_digest_tracks_summary() -> None:
    """closure_digest must match SHA-256 over sorted-key summary counters per stability-closure-atlas.md."""
    wipe()
    sid, bundle = SESSION_POOL[0], "severity-ladder"
    out = run_closure_pipeline(sid, bundle)
    body = json.loads(out.read_text(encoding="utf-8"))
    exp = reference_closure(sid, bundle, FIXTURE_DIR / f"{bundle}.json")
    assert body["closure_digest"] == exp["closure_digest"]
