"""Bundled wgpatlas behavioral tests."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from wgpatlas_cli_support import WORKSPACE, run_pipeline, wipe
from wgpatlas_contract_math import reference_atlas, workspace_fingerprint, build_peers, build_overlaps


def test_wgpatlas_cli_on_path():
    """Verify wgpatlas is installed at /app/bin/wgpatlas per instruction."""
    assert Path("/app/bin/wgpatlas").is_file()
    proc = subprocess.run(["/app/bin/wgpatlas"], capture_output=True, text=True)
    assert proc.returncode != 0


def test_coastal_mesh_atlas_matches_reference():
    """Verify coastal-mesh export peers overlaps route_conflicts and audit_digest match reference math."""
    wipe()
    out = run_pipeline("coastal-mesh", "run-coastal")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_atlas(Path("/app/sites/coastal-mesh"), "run-coastal")
    assert rep["peers"] == ref["peers"]
    assert rep["overlaps"] == ref["overlaps"]
    assert rep["route_conflicts"] == ref["route_conflicts"]
    assert rep["audit_digest"] == ref["audit_digest"]


def test_workspace_snapshot_schema():
    """Verify wgpatlas-workspace.json includes run_id workspace_fingerprint and peer rows after analyze."""
    wipe()
    run_pipeline("coastal-mesh", "run-schema")
    snap = json.loads(WORKSPACE.read_text(encoding="utf-8"))
    assert snap["run_id"] == "run-schema"
    assert "workspace_fingerprint" in snap
    assert len(snap["peers"]) >= 3


def test_workspace_fingerprint_matches_reference():
    """Verify workspace_fingerprint matches independent hash from workspace-atlas-schema contract."""
    wipe()
    run_pipeline("coastal-mesh", "run-fp")
    snap = json.loads(WORKSPACE.read_text(encoding="utf-8"))
    site = Path("/app/sites/coastal-mesh")
    policy = json.loads((site / "site-policy.json").read_text(encoding="utf-8"))
    peers = build_peers(site, policy)
    overlaps = build_overlaps(peers)
    disabled = policy.get("disabled_peers", [])
    ref_fp = workspace_fingerprint("run-fp", peers, overlaps, disabled)
    assert snap["workspace_fingerprint"] == ref_fp


def test_allowed_ip_overlap_detected_coastal():
    """Verify allowed-IP overlap between peer-alpha and peer-delta per coastal-mesh catalog."""
    wipe()
    run_pipeline("coastal-mesh", "run-overlap")
    snap = json.loads(WORKSPACE.read_text(encoding="utf-8"))
    assert any(o["peer_a"] == "peer-alpha" and o["peer_b"] == "peer-delta" for o in snap["overlaps"])


def test_disabled_peer_excluded_from_export():
    """Verify disabled peer-gamma is excluded from export peers per disabled-peer-contract."""
    wipe()
    out = run_pipeline("coastal-mesh", "run-disabled")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ids = {p["peer_id"] for p in rep["peers"]}
    assert "peer-gamma" not in ids


def test_endpoint_precedence_lower_metric_wins():
    """Verify dual-uplink spoke-one endpoint 192.0.2.50:51820 when lower metric wins."""
    wipe()
    out = run_pipeline("dual-uplink", "run-ep")
    rep = json.loads(out.read_text(encoding="utf-8"))
    row = next(p for p in rep["peers"] if p["peer_id"] == "spoke-one")
    assert row["endpoint"] == "192.0.2.50:51820"


def test_dual_uplink_multi_allowed_ips_present():
    """Verify AllowedIPs parsing retains both CIDRs for spoke-one on dual-uplink site."""
    wipe()
    out = run_pipeline("dual-uplink", "run-multi")
    rep = json.loads(out.read_text(encoding="utf-8"))
    row = next(p for p in rep["peers"] if p["peer_id"] == "spoke-one")
    assert len(row["allowed_ips"]) == 2


def test_route_table_cross_interface_conflict():
    """Verify table-split emits cross_interface_table_id route conflict on shared table_id 300."""
    wipe()
    out = run_pipeline("table-split", "run-table")
    rep = json.loads(out.read_text(encoding="utf-8"))
    assert len(rep["route_conflicts"]) >= 1
    assert rep["route_conflicts"][0]["reason"] == "cross_interface_table_id"


def test_export_peers_sorted_by_public_key():
    """Verify export peers sort by public_key ascending per topology-export-contract."""
    wipe()
    out = run_pipeline("coastal-mesh", "run-sort")
    rep = json.loads(out.read_text(encoding="utf-8"))
    keys = [p["public_key"] for p in rep["peers"]]
    assert keys == sorted(keys)


def test_export_bytes_stable_on_repeat():
    """Verify repeat export to /app/output/run-stable-atlas.json is byte-identical."""
    wipe()
    run_pipeline("coastal-mesh", "run-stable")
    first = (Path("/app/output/run-stable-atlas.json")).read_bytes()
    from wgpatlas_cli_support import invoke, CLI
    invoke([str(CLI), "export", "--run-id", "run-stable", "--output", "/app/output/run-stable-atlas.json"])
    assert first == Path("/app/output/run-stable-atlas.json").read_bytes()


def test_decoy_mesh_rank_helper_absent():
    """Verify export atlas JSON does not include decoy mesh_rank_helper output."""
    wipe()
    run_pipeline("coastal-mesh", "run-decoy")
    text = Path("/app/output/run-decoy-atlas.json").read_text(encoding="utf-8")
    assert "mesh_rank_helper" not in text


def test_coastal_alpha_endpoint_from_policy():
    """Verify coastal-mesh peer-alpha endpoint 203.0.113.10:51820 from site-policy precedence."""
    wipe()
    out = run_pipeline("coastal-mesh", "run-alpha-ep")
    rep = json.loads(out.read_text(encoding="utf-8"))
    row = next(p for p in rep["peers"] if p["peer_id"] == "peer-alpha")
    assert row["endpoint"] == "203.0.113.10:51820"


def test_summary_counts_match_arrays():
    """Verify summary active overlap and conflict counts match exported array lengths."""
    wipe()
    out = run_pipeline("coastal-mesh", "run-summary")
    rep = json.loads(out.read_text(encoding="utf-8"))
    assert rep["summary"]["active_peer_count"] == len(rep["peers"])
    assert rep["summary"]["overlap_count"] == len(rep["overlaps"])
    assert rep["summary"]["conflict_count"] == len(rep["route_conflicts"])
