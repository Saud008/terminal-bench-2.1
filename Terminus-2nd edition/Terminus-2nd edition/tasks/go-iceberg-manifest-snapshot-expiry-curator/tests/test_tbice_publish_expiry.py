"""Publish-expiry plan and orphan ledger export parity."""

from __future__ import annotations

from expiry_curator_ctl import (
    CTL_BUNDLE,
    CTL_ORPHAN,
    CTL_PLAN,
    read_json,
    read_jsonl,
    reset_curator_workspace,
    run_curator_chain,
)
from lakehouse_expiry_ref import reference_expiry_plan as reference_expiry_plan_output
from lakehouse_expiry_ref import reference_orphans as reference_orphan_ledger_rows


def test_tbice30_clean_lineage_expired_snapshot_ids() -> None:
    """publish-expiry expired_snapshot_ids match lakehouse_expiry_ref for clean-lineage."""
    reset_curator_workspace()
    run_curator_chain("clean-lineage")
    body = read_json(CTL_PLAN)
    ref = reference_expiry_plan_output("clean-lineage", CTL_BUNDLE)
    assert body["expired_snapshot_ids"] == ref["expired_snapshot_ids"]


def test_tbice31_branch_protect_protected_count() -> None:
    """branch-protect protected_count matches refmath protected closure size."""
    reset_curator_workspace()
    run_curator_chain("branch-protect")
    body = read_json(CTL_PLAN)
    ref = reference_expiry_plan_output("branch-protect", CTL_BUNDLE)
    assert body["protected_count"] == ref["protected_count"]


def test_tbice32_delete_retain_plan_digest() -> None:
    """delete-retain plan_digest sealed with scenario in digest payload."""
    reset_curator_workspace()
    run_curator_chain("delete-retain")
    body = read_json(CTL_PLAN)
    ref = reference_expiry_plan_output("delete-retain", CTL_BUNDLE)
    assert body["plan_digest"] == ref["plan_digest"]


def test_tbice33_manifest_nested_orphan_rows() -> None:
    """manifest-nested orphan ledger lists referenced minus live data files."""
    reset_curator_workspace()
    run_curator_chain("manifest-nested")
    orphans = read_jsonl(CTL_ORPHAN)
    ref = reference_orphan_ledger_rows("manifest-nested", CTL_BUNDLE)
    assert orphans == ref


def test_tbice34_orphan_trap_skips_deleted_status() -> None:
    """orphan-trap ledger excludes deleted manifest rows from orphan accounting."""
    reset_curator_workspace()
    run_curator_chain("orphan-trap")
    orphans = read_jsonl(CTL_ORPHAN)
    ref = reference_orphan_ledger_rows("orphan-trap", CTL_BUNDLE)
    assert orphans == ref


def test_tbice35_idempotent_publish_plan_digest_stable() -> None:
    """repeated publish-expiry on stable-republish keeps identical plan_digest bytes."""
    reset_curator_workspace()
    run_curator_chain("stable-republish")
    first = read_json(CTL_PLAN)
    run_curator_chain("stable-republish")
    second = read_json(CTL_PLAN)
    assert first["plan_digest"] == second["plan_digest"]
