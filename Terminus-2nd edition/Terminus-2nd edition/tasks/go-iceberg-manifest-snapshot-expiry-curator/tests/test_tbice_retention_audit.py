"""Retention audit and lineage protection refmath checks."""

from __future__ import annotations

import json

from expiry_curator_ctl import (
    CTL_AUDIT_PASS,
    CTL_AUDIT_WITNESS,
    CTL_BUNDLE,
    reset_curator_workspace,
    run_curator_chain,
)
from lakehouse_expiry_ref import protected_snapshot_ids


def test_tbice20_branch_protect_closure_has_three_snapshots() -> None:
    """branch-protect protected snapshot ids include ancestors 1 2 3."""
    table = json.loads((CTL_BUNDLE / "tables/branch-protect/table.json").read_text(encoding="utf-8"))
    prot = protected_snapshot_ids(table)
    assert {1, 2, 3}.issubset(prot)


def test_tbice21_tag_pin_protects_snapshot_two() -> None:
    """tag-pin scenario keeps tag ref snapshot id inside protected closure."""
    table = json.loads((CTL_BUNDLE / "tables/tag-pin/table.json").read_text(encoding="utf-8"))
    prot = protected_snapshot_ids(table)
    assert 2 in prot


def test_tbice22_audit_pass_counter_positive() -> None:
    """audit-retention increments analyze_revision after curator chain on clean-lineage."""
    reset_curator_workspace()
    run_curator_chain("clean-lineage")
    gen = json.loads(CTL_AUDIT_PASS.read_text(encoding="utf-8"))
    assert gen["analyze_revision"] >= 1


def test_tbice23_audit_writes_witness_json() -> None:
    """audit-retention emits analyze-findings.json under /app/work for delete-retain."""
    reset_curator_workspace()
    run_curator_chain("delete-retain")
    assert CTL_AUDIT_WITNESS.is_file()


def test_tbice24_clean_lineage_tip_snapshot_five() -> None:
    """clean-lineage current_snapshot_id fixture tip is snapshot 5."""
    table = json.loads((CTL_BUNDLE / "tables/clean-lineage/table.json").read_text(encoding="utf-8"))
    assert int(table["current_snapshot_id"]) == 5
