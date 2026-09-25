from __future__ import annotations

import os
import shutil
import subprocess
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest

from reference_sentinel import (
    expected_audit_exit,
    expected_report,
    expected_stage,
    load_catalog,
    load_json,
)

BIN = Path("/app/bin/tf-tag-sentinel")
PLANS = Path("/app/fixtures/plans")
POLICY = Path("/app/config/tag-policies.json")
EXPIRED_POLICY = Path("/app/fixtures/policies/expired-waiver-policy.json")
STATE = Path("/app/state")
OUTPUT = Path("/app/output")
STAGING = STATE / "plan-tag.stage"
REPORT = OUTPUT / "tag-violations.json"
STAGING_PATH = "/app/state/plan-tag.stage"
REPORT_PATH = "/app/output/tag-violations.json"
LIB = Path("/app/lib")
BROKEN = Path("/opt/verifier-broken-sentinel")
GOLDEN = Path("/tests/golden_lib")
TB3_PLAN = Path("/opt/verifier-fixtures/tf-plans/tb3-random-plan.json")
TB3_POLICY = Path("/opt/verifier-fixtures/tf-policies/tb3-random-policy.json")
TB3_META = Path("/opt/verifier-fixtures/tf-plans/tb3-meta.json")
MODULES = (
    "common",
    "parse_plan",
    "alias",
    "inherit",
    "moved",
    "unknowns",
    "policy",
    "staging",
    "report",
)
CAT = load_catalog(PLANS / "catalog.json")


def _tool_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    merged = os.environ.copy()
    merged["PATH"] = "/app/bin:/opt/verifier-venv/bin:/usr/local/bin:" + merged.get("PATH", "")
    merged["APP_ROOT"] = "/app"
    if extra:
        merged.update(extra)
    return merged


def run(cmd: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd, cwd="/app", capture_output=True, text=True, check=False, env=_tool_env(env)
    )


def reset() -> None:
    if STATE.exists():
        shutil.rmtree(STATE)
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    STATE.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    Path("/app/state/run-registry.json").write_text('{"runs":[]}\n', encoding="utf-8")


def ingest(
    plan: Path,
    policy: Path = POLICY,
    staging: Path = STAGING,
) -> subprocess.CompletedProcess[str]:
    return run(
        [
            str(BIN),
            "ingest",
            "--plan",
            str(plan),
            "--policy",
            str(policy),
            "--staging",
            str(staging),
        ]
    )


def audit(
    out: Path = REPORT,
    policy: Path = POLICY,
    staging: Path = STAGING,
) -> subprocess.CompletedProcess[str]:
    return run(
        [
            str(BIN),
            "audit",
            "--staging",
            str(staging),
            "--policy",
            str(policy),
            "--out",
            str(out),
        ]
    )


def run_pipeline(
    plan: Path,
    out: Path = REPORT,
    policy: Path = POLICY,
    staging: Path = STAGING,
) -> subprocess.CompletedProcess[str]:
    proc = ingest(plan, policy, staging)
    if proc.returncode != 0:
        return proc
    return audit(out, policy, staging)


def install_modules(only_broken: set[str]) -> None:
    for mod in MODULES:
        src = BROKEN / f"{mod}.sh" if mod in only_broken else GOLDEN / f"{mod}.sh"
        shutil.copy2(src, LIB / f"{mod}.sh")
        os.chmod(LIB / f"{mod}.sh", 0o755)


def restore_broken() -> None:
    for mod in MODULES:
        shutil.copy2(BROKEN / f"{mod}.sh", LIB / f"{mod}.sh")


@contextmanager
def partial_module_trap(only_broken: set[str]) -> Iterator[None]:
    install_modules(only_broken)
    try:
        yield
    finally:
        install_modules(set())


def stage_digest(plan_path: Path) -> str:
    import hashlib

    return hashlib.sha256(plan_path.read_bytes()).hexdigest()


@pytest.fixture(autouse=True)
def _reset() -> None:
    reset()


def test_catalog_lists_plans() -> None:
    """Fixture catalog exposes bundled Terraform plan JSON scenarios."""
    assert len(CAT["plans"]) >= 4


def test_binary_exists() -> None:
    """tf-tag-sentinel CLI is installed at /app/bin/tf-tag-sentinel."""
    assert BIN.is_file()


