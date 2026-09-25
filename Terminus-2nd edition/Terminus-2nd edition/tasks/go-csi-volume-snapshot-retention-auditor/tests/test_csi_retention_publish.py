"""Retention report publish and quota accounting verification."""

from __future__ import annotations

from pathlib import Path

from csi_audit_runner import (
    AUDIT_BIN,
    DANGLING_JSONL,
    FIXTURE_ROOT,
    REPORT_JSON,
    SCENARIO_CLASS,
    SCENARIO_CLEAN,
    SCENARIO_DANGLING,
    SCENARIO_POLICY,
    SCENARIO_PVC,
    SCENARIO_QUOTA,
    SCENARIO_RETAIN,
    SCENARIO_STABLE_REPUBLISH,
    invoke_audit,
    load_json_file,
    load_jsonl_file,
    run_full_audit,
    wipe_audit_state,
)
from k8s_volume_refmath import dangling_rows, load_cluster, reference_retention_report

PATH_VOLSNAP_AUDIT_REPORT = "/app/output/volsnap-audit-report.json"
PATH_ORPHAN_SNAPSHOT_LEDGER = "/app/output/orphan-snapshot-ledger.jsonl"


def test_csi_publish_clean_retention_deletable_uids() -> None:
    """publish-audit writes volsnap-audit-report.json deletable_snapshot_uids for clean-retention."""
    wipe_audit_state()
    run_full_audit(SCENARIO_CLEAN)
    assert str(REPORT_JSON) == PATH_VOLSNAP_AUDIT_REPORT
    body = load_json_file(REPORT_JSON)
    ref = reference_retention_report(SCENARIO_CLEAN, FIXTURE_ROOT)
    assert body["deletable_snapshot_uids"] == ref["deletable_snapshot_uids"]


def test_csi_publish_retain_pin_protected_count() -> None:
    """Retain deletion policy snapshots increment protected_count in volsnap-audit-report.json."""
    wipe_audit_state()
    run_full_audit(SCENARIO_RETAIN)
    body = load_json_file(REPORT_JSON)
    ref = reference_retention_report(SCENARIO_RETAIN, FIXTURE_ROOT)
    assert body["protected_count"] == ref["protected_count"]


def test_csi_publish_policy_precedence_digest() -> None:
    """Backup policy precedence over storage class must match report_digest per volsnap-audit-contract."""
    wipe_audit_state()
    run_full_audit(SCENARIO_POLICY)
    body = load_json_file(REPORT_JSON)
    ref = reference_retention_report(SCENARIO_POLICY, FIXTURE_ROOT)
    assert body["report_digest"] == ref["report_digest"]


def test_csi_publish_dangling_ledger_rows() -> None:
    """Dangling snapshots export to orphan-snapshot-ledger.jsonl rows per dangling-contract."""
    wipe_audit_state()
    run_full_audit(SCENARIO_DANGLING)
    assert str(DANGLING_JSONL) == PATH_ORPHAN_SNAPSHOT_LEDGER
    rows = load_jsonl_file(DANGLING_JSONL)
    cluster = load_cluster(FIXTURE_ROOT, SCENARIO_DANGLING)
    assert rows == dangling_rows(cluster)


def test_csi_publish_quota_cap_violations() -> None:
    """Namespace quota projection lists quota_violations when restore bytes exceed max_snapshot_bytes."""
    wipe_audit_state()
    run_full_audit(SCENARIO_QUOTA)
    body = load_json_file(REPORT_JSON)
    ref = reference_retention_report(SCENARIO_QUOTA, FIXTURE_ROOT)
    assert body["quota_violations"] == ref["quota_violations"]


def test_csi_publish_class_override_deletable_set() -> None:
    """StorageClass retention_days override changes deletable_snapshot_uids versus cluster default."""
    wipe_audit_state()
    run_full_audit(SCENARIO_CLASS)
    body = load_json_file(REPORT_JSON)
    ref = reference_retention_report(SCENARIO_CLASS, FIXTURE_ROOT)
    assert body["deletable_snapshot_uids"] == ref["deletable_snapshot_uids"]
    # Age-10 snap on sc-fast (7d) is deletable under class override; default 30d would keep it.
    assert "snap-class-override-a" in body["deletable_snapshot_uids"]


