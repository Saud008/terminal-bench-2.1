"""Temporal workflow history compaction inspector — wfhistctl contract suite."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from histctl_independent import (
    golden_inspection as reference_inspection,
    golden_seal as reference_seal,
    golden_staging as reference_staging,
    rank_events as sort_events,
)
from histctl_workspace import (
    AUDIT_JSON,
    BUNDLE_ROOT,
    CATALOG_SLUGS,
    HIDDEN_ROOT,
    RISK_JSONL,
    SEAL_JSON,
    SQLITE_DB,
    STAGING_JSON,
    WFHIST_BIN,
    WFHIST_NS,
    load_jsonl,
    reset_histctl_workspace,
    run_histctl,
    run_histctl_pipeline,
    sqlite_activity_rows,
)

CATALOG = json.loads((Path(__file__).parent / "histctl_catalog.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def _histctl_clean_room():
    reset_histctl_workspace()
    yield
    reset_histctl_workspace()


def test_histctl_contract_paths_materialize_after_emit():
    """emit-inspect writes /app/state/wf-history-staging.json, wf-compaction-seal.json, inspection.db, replay-risk-report.jsonl."""
    run_histctl_pipeline("clean-run")
    assert STAGING_JSON.is_file()
    assert SEAL_JSON.is_file()
    assert str(STAGING_JSON) == "/app/state/wf-history-staging.json"
    assert str(SEAL_JSON) == "/app/state/wf-compaction-seal.json"
    assert SQLITE_DB.is_file()
    assert str(SQLITE_DB) == "/app/output/inspection.db"
    assert RISK_JSONL.is_file()
    assert str(RISK_JSONL) == "/app/output/replay-risk-report.jsonl"


def test_histctl_ingest_staging_digest_golden():
    """ingest-history staging_digest matches golden_staging including max_run_generation."""
    proc = run_histctl(
        [WFHIST_BIN, "ingest-history", "--namespace", WFHIST_NS, "--scenario", "clean-run", "--fixture-dir", str(BUNDLE_ROOT)]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    body = json.loads(STAGING_JSON.read_text(encoding="utf-8"))
    ref = reference_staging(WFHIST_NS, "clean-run", BUNDLE_ROOT)
    assert body["staging_digest"] == ref["staging_digest"]


def test_histctl_emit_blocked_without_compaction_seal():
    """emit-inspect fails when /app/state/wf-compaction-seal.json compaction_seal is zero."""
    assert run_histctl(
        [WFHIST_BIN, "ingest-history", "--namespace", WFHIST_NS, "--scenario", "clean-run", "--fixture-dir", str(BUNDLE_ROOT)]
    ).returncode == 0
    blocked = run_histctl([WFHIST_BIN, "emit-inspect", "--namespace", WFHIST_NS, "--scenario", "clean-run"])
    assert blocked.returncode != 0


def test_histctl_compact_summary_positive_seal_and_audit():
    """compact-summary writes /app/work/wf-compaction-audit.json and positive seal epoch."""
    run_histctl_pipeline("clean-run")
    assert AUDIT_JSON.is_file()
    seal = json.loads(SEAL_JSON.read_text(encoding="utf-8"))
    assert seal["compaction_seal"] > 0
    audit = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))
    assert "finding_count" in audit


def test_histctl_activity_retry_retry_chain_risk():
    """activity-retry emits RETRY_CHAIN with max_attempt two on replay-risk-report.jsonl."""
    run_histctl_pipeline("activity-retry")
    risks = load_jsonl(RISK_JSONL)
    assert risks and risks[0]["max_attempt"] == 2
    assert risks[0]["risk_code"] == "RETRY_CHAIN"


def test_histctl_timer_cancel_clears_pending_lane():
    """timer-cancel leaves pending_timers zero in replay risk rollup."""
    run_histctl_pipeline("timer-cancel")
    risks = load_jsonl(RISK_JSONL)
    assert risks == [] or all(r["pending_timers"] == 0 for r in risks)


def test_histctl_timer_fire_drops_pending_timer():
    """timer-fire clears pending timer after TimerFired."""
    run_histctl_pipeline("timer-fire")
    risks = load_jsonl(RISK_JSONL)
    assert risks == [] or all(r["pending_timers"] == 0 for r in risks)


def test_histctl_continue_as_new_resets_rollup_attempt():
    """continue-as-new generation one rollup attempt resets to one in inspection.db."""
    run_histctl_pipeline("continue-as-new")
    rows = sqlite_activity_rows()
    gen1 = [r for r in rows if r["run_generation"] == 1 and r["activity_id"] == "rollup"]
    assert gen1 and gen1[0]["attempt"] == 1


def test_histctl_chronorder_tie_breaks_on_event_id():
    """event-order-tie ranks equal timestamp_ms by event_id then seq in staging events."""
    assert run_histctl(
        [WFHIST_BIN, "ingest-history", "--namespace", WFHIST_NS, "--scenario", "event-order-tie", "--fixture-dir", str(BUNDLE_ROOT)]
    ).returncode == 0
    body = json.loads(STAGING_JSON.read_text(encoding="utf-8"))
    raw = [
        json.loads(line)
        for line in (BUNDLE_ROOT / "workflow-histories/event-order-tie/events.jsonl").read_text().splitlines()
        if line.strip()
    ]
    assert [e["event_id"] for e in body["events"]] == [e["event_id"] for e in sort_events(raw)]


def test_histctl_mixed_compaction_seal_matches_golden():
    """mixed-compaction seal equals golden_seal CAN boundary count."""
    run_histctl_pipeline("mixed-compaction")
    events = json.loads(STAGING_JSON.read_text(encoding="utf-8"))["events"]
    seal = json.loads(SEAL_JSON.read_text(encoding="utf-8"))
    assert seal["compaction_seal"] == reference_seal(events)


def test_histctl_sqlite_rows_match_golden_inspection():
    """inspection.db rows sorted by run_generation activity_id attempt match golden_inspection."""
    run_histctl_pipeline("activity-retry")
    events = json.loads(STAGING_JSON.read_text(encoding="utf-8"))["events"]
    ref_acts, _ = reference_inspection(events)
    assert sqlite_activity_rows() == ref_acts


def test_histctl_replay_risk_jsonl_matches_golden():
    """replay-risk-report.jsonl lines match golden_inspection risk rows."""
    run_histctl_pipeline("activity-retry")
    events = json.loads(STAGING_JSON.read_text(encoding="utf-8"))["events"]
    _, ref_risks = reference_inspection(events)
    assert load_jsonl(RISK_JSONL) == ref_risks


def test_histctl_catalog_bundled_slugs_ingest_ready():
    """Bundled scenario slugs from the catalog remain available for ingest."""
    for slug in CATALOG["bundled"]:
        assert slug in CATALOG_SLUGS


def test_histctl_hidden_can_poison_seal_at_least_two():
    """Hidden /opt/verifier-fixtures can-poison fixture increments compaction seal >= 2."""
    run_histctl_pipeline("hidden-can-poison", HIDDEN_ROOT)
    seal = json.loads(SEAL_JSON.read_text(encoding="utf-8"))
    assert seal["compaction_seal"] >= 2


def test_histctl_hidden_timer_fire_clears_pending():
    """Hidden /opt/verifier-fixtures timer-grace: TimerFired clears pending_timers."""
    run_histctl_pipeline("hidden-timer-grace", HIDDEN_ROOT)
    risks = load_jsonl(RISK_JSONL)
    assert risks == [] or all(r["pending_timers"] == 0 for r in risks)


def test_histctl_hidden_fixture_dir_ingest_subprocess():
    """ingest-history --fixture-dir reads /opt/verifier-fixtures/wfhistctl roots."""
    proc = subprocess.run(
        [
            WFHIST_BIN,
            "ingest-history",
            "--namespace",
            WFHIST_NS,
            "--scenario",
            "hidden-can-poison",
            "--fixture-dir",
            str(HIDDEN_ROOT),
        ],
        cwd="/app",
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout


def test_histctl_idempotent_export_bytes_stable():
    """second full pipeline run yields byte-identical inspection.db and replay-risk-report.jsonl."""
    run_histctl_pipeline("clean-run")
    db_blob = SQLITE_DB.read_bytes()
    risk_blob = RISK_JSONL.read_bytes()
    reset_histctl_workspace()
    run_histctl_pipeline("clean-run")
    assert SQLITE_DB.read_bytes() == db_blob
    assert RISK_JSONL.read_bytes() == risk_blob


def test_histctl_staging_records_namespace_and_event_count():
    """ingest-history stores namespace slug and event_count in wf-history-staging.json."""
    proc = run_histctl(
        [WFHIST_BIN, "ingest-history", "--namespace", WFHIST_NS, "--scenario", "clean-run", "--fixture-dir", str(BUNDLE_ROOT)]
    )
    assert proc.returncode == 0
    body = json.loads(STAGING_JSON.read_text(encoding="utf-8"))
    assert body["namespace"] == WFHIST_NS
    assert body["event_count"] == 3


def test_histctl_hidden_can_poison_listed_in_catalog():
    """Hidden catalog entry hidden-can-poison is declared for /opt/verifier-fixtures runs."""
    assert "hidden-can-poison" in CATALOG["hidden"]


def test_histctl_audit_can_boundaries_field_present():
    """compact-summary audit includes can_boundaries for mixed-compaction."""
    run_histctl_pipeline("mixed-compaction")
    report = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))
    assert report.get("can_boundaries", 0) >= 1


@pytest.mark.parametrize("slug", ["clean-run", "timer-fire", "continue-as-new"])
def test_histctl_param_sqlite_matches_golden(slug: str):
    """parametrized bundled scenarios match golden_inspection SQLite projection."""
    run_histctl_pipeline(slug)
    events = json.loads(STAGING_JSON.read_text(encoding="utf-8"))["events"]
    ref_acts, _ = reference_inspection(events)
    assert sqlite_activity_rows() == ref_acts
