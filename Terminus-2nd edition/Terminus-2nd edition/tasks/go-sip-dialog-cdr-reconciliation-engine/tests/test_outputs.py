"""End-to-end sipcdrctl carrier pipeline behavioral tests."""

from __future__ import annotations

import json
import subprocess

from sip_cdr_refmath import reference_carrier_sqlite
from sip_transcript_runner import (
    ARTIFACTS,
    CARRIER_TENANT,
    FIXTURE_ROOT,
    TB3_FIXTURE_DIR,
    fetch_sqlite_rows,
    invoke_sipcdr,
    reset_carrier_workspace,
    run_carrier_pipeline,
)


def test_t700598_sipcdr_invite_flow_sqlite_matches_reference() -> None:
    """Answered INVITE/BYE dialog produces SQLite rows matching reference math."""
    reset_carrier_workspace()
    run_carrier_pipeline("invite-answer-bye")
    assert ARTIFACTS["sqlite"].is_file()
    got = fetch_sqlite_rows(ARTIFACTS["sqlite"])
    ref, _ = reference_carrier_sqlite(CARRIER_TENANT, "invite-answer-bye", FIXTURE_ROOT)
    assert got == ref
    assert got[0]["disposition"] == "completed"


def test_t700598_sipcdr_forked_to_tag_keeps_one_billed_branch() -> None:
    """Forked To-tag branches bill only the answered leg per legfold-branch-contract."""
    reset_carrier_workspace()
    run_carrier_pipeline("forked-branch-join")
    got = fetch_sqlite_rows(ARTIFACTS["sqlite"])
    ref, _ = reference_carrier_sqlite(CARRIER_TENANT, "forked-branch-join", FIXTURE_ROOT)
    assert got == ref
    assert len(got) == 1


def test_t700598_sipcdr_cancel_before_answer_exports_zero_rows() -> None:
    """Early CANCEL suppresses SQLite export when no 2xx answer occurred."""
    reset_carrier_workspace()
    run_carrier_pipeline("cancel-before-200")
    got = fetch_sqlite_rows(ARTIFACTS["sqlite"])
    ref, _ = reference_carrier_sqlite(CARRIER_TENANT, "cancel-before-200", FIXTURE_ROOT)
    assert got == ref == []


def test_t700598_sipcdr_provisional_ring_no_cdr_rows() -> None:
    """180/183-only dialogs never materialize cdr.sqlite rows."""
    reset_carrier_workspace()
    run_carrier_pipeline("provisional-only")
    assert fetch_sqlite_rows(ARTIFACTS["sqlite"]) == []


def test_t700598_sipcdr_skew_shifts_peak_billing_tier() -> None:
    """clock_skew_ms moves answer timestamp into peak billing window."""
    reset_carrier_workspace()
    run_carrier_pipeline("clock-skew-window")
    got = fetch_sqlite_rows(ARTIFACTS["sqlite"])
    ref, _ = reference_carrier_sqlite(CARRIER_TENANT, "clock-skew-window", FIXTURE_ROOT)
    assert got == ref
    assert got[0]["billing_tier"] == "peak"


def test_t700598_sipcdr_retransmit_dedupe_single_row() -> None:
    """Duplicate 200 retransmits collapse to one SQLite row."""
    reset_carrier_workspace()
    run_carrier_pipeline("retransmit-storm")
    got = fetch_sqlite_rows(ARTIFACTS["sqlite"])
    ref, _ = reference_carrier_sqlite(CARRIER_TENANT, "retransmit-storm", FIXTURE_ROOT)
    assert got == ref
    assert len(got) == 1


def test_t700598_sipcdr_repeat_pipeline_stable_sqlite_bytes() -> None:
    """Second pipeline pass yields identical cdr.sqlite bytes after workspace reset."""
    reset_carrier_workspace()
    run_carrier_pipeline("cross-run-stable-bytes")
    first = ARTIFACTS["sqlite"].read_bytes()
    reset_carrier_workspace()
    run_carrier_pipeline("cross-run-stable-bytes")
    assert ARTIFACTS["sqlite"].read_bytes() == first


def test_t700598_sipcdr_export_seal_nonzero() -> None:
    """export-cdr emits cdr-publish-seal.json with populated dialog_seal."""
    reset_carrier_workspace()
    run_carrier_pipeline("invite-answer-bye")
    assert ARTIFACTS["seal"].is_file()
    seal = json.loads(ARTIFACTS["seal"].read_text(encoding="utf-8"))
    assert seal["dialog_seal"]
    assert seal["row_count"] >= 1


