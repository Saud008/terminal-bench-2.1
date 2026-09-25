"""Catalog capture contract — staging digest and manifest materialization."""

from __future__ import annotations

import json

from expiry_curator_ctl import (
    CTL_BIN,
    CTL_BUNDLE,
    CTL_CURSOR,
    catalog_for,
    invoke_iceexpctl,
    reset_curator_workspace,
)
from lakehouse_expiry_ref import load_table
from lakehouse_expiry_ref import (
    reference_cursor_snapshot as reference_cursor_snapshot_snapshot,
)


def test_tbice10_staging_engine_iceexpctl() -> None:
    """capture-catalog tags cursor engine field as iceexpctl."""
    reset_curator_workspace()
    scenario = "branch-protect"
    invoke_iceexpctl(
        [
            CTL_BIN,
            "capture-catalog",
            "--catalog",
            catalog_for(scenario),
            "--scenario",
            scenario,
            "--fixture-dir",
            str(CTL_BUNDLE),
        ]
    )
    body = json.loads(CTL_CURSOR.read_text(encoding="utf-8"))
    assert body["engine"] == "iceexpctl"


def test_tbice11_snapshot_row_count_matches_fixture() -> None:
    """cursor snapshot list length equals tables/SCENARIO/table.json snapshots array."""
    reset_curator_workspace()
    scenario = "branch-protect"
    invoke_iceexpctl(
        [
            CTL_BIN,
            "capture-catalog",
            "--catalog",
            catalog_for(scenario),
            "--scenario",
            scenario,
            "--fixture-dir",
            str(CTL_BUNDLE),
        ]
    )
    body = json.loads(CTL_CURSOR.read_text(encoding="utf-8"))
    table, _ = load_table(CTL_BUNDLE, scenario)
    assert len(body["table"]["snapshots"]) == len(table["snapshots"])


def test_tbice12_branch_protect_cursor_seal() -> None:
    """branch-protect cursor_seal matches lakehouse_expiry_ref normalized bytes."""
    reset_curator_workspace()
    scenario = "branch-protect"
    invoke_iceexpctl(
        [
            CTL_BIN,
            "capture-catalog",
            "--catalog",
            catalog_for(scenario),
            "--scenario",
            scenario,
            "--fixture-dir",
            str(CTL_BUNDLE),
        ]
    )
    body = json.loads(CTL_CURSOR.read_text(encoding="utf-8"))
    ref = reference_cursor_snapshot_snapshot(scenario, CTL_BUNDLE)
    assert body["cursor_seal"] == ref["cursor_seal"]


def test_tbice13_delete_retain_cursor_seal() -> None:
    """delete-retain scenario digest uses numeric manifest key order."""
    reset_curator_workspace()
    scenario = "delete-retain"
    invoke_iceexpctl(
        [
            CTL_BIN,
            "capture-catalog",
            "--catalog",
            catalog_for(scenario),
            "--scenario",
            scenario,
            "--fixture-dir",
            str(CTL_BUNDLE),
        ]
    )
    body = json.loads(CTL_CURSOR.read_text(encoding="utf-8"))
    ref = reference_cursor_snapshot_snapshot(scenario, CTL_BUNDLE)
    assert body["cursor_seal"] == ref["cursor_seal"]


def test_tbice14_meta_order_manifest_shard_present() -> None:
    """meta-order scenario loads meta_10.json manifest shard after numeric sort."""
    reset_curator_workspace()
    scenario = "meta-order"
    invoke_iceexpctl(
        [
            CTL_BIN,
            "capture-catalog",
            "--catalog",
            catalog_for(scenario),
            "--scenario",
            scenario,
            "--fixture-dir",
            str(CTL_BUNDLE),
        ]
    )
    body = json.loads(CTL_CURSOR.read_text(encoding="utf-8"))
    assert "meta_10.json" in body["manifests"]


def test_tbice15_manifest_nested_has_nested_pointer() -> None:
    """manifest-nested fixture includes nested_manifest entries in staging manifests map."""
    reset_curator_workspace()
    scenario = "manifest-nested"
    invoke_iceexpctl(
        [
            CTL_BIN,
            "capture-catalog",
            "--catalog",
            catalog_for(scenario),
            "--scenario",
            scenario,
            "--fixture-dir",
            str(CTL_BUNDLE),
        ]
    )
    body = json.loads(CTL_CURSOR.read_text(encoding="utf-8"))
    found = False
    for rows in body["manifests"].values():
        for row in rows:
            if row.get("nested_manifest"):
                found = True
    assert found


def test_tbice16_orphan_trap_catalog_capture_ok() -> None:
    """orphan-trap capture-catalog exits zero for lake_orphan-trap catalog name."""
    reset_curator_workspace()
    scenario = "orphan-trap"
    proc = invoke_iceexpctl(
        [
            CTL_BIN,
            "capture-catalog",
            "--catalog",
            catalog_for(scenario),
            "--scenario",
            scenario,
            "--fixture-dir",
            str(CTL_BUNDLE),
        ]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout


def test_tbice17_idempotent_export_location_prefix() -> None:
    """stable-republish table metadata location uses s3 scheme prefix."""
    table, _ = load_table(CTL_BUNDLE, "stable-republish")
    assert table["location"].startswith("s3://")
