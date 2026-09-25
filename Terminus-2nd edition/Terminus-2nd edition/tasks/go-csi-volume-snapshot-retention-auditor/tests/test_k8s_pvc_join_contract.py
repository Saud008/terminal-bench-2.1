"""PVC join and dangling snapshot contract probes."""

from __future__ import annotations

import json

from csi_audit_runner import (
    AUDIT_BIN,
    FINDINGS_JSON,
    FIXTURE_ROOT,
    FLEET_GRAPH_JSON,
    REVISION_JSON,
    SCENARIO_CLEAN,
    SCENARIO_DANGLING,
    SCENARIO_POLICY,
    SCENARIO_PVC,
    invoke_audit,
    run_full_audit,
    wipe_audit_state,
)
from k8s_volume_refmath import (
    dangling_rows,
    join_map,
    load_cluster,
    reference_fleet_graph,
    retention_days,
    snapshot_pvc,
)

PATH_AUDIT_PASS_COUNTER = "/app/state/audit-pass-counter.json"
PATH_SCORING_FINDINGS = "/app/work/scoring-findings.json"
PATH_K8S_FLEET_GRAPH = "/app/state/k8s-fleet-graph.json"


def test_k8s_pvc_join_chain_resolves_claim() -> None:
    """PVC join contract binds VolumeSnapshot source_pvc to namespace/name PVC records."""
    cluster = load_cluster(FIXTURE_ROOT, SCENARIO_PVC)
    snap = next(s for s in cluster["snapshots"] if s["name"] == "snap-chain")
    assert snapshot_pvc(cluster, snap) is not None


def test_k8s_dangling_snapshot_missing_claim() -> None:
    """Snapshots referencing absent PVC keys are unresolved for retention class lookup."""
    cluster = load_cluster(FIXTURE_ROOT, SCENARIO_DANGLING)
    orphan = next(s for s in cluster["snapshots"] if s["name"] == "snap-orphan")
    assert snapshot_pvc(cluster, orphan) is None


def test_k8s_join_map_keys_namespace_slash_name() -> None:
    """Join map keys use namespace/name slash form from pvc-join-contract."""
    cluster = load_cluster(FIXTURE_ROOT, SCENARIO_CLEAN)
    jm = join_map(cluster)
    pvc = cluster["pvcs"][0]
    assert f"{pvc['namespace']}/{pvc['name']}" in jm


def test_k8s_dangling_fixture_orphan_uid() -> None:
    """Dangling fixture lists orphan VolumeSnapshot UID when source PVC is missing."""
    cluster = load_cluster(FIXTURE_ROOT, SCENARIO_DANGLING)
    rows = dangling_rows(cluster)
    assert any(r["source_pvc"] == "missing-pvc" for r in rows)


def test_k8s_ingest_class_override_fleet_graph_digest() -> None:
    """import-graph writes /app/state/k8s-fleet-graph.json fleet_graph_digest for class-override."""
    wipe_audit_state()
    proc = invoke_audit(
        [AUDIT_BIN, "import-graph", "--scenario", "class-override", "--fixture-dir", str(FIXTURE_ROOT)]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert str(FLEET_GRAPH_JSON) == PATH_K8S_FLEET_GRAPH
    body = json.loads(FLEET_GRAPH_JSON.read_text(encoding="utf-8"))
    ref = reference_fleet_graph("class-override", FIXTURE_ROOT)
    assert body["fleet_graph_digest"] == ref["fleet_graph_digest"]


def test_k8s_analyze_pass_bumps_revision_counter() -> None:
    """score-retention advances audit_pass_seq in /app/state/audit-pass-counter.json."""
    wipe_audit_state()
    run_full_audit(SCENARIO_CLEAN)
    assert str(REVISION_JSON) == PATH_AUDIT_PASS_COUNTER
    gen = json.loads(REVISION_JSON.read_text(encoding="utf-8"))
    assert gen["audit_pass_seq"] >= 1


def test_k8s_analyze_pass_emits_findings_json() -> None:
    """score-retention writes scoring findings to /app/work/scoring-findings.json."""
    wipe_audit_state()
    run_full_audit(SCENARIO_POLICY)
    assert str(FINDINGS_JSON) == PATH_SCORING_FINDINGS
    assert FINDINGS_JSON.is_file()


def test_k8s_storage_class_retention_days_present() -> None:
    """class-override fixture includes storage class retention_days for class-retention-contract."""
    cluster = load_cluster(FIXTURE_ROOT, "class-override")
    assert any(int(sc["retention_days"]) == 7 for sc in cluster["storage_classes"])


def test_k8s_pvc_namespace_name_collision_binds_own_namespace() -> None:
    """Same PVC name in two namespaces must join by namespace/name, not name alone."""
    cluster = load_cluster(FIXTURE_ROOT, SCENARIO_PVC)
    names = [pvc["name"] for pvc in cluster["pvcs"]]
    assert len(names) != len(set(names)), "fixture must include a cross-namespace name collision"
    snap = next(s for s in cluster["snapshots"] if s["name"] == "snap-a")
    pvc = snapshot_pvc(cluster, snap)
    assert pvc is not None
    assert pvc["namespace"] == snap["namespace"]
    assert pvc["storage_class_name"] == "sc-fast"
    jm = join_map(cluster)
    assert f"{snap['namespace']}/{snap['source_pvc']}" in jm
    other = next(p for p in cluster["pvcs"] if p["name"] == snap["source_pvc"] and p["namespace"] != snap["namespace"])
    assert other["storage_class_name"] == "sc-slow"
    assert retention_days(cluster, snap) == 7


def test_k8s_default_retention_env_override(monkeypatch) -> None:
    """TB3_CLUSTER_DEFAULT_RETENTION_DAYS overrides cluster default when policy and class do not apply."""
    cluster = load_cluster(FIXTURE_ROOT, SCENARIO_CLEAN)
    cluster["backup_policies"] = []
    for sc in cluster["storage_classes"]:
        sc["retention_days"] = 0
    snap = cluster["snapshots"][0]
    monkeypatch.delenv("TB3_CLUSTER_DEFAULT_RETENTION_DAYS", raising=False)
    assert retention_days(cluster, snap) == int(cluster["default_retention_days"])
    monkeypatch.setenv("TB3_CLUSTER_DEFAULT_RETENTION_DAYS", "5")
    assert retention_days(cluster, snap) == 5