def test_t700598_sipcdr_rate_billing_report_written() -> None:
    """rate-billing stage writes billing-window-report.json with rated dialogs."""
    reset_carrier_workspace()
    run_carrier_pipeline("invite-answer-bye")
    report = json.loads(ARTIFACTS["billing"].read_text(encoding="utf-8"))
    assert report["rated_count"] >= 1


def test_t700598_sipcdr_staging_seal_after_compile() -> None:
    """compile-dialogs stamps dialog_seal on dialog-buffer staging artifact."""
    reset_carrier_workspace()
    run_carrier_pipeline("invite-answer-bye")
    staging = json.loads(ARTIFACTS["staging"].read_text(encoding="utf-8"))
    assert staging["dialog_seal"]


def test_t700598_sipcdr_ingest_only_creates_staging_file() -> None:
    """ingest-transcript alone materializes dialog-buffer.json under /app/state."""
    reset_carrier_workspace()
    proc = invoke_sipcdr(["ingest-transcript", "--tenant", CARRIER_TENANT, "--scenario", "invite-answer-bye"])
    assert proc.returncode == 0
    assert isinstance(proc, subprocess.CompletedProcess)
    assert ARTIFACTS["staging"].is_file()


def test_t700598_sipcdr_sqlite_rows_sorted_lexicographically() -> None:
    """cdr_rows appear in call_id then branch_key ascending order."""
    reset_carrier_workspace()
    run_carrier_pipeline("invite-answer-bye")
    keys = [(r["call_id"], r["branch_key"]) for r in fetch_sqlite_rows(ARTIFACTS["sqlite"])]
    assert keys == sorted(keys)


def test_t700598_sipcdr_duration_seconds_positive_for_completed() -> None:
    """Completed calls record positive duration_sec between answer and BYE."""
    reset_carrier_workspace()
    run_carrier_pipeline("invite-answer-bye")
    rows = fetch_sqlite_rows(ARTIFACTS["sqlite"])
    assert rows[0]["duration_sec"] > 0


def test_t700598_sipcdr_tb3_cancel_poison_matches_reference() -> None:
    """Off-catalog cancel poison requires TB3 transcript sort and precedence."""
    reset_carrier_workspace()
    run_carrier_pipeline("hidden-cancel-poison", TB3_FIXTURE_DIR)
    got = fetch_sqlite_rows(ARTIFACTS["sqlite"])
    ref, _ = reference_carrier_sqlite(CARRIER_TENANT, "hidden-cancel-poison", TB3_FIXTURE_DIR)
    assert got == ref


def test_t700598_sipcdr_tb3_billing_boundary_inclusive_end() -> None:
    """Hidden billing boundary honors inclusive billing window end minute."""
    reset_carrier_workspace()
    run_carrier_pipeline("hidden-billing-boundary", TB3_FIXTURE_DIR)
    got = fetch_sqlite_rows(ARTIFACTS["sqlite"])
    ref, _ = reference_carrier_sqlite(CARRIER_TENANT, "hidden-billing-boundary", TB3_FIXTURE_DIR)
    assert got == ref


def test_t700598_sipcdr_peak_or_offpeak_tier_on_rated_row() -> None:
    """Rated rows always carry peak or offpeak tier labels."""
    reset_carrier_workspace()
    run_carrier_pipeline("clock-skew-window")
    tier = fetch_sqlite_rows(ARTIFACTS["sqlite"])[0]["billing_tier"]
    assert tier in ("peak", "offpeak")


def test_t700598_sipcdr_fork_staging_retains_two_branches() -> None:
    """Forked scenario staging tracks at least two branch keys before cdrsqlite."""
    reset_carrier_workspace()
    run_carrier_pipeline("forked-branch-join")
    staging = json.loads(ARTIFACTS["staging"].read_text(encoding="utf-8"))
    assert len(staging.get("dialogs", {})) >= 2


def test_t700598_sipcdr_seal_row_count_matches_reference() -> None:
    """cdr-publish-seal row_count equals golden export row count."""
    reset_carrier_workspace()
    run_carrier_pipeline("invite-answer-bye")
    seal = json.loads(ARTIFACTS["seal"].read_text(encoding="utf-8"))
    _, ref_seal = reference_carrier_sqlite(CARRIER_TENANT, "invite-answer-bye", FIXTURE_ROOT)
    assert seal["row_count"] == ref_seal["row_count"]