@pytest.mark.parametrize("plan_id", ["base", "moved", "unknown", "waiver"])
def test_ingest_writes_expected_staging(plan_id: str) -> None:
    """ingest writes /app/state/plan-tag.stage matching the independent reference."""
    plan_path = PLANS / str(CAT["plans"][next(i for i, p in enumerate(CAT["plans"]) if p["id"] == plan_id)]["path"])
    proc = ingest(plan_path)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert str(STAGING) == STAGING_PATH
    assert load_json(STAGING) == expected_stage(plan_path, POLICY)


def test_ingest_does_not_write_report() -> None:
    """ingest alone must not create /app/output/tag-violations.json."""
    proc = ingest(PLANS / "base-plan.json")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert STAGING.is_file()
    assert str(REPORT) == REPORT_PATH
    assert not REPORT.exists()


def test_audit_reads_staging_only() -> None:
    """audit evaluates frozen staging and ignores later plan mutations."""
    plan_path = PLANS / "base-plan.json"
    scratch = OUTPUT / "mutated-plan.json"
    shutil.copy2(plan_path, scratch)
    proc = ingest(plan_path)
    assert proc.returncode == 0
    scratch.write_text('{"resource_changes":[]}\n', encoding="utf-8")
    out = OUTPUT / "audit-only.json"
    proc_audit = audit(out)
    assert proc_audit.returncode == expected_audit_exit(expected_report(load_json(STAGING), load_json(POLICY)))
    assert load_json(out) == expected_report(load_json(STAGING), load_json(POLICY))


def test_base_plan_pipeline_report() -> None:
    """Full pipeline writes /app/output/tag-violations.json for the base plan."""
    plan_path = PLANS / "base-plan.json"
    proc = run_pipeline(plan_path)
    expected = expected_report(expected_stage(plan_path, POLICY), load_json(POLICY))
    assert proc.returncode == expected_audit_exit(expected)
    assert REPORT.is_file()
    assert str(REPORT) == REPORT_PATH
    assert load_json(REPORT) == expected


def test_moved_plan_detects_tag_drift_remove() -> None:
    """Moved update that drops inherited tags emits TAG_DRIFT_REMOVE."""
    plan_path = PLANS / "moved-plan.json"
    proc = run_pipeline(plan_path, out=OUTPUT / "moved.json")
    assert proc.returncode == 2
    report = load_json(OUTPUT / "moved.json")
    codes = {v["code"] for v in report["violations"]}
    assert "TAG_DRIFT_REMOVE" in codes


def test_unknown_plan_emits_unknown_exempt() -> None:
    """Computed unknown literals produce UNKNOWN_EXEMPT info rows."""
    plan_path = PLANS / "unknown-plan.json"
    proc = run_pipeline(plan_path, out=OUTPUT / "unknown.json")
    assert proc.returncode == expected_audit_exit(
        expected_report(expected_stage(plan_path, POLICY), load_json(POLICY))
    )
    report = load_json(OUTPUT / "unknown.json")
    assert report["summary"]["unknown_exempt_count"] >= 2
    assert any(v["code"] == "UNKNOWN_EXEMPT" for v in report["violations"])


def test_provider_alias_maps_east_to_aws_scope() -> None:
    """provider_aliases maps aws.east to aws deny scope."""
    plan_path = PLANS / "base-plan.json"
    stage = expected_stage(plan_path, POLICY)
    vpc = next(r for r in stage["resources"] if r["address"] == "module.network.aws_vpc.core")
    assert vpc["provider_key"] == "aws.east"
    assert vpc["provider_scope"] == "aws"


def test_module_inheritance_adds_cost_center() -> None:
    """module.network defaults inject cost_center on child resources."""
    plan_path = PLANS / "base-plan.json"
    stage = expected_stage(plan_path, POLICY)
    vpc = next(r for r in stage["resources"] if r["address"] == "module.network.aws_vpc.core")
    assert vpc["effective_tags_after"]["cost_center"] == "CC-NET-400"


def test_bastion_waiver_suppresses_missing_cost_center() -> None:
    """Resource-specific waiver suppresses MISSING_REQUIRED_TAG for bastion."""
    plan_path = PLANS / "base-plan.json"
    report = expected_report(expected_stage(plan_path, POLICY), load_json(POLICY))
    waived = {(w["resource"], w["tag_key"]) for w in report["waived"]}
    assert ("aws_instance.bastion", "cost_center") in waived
    assert not any(
        v["resource"] == "aws_instance.bastion" and v["code"] == "MISSING_REQUIRED_TAG"
        for v in report["violations"]
    )


