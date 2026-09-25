"""TB3 overlay traps — hidden fixture directory and retention env."""

from __future__ import annotations

import os

from expiry_curator_ctl import (
    CTL_BIN,
    CTL_OVERLAY,
    CTL_PLAN,
    catalog_for,
    invoke_iceexpctl,
    read_json,
    reset_curator_workspace,
)
from lakehouse_expiry_ref import delete_retention_hours
from lakehouse_expiry_ref import reference_expiry_plan as reference_expiry_plan_output


def test_tbice40_overlay_tag_branch_trap_expired_ids() -> None:
    """hidden tag-branch-trap fixture expired ids match refmath under TB3_FIXTURE_DIR."""
    reset_curator_workspace()
    scenario = "tag-branch-trap"
    env = {"TB3_FIXTURE_DIR": str(CTL_OVERLAY)}
    catalog = catalog_for(scenario)
    for step in (
        [CTL_BIN, "capture-catalog", "--catalog", catalog, "--scenario", scenario, "--fixture-dir", str(CTL_OVERLAY)],
        [CTL_BIN, "audit-retention", "--catalog", catalog, "--scenario", scenario],
        [CTL_BIN, "publish-expiry", "--catalog", catalog, "--scenario", scenario],
    ):
        proc = invoke_iceexpctl(step, env=env)
        assert proc.returncode == 0, proc.stderr + proc.stdout
    body = read_json(CTL_PLAN)
    ref = reference_expiry_plan_output(scenario, CTL_OVERLAY)
    assert body["expired_snapshot_ids"] == ref["expired_snapshot_ids"]


def test_tbice41_overlay_delete_boundary_retention_hours() -> None:
    """TB3_DELETE_RETENTION_HOURS shifts delete floor for delete-boundary-trap overlay."""
    reset_curator_workspace()
    scenario = "delete-boundary-trap"
    env = {"TB3_FIXTURE_DIR": str(CTL_OVERLAY), "TB3_DELETE_RETENTION_HOURS": "72"}
    catalog = catalog_for(scenario)
    invoke_iceexpctl(
        [CTL_BIN, "capture-catalog", "--catalog", catalog, "--scenario", scenario, "--fixture-dir", str(CTL_OVERLAY)],
        env=env,
    )
    table = read_json(CTL_OVERLAY / "tables/delete-boundary-trap/table.json")
    prev = os.environ.get("TB3_DELETE_RETENTION_HOURS")
    os.environ["TB3_DELETE_RETENTION_HOURS"] = "72"
    try:
        assert delete_retention_hours(table) == 72
        ref = reference_expiry_plan_output(scenario, CTL_OVERLAY)
    finally:
        if prev is None:
            os.environ.pop("TB3_DELETE_RETENTION_HOURS", None)
        else:
            os.environ["TB3_DELETE_RETENTION_HOURS"] = prev
    invoke_iceexpctl([CTL_BIN, "audit-retention", "--catalog", catalog, "--scenario", scenario], env=env)
    invoke_iceexpctl([CTL_BIN, "publish-expiry", "--catalog", catalog, "--scenario", scenario], env=env)
    body = read_json(CTL_PLAN)
    assert body["plan_digest"] == ref["plan_digest"]