def test_csi_publish_default_retention_env_override(tmp_path: Path, monkeypatch) -> None:
    """TB3_CLUSTER_DEFAULT_RETENTION_DAYS overrides cluster default when policy and class do not apply."""
    import json

    cluster = load_cluster(FIXTURE_ROOT, SCENARIO_CLEAN)
    cluster["backup_policies"] = []
    for sc in cluster["storage_classes"]:
        sc["retention_days"] = 0
    scenario = "default-retention-env"
    root = tmp_path / "fixtures"
    scen_dir = root / "clusters" / scenario
    scen_dir.mkdir(parents=True)
    (scen_dir / "cluster.json").write_text(json.dumps(cluster, indent=2) + "\n", encoding="utf-8")
    monkeypatch.setenv("TB3_CLUSTER_DEFAULT_RETENTION_DAYS", "200")
    wipe_audit_state()
    run_full_audit(
        scenario,
        fixture_root=root,
        extra_env={"TB3_CLUSTER_DEFAULT_RETENTION_DAYS": "200"},
    )
    body = load_json_file(REPORT_JSON)
    ref = reference_retention_report(scenario, root)
    assert body["deletable_snapshot_uids"] == ref["deletable_snapshot_uids"]
    assert body["deletable_snapshot_uids"] == []


def test_csi_publish_idempotent_report_digest() -> None:
    """Repeated publish-audit on stable-republish keeps byte-stable report_digest per publish contract."""
    wipe_audit_state()
    run_full_audit(SCENARIO_STABLE_REPUBLISH)
    first = load_json_file(REPORT_JSON)
    run_full_audit(SCENARIO_STABLE_REPUBLISH)
    second = load_json_file(REPORT_JSON)
    assert first["report_digest"] == second["report_digest"]


def test_csi_publish_pvc_join_chain_digest() -> None:
    """PVC join chain retention scoring must match independent report_digest reference math."""
    wipe_audit_state()
    run_full_audit(SCENARIO_PVC)
    body = load_json_file(REPORT_JSON)
    ref = reference_retention_report(SCENARIO_PVC, FIXTURE_ROOT)
    assert body["report_digest"] == ref["report_digest"]


def test_csi_publish_blocked_when_audit_pass_seq_zero() -> None:
    """publish-audit must fail when audit_pass_seq is zero per cli-surface.md."""
    wipe_audit_state()
    proc = invoke_audit(
        [
            AUDIT_BIN,
            "import-graph",
            "--scenario",
            SCENARIO_CLEAN,
            "--fixture-dir",
            str(FIXTURE_ROOT),
        ]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    blocked = invoke_audit([AUDIT_BIN, "publish-audit", "--scenario", SCENARIO_CLEAN])
    assert blocked.returncode != 0
    assert "audit_pass_seq" in (blocked.stderr + blocked.stdout).lower() or "blocked" in (
        blocked.stderr + blocked.stdout
    ).lower()
    assert not REPORT_JSON.is_file()
    assert not DANGLING_JSONL.is_file()


def test_csi_publish_custom_output_paths() -> None:
    """publish-audit --output-report and --output-dangling honor custom paths from cli-surface.md."""
    wipe_audit_state()
    custom_report = Path("/app/work/custom-volsnap-report.json")
    custom_ledger = Path("/app/work/custom-orphan-ledger.jsonl")
    for path in (custom_report, custom_ledger):
        if path.is_file():
            path.unlink()
    proc = invoke_audit(
        [
            AUDIT_BIN,
            "import-graph",
            "--scenario",
            SCENARIO_CLEAN,
            "--fixture-dir",
            str(FIXTURE_ROOT),
        ]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    proc = invoke_audit([AUDIT_BIN, "score-retention", "--scenario", SCENARIO_CLEAN])
    assert proc.returncode == 0, proc.stderr + proc.stdout
    proc = invoke_audit(
        [
            AUDIT_BIN,
            "publish-audit",
            "--scenario",
            SCENARIO_CLEAN,
            "--output-report",
            str(custom_report),
            "--output-dangling",
            str(custom_ledger),
        ]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert custom_report.is_file()
    assert custom_ledger.is_file()
    assert not REPORT_JSON.is_file()
    assert not DANGLING_JSONL.is_file()
    body = load_json_file(custom_report)
    ref = reference_retention_report(SCENARIO_CLEAN, FIXTURE_ROOT)
    assert body["deletable_snapshot_uids"] == ref["deletable_snapshot_uids"]


def test_csi_publish_byte_identical_report_and_ledger_republish() -> None:
    """Second publish-audit without state mutation is byte-identical for report and ledger."""
    wipe_audit_state()
    run_full_audit(SCENARIO_STABLE_REPUBLISH)
    report_bytes_1 = REPORT_JSON.read_bytes()
    ledger_bytes_1 = DANGLING_JSONL.read_bytes()
    proc = invoke_audit(
        [AUDIT_BIN, "publish-audit", "--scenario", SCENARIO_STABLE_REPUBLISH]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert REPORT_JSON.read_bytes() == report_bytes_1
    assert DANGLING_JSONL.read_bytes() == ledger_bytes_1