def test_expired_waiver_allows_deny() -> None:
    """Expired waivers do not suppress deny violations."""
    plan_path = PLANS / "waiver-plan.json"
    proc = run_pipeline(plan_path, out=OUTPUT / "expired.json", policy=EXPIRED_POLICY)
    assert proc.returncode == 2
    report = load_json(OUTPUT / "expired.json")
    assert any(
        v["resource"] == "aws_instance.expired_waiver" and v["code"] == "MISSING_REQUIRED_TAG"
        for v in report["violations"]
    )


def test_monitoring_module_waiver_for_environment() -> None:
    """module_prefix waiver applies to module.monitoring resources."""
    plan_path = PLANS / "waiver-plan.json"
    report = expected_report(expected_stage(plan_path, POLICY), load_json(POLICY))
    assert any(w["resource"].startswith("module.monitoring") for w in report["waived"])


def test_violations_sorted_lexicographically() -> None:
    """Violation rows sort by resource, tag_key, then code."""
    plan_path = PLANS / "base-plan.json"
    report = expected_report(expected_stage(plan_path, POLICY), load_json(POLICY))
    rows = [(v["resource"], v["tag_key"], v["code"]) for v in report["violations"]]
    assert rows == sorted(rows)


def test_report_carries_staging_digests() -> None:
    """Report copies plan_digest and policy_digest from staging."""
    plan_path = PLANS / "base-plan.json"
    stage = expected_stage(plan_path, POLICY)
    proc = run_pipeline(plan_path)
    assert proc.returncode == expected_audit_exit(expected_report(stage, load_json(POLICY)))
    report = load_json(REPORT)
    assert report["plan_digest"] == stage["plan_digest"]
    assert report["policy_digest"] == stage["policy_digest"]


def test_run_registry_tracks_plan_digest() -> None:
    """ingest updates /app/state/run-registry.json with plan digest."""
    plan_path = PLANS / "base-plan.json"
    proc = ingest(plan_path)
    assert proc.returncode == 0
    registry = load_json(STATE / "run-registry.json")
    assert registry["runs"][-1]["plan_digest"] == stage_digest(plan_path)


def test_decoy_not_on_hot_path() -> None:
    """legacy_flatten decoy exists but pipeline still passes with golden modules."""
    decoy = Path("/app/lib/decoy/legacy_flatten.sh")
    assert decoy.is_file()
    plan_path = PLANS / "base-plan.json"
    proc = run_pipeline(plan_path)
    assert proc.returncode == expected_audit_exit(
        expected_report(expected_stage(plan_path, POLICY), load_json(POLICY))
    )


def test_instruction_staging_path_written() -> None:
    """Instruction staging path /app/state/plan-tag.stage is created by ingest."""
    plan_path = PLANS / "base-plan.json"
    proc = ingest(plan_path, staging=Path(STAGING_PATH))
    assert proc.returncode == 0
    assert Path(STAGING_PATH).is_file()
    assert load_json(Path(STAGING_PATH))["schema"] == "plan-tag-stage/1"


def test_export_report_from_staging_snapshot() -> None:
    """export audit phase emits /app/output/tag-violations.json from staging only."""
    plan_path = PLANS / "waiver-plan.json"
    proc = ingest(plan_path)
    assert proc.returncode == 0
    out = OUTPUT / "export-only.json"
    proc_audit = audit(out)
    report = expected_report(load_json(STAGING), load_json(POLICY))
    assert proc_audit.returncode == expected_audit_exit(report)
    assert load_json(out) == report


def test_ingest_only_does_not_export_report() -> None:
    """ingest stage alone must not run export audit output."""
    proc = ingest(PLANS / "unknown-plan.json")
    assert proc.returncode == 0
    assert STAGING.is_file()
    assert not (OUTPUT / "tag-violations.json").exists()


def test_instruction_report_path_written() -> None:
    """Instruction report path /app/output/tag-violations.json is created by audit."""
    plan_path = PLANS / "base-plan.json"
    proc = run_pipeline(plan_path, out=Path(REPORT_PATH))
    expected = expected_report(expected_stage(plan_path, POLICY), load_json(POLICY))
    assert proc.returncode == expected_audit_exit(expected)
    assert Path(REPORT_PATH).is_file()
    assert load_json(Path(REPORT_PATH))["schema"] == "tag-violation-report/1"


