"""TB3 hidden overlay traps for policy boundary and quota."""

from __future__ import annotations

from csi_audit_runner import (
    AUDIT_BIN,
    HIDDEN_FIXTURE_ROOT,
    REPORT_JSON,
    invoke_audit,
    load_json_file,
    wipe_audit_state,
)
from k8s_volume_refmath import reference_retention_report

PATH_VOLSNAP_AUDIT_REPORT = "/app/output/volsnap-audit-report.json"


def test_tb3_policy_boundary_hidden_deletable_uids() -> None:
    """TB3 policy-boundary-trap hidden fixture verifies backup precedence deletable set."""
    wipe_audit_state()
    env = {"TB3_FIXTURE_DIR": str(HIDDEN_FIXTURE_ROOT)}
    for step in (
        [AUDIT_BIN, "import-graph", "--scenario", "policy-boundary-trap", "--fixture-dir", str(HIDDEN_FIXTURE_ROOT)],
        [AUDIT_BIN, "score-retention", "--scenario", "policy-boundary-trap"],
        [AUDIT_BIN, "publish-audit", "--scenario", "policy-boundary-trap"],
    ):
        proc = invoke_audit(step, env=env)
        assert proc.returncode == 0, proc.stderr + proc.stdout
    assert str(REPORT_JSON) == PATH_VOLSNAP_AUDIT_REPORT
    body = load_json_file(REPORT_JSON)
    ref = reference_retention_report("policy-boundary-trap", HIDDEN_FIXTURE_ROOT)
    assert body["deletable_snapshot_uids"] == ref["deletable_snapshot_uids"]


def test_tb3_quota_hidden_trap_namespace_violation() -> None:
    """TB3 quota-hidden-trap verifies namespace byte quota violations on hidden fixtures."""
    wipe_audit_state()
    env = {"TB3_FIXTURE_DIR": str(HIDDEN_FIXTURE_ROOT)}
    invoke_audit(
        [AUDIT_BIN, "import-graph", "--scenario", "quota-hidden-trap", "--fixture-dir", str(HIDDEN_FIXTURE_ROOT)],
        env=env,
    )
    invoke_audit([AUDIT_BIN, "score-retention", "--scenario", "quota-hidden-trap"], env=env)
    invoke_audit([AUDIT_BIN, "publish-audit", "--scenario", "quota-hidden-trap"], env=env)
    body = load_json_file(REPORT_JSON)
    ref = reference_retention_report("quota-hidden-trap", HIDDEN_FIXTURE_ROOT)
    assert body["quota_violations"] == ref["quota_violations"]