@pytest.mark.skipif(not TB3_PLAN.is_file(), reason="TB3 fixtures not mounted")
def test_tb3_random_addresses_require_alias_and_inherit() -> None:
    """TB3 seeded plan uses random addresses requiring alias and inheritance."""
    meta = load_json(TB3_META)
    proc = run_pipeline(TB3_PLAN, out=OUTPUT / "tb3.json", policy=TB3_POLICY)
    stage = expected_stage(TB3_PLAN, TB3_POLICY)
    assert proc.returncode == expected_audit_exit(expected_report(stage, load_json(TB3_POLICY)))
    suffix = meta["suffix"]
    assert any(f"tb3_{suffix}" in r["address"] for r in stage["resources"])


@pytest.mark.skipif(not TB3_PLAN.is_file(), reason="TB3 fixtures not mounted")
def test_tb3_hidden_plan_differs_from_bundled_catalog() -> None:
    """Hidden TB3 plan is not listed in the bundled catalog."""
    meta = load_json(TB3_META)
    assert meta["suffix"]
    assert not any(p["id"] == f"tb3_{meta['suffix']}" for p in CAT["plans"])


def test_partial_moved_only_fix_fails_lineage() -> None:
    """Moved-only partial fix skips previous_address before-tag merge."""
    with partial_module_trap({"moved"}):
        plan_path = PLANS / "moved-plan.json"
        proc = ingest(plan_path)
        assert proc.returncode == 0
        stage = load_json(STAGING)
        archive = next(r for r in stage["resources"] if r["address"] == "aws_s3_bucket.archive")
        assert "cost_center" not in archive.get("effective_tags_before", {})


def test_partial_alias_only_fix_leaves_wrong_scope() -> None:
    """Alias-only partial fix keeps unmapped provider scope."""
    with partial_module_trap({"alias"}):
        plan_path = PLANS / "base-plan.json"
        proc = ingest(plan_path)
        assert proc.returncode == 0
        stage = load_json(STAGING)
        vpc = next(r for r in stage["resources"] if r["address"] == "module.network.aws_vpc.core")
        assert vpc["provider_scope"] == "aws.east"


def test_partial_report_only_fix_fails_moved_drift() -> None:
    """Report-only partial fix omits TAG_DRIFT_REMOVE detection."""
    with partial_module_trap({"report"}):
        plan_path = PLANS / "moved-plan.json"
        proc = run_pipeline(plan_path, out=OUTPUT / "partial-moved.json")
        assert proc.returncode in (0, 2)
        report = load_json(OUTPUT / "partial-moved.json")
        assert "TAG_DRIFT_REMOVE" not in {v["code"] for v in report["violations"]}


def test_azurerm_create_requires_environment() -> None:
    """azurerm create deny rule requires environment tag."""
    plan_path = PLANS / "base-plan.json"
    report = expected_report(expected_stage(plan_path, POLICY), load_json(POLICY))
    assert any(
        v["resource"] == "azurerm_storage_account.logs"
        and v["tag_key"] == "environment"
        and v["code"] == "MISSING_REQUIRED_TAG"
        for v in report["violations"]
    )


def test_moved_resource_inherits_previous_before_tags() -> None:
    """Move actions inherit before tags from previous_address when before is sparse."""
    plan_path = PLANS / "moved-plan.json"
    stage = expected_stage(plan_path, POLICY)
    archive = next(r for r in stage["resources"] if r["address"] == "aws_s3_bucket.archive")
    assert archive["effective_tags_before"].get("cost_center") == "CC-STORE-300"


def test_audit_exit_code_two_when_denies_present() -> None:
    """audit exits 2 when deny_count is greater than zero."""
    plan_path = PLANS / "moved-plan.json"
    proc = run_pipeline(plan_path, out=OUTPUT / "exit.json")
    assert proc.returncode == 2


def test_audit_exit_code_zero_when_only_waived_and_info() -> None:
    """audit exits 0 when no deny violations remain."""
    plan_path = PLANS / "waiver-plan.json"
    proc = run_pipeline(plan_path, out=OUTPUT / "waiver-only.json")
    report = expected_report(expected_stage(plan_path, POLICY), load_json(POLICY))
    if report["summary"]["deny_count"] == 0:
        assert proc.returncode == 0
