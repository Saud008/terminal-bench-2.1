"""Behavioral verifier for casctl access-decision attestation."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from types import ModuleType


def _load_casbin_batch_math() -> ModuleType:
    path = Path("/opt/verifier-casctl-math/casbin_batch_math.py")
    if not path.is_file():
        raise RuntimeError("verifier math bundle missing; test.sh must stage /opt/verifier-casctl-math")
    spec = importlib.util.spec_from_file_location("casbin_batch_math", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load reference module from {path}")
    mod = importlib.util.module_from_spec(spec)
    # dataclasses look up the module in sys.modules while the class body runs
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


_casbin_math = _load_casbin_batch_math()
reference_enforce = _casbin_math.reference_enforce
result_row = _casbin_math.result_row
select_bundles = _casbin_math.select_bundles

APP = Path("/app")
FIXTURES = APP / "fixtures"
CLI_CONFIG = APP / "config/casctl.json"
VERIFIER_CONFIG = Path("/opt/verifier-casctl/casctl.json")
VERIFIER_MATH = Path("/opt/verifier-casctl-math")
VERIFIER_LAYERS = Path("/opt/verifier-casctl-layers")
OUTPUT = APP / "output/enforce-report.json"
RESET = APP / "scripts/reset-state.sh"
SNAPSHOT = APP / "state/casctl/policy-snapshot.json"
AUTHZ_KERNEL = APP / "internal/authzkernel"
TESTS = Path(__file__).resolve().parent
BROKEN = TESTS / "patches" / "broken"
SEED = os.environ.get("VERIFIER_SEED", "casbin-seed-1")

PROTECTED_PATHS = [
    "models/rbac_domains_priority.conf",
    "policies/bundle-a/p.csv",
    "policies/bundle-a/g.csv",
    "policies/bundle-b/p.csv",
    "policies/bundle-b/g.csv",
    "policies/bundle-c/p.csv",
    "policies/bundle-c/g.csv",
    "requests/batch-alpha.jsonl",
    "requests/batch-beta.jsonl",
    "requests/batch-gamma.jsonl",
]

PROTECTED_SHA256: dict[str, str] = {
    "models/rbac_domains_priority.conf": "130b343fa87dbcf90d918d47e6dba580d4ca84612f6f655d5c10567a71c2804d",
    "policies/bundle-a/p.csv": "20241e3a2c8083e025a5eef711af1a5abe786131a6624ceabb3100f6c748797f",
    "policies/bundle-a/g.csv": "930b4f037ca28ed037ced0ac39b816b31996dfc4e4dc14539f32909538bc97f2",
    "policies/bundle-b/p.csv": "ad1cd69d0cc9402bb0bd338744456b0a70ea4a269a1236595933ede762b40fc0",
    "policies/bundle-b/g.csv": "084f628c102c924f32b41d8a150ae94a0a235c62588050fcee15e3e60b6acd98",
    "policies/bundle-c/p.csv": "2352e647f94c88660343ef62cd7cbfed2d5efe627cb417a09b51d617b1a9ad13",
    "policies/bundle-c/g.csv": "64480b632723bdd6d0d746a74c88c3a4eec064a9bb422c0fd955f8ea1c7ce045",
    "requests/batch-alpha.jsonl": "871490fa6e6ad89707add9326f4291e5429c905ca3842204090302110007a1a9",
    "requests/batch-beta.jsonl": "62aa63aa01834b3e28c0aa05272cb709135a0d8b4477a515c30ebbabddb7aad7",
    "requests/batch-gamma.jsonl": "5f573ee30a626b0a6bcbe695ee1c8945869cf4af5a55c25fccfe01950f9dd52b",
}

CANONICAL_CONFIG_SHA256 = "0ab0bf6f100f703c422e021bd3e640533926b33c0c988cfc0762fb8a71df7796"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run(cmd: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd or APP),
        capture_output=True,
        text=True,
        check=False,
    )


def reset_state() -> None:
    proc = _run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def build_cli() -> None:
    proc = _run(
        ["go", "build", "-mod=readonly", "-o", "/usr/local/bin/casctl", "./cmd/casctl"],
        cwd=APP,
    )
    assert proc.returncode == 0, proc.stderr


def with_partial_patch(files: dict[str, Path], fn) -> None:
    saved: dict[Path, str] = {}
    try:
        for target in AUTHZ_KERNEL.glob("*.go"):
            saved[target] = target.read_text(encoding="utf-8")
            broken = BROKEN / target.name
            if broken.is_file():
                shutil.copy2(broken, target)
        for dest_name, src in files.items():
            shutil.copy2(src, AUTHZ_KERNEL / dest_name)
        build_cli()
        fn()
    finally:
        for target, content in saved.items():
            target.write_text(content, encoding="utf-8")
        build_cli()


def enforce(
    requests: Path,
    output: Path = OUTPUT,
    config: Path = CLI_CONFIG,
) -> subprocess.CompletedProcess[str]:
    output.parent.mkdir(parents=True, exist_ok=True)
    return _run(
        [
            "casctl",
            "enforce",
            "--config",
            str(config),
            "--requests",
            str(requests),
            "--output",
            str(output),
        ]
    )


class TestCasctlEnforce:
    """Offline RBAC authorization gate — subprocess casctl enforce vs independent reference."""

    @classmethod
    def setup_class(cls) -> None:
        reset_state()
        build_cli()

    def test_canonical_artifact_paths_written(self) -> None:
        """enforce must write /app/output/enforce-report.json and stage /app/state/casctl/policy-snapshot.json."""
        reset_state()
        req = FIXTURES / "requests/batch-alpha.jsonl"
        assert OUTPUT == Path("/app/output/enforce-report.json")
        assert SNAPSHOT == Path("/app/state/casctl/policy-snapshot.json")
        proc = enforce(req, OUTPUT)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        assert OUTPUT.is_file()
        assert (APP / "state/casctl").is_dir()
        assert SNAPSHOT.is_file()
        json.loads(OUTPUT.read_text(encoding="utf-8"))
        json.loads(SNAPSHOT.read_text(encoding="utf-8"))

    def test_fixture_integrity_hashes(self) -> None:
        """Protected fixtures must not be modified."""
        for rel, expect in PROTECTED_SHA256.items():
            assert _sha256(FIXTURES / rel) == expect, f"fixture tampered: {rel}"

    def test_config_integrity_hash(self) -> None:
        """Canonical casctl config must match verifier-controlled ground truth."""
        assert VERIFIER_CONFIG.is_file(), "verifier config snapshot missing"
        assert _sha256(CLI_CONFIG) == CANONICAL_CONFIG_SHA256, "cli config tampered"
        assert _sha256(VERIFIER_CONFIG) == CANONICAL_CONFIG_SHA256, "verifier config drift"

    def test_verifier_ground_truth_staged_outside_app(self) -> None:
        """Reference math and golden layers must be staged under /opt, not shipped in /app."""
        assert VERIFIER_MATH.is_dir(), "verifier math bundle missing"
        assert (VERIFIER_MATH / "casbin_batch_math.py").is_file()
        assert VERIFIER_LAYERS.is_dir(), "verifier layer bundle missing"
        assert list(VERIFIER_LAYERS.glob("golden_*.go"))
        assert not list((APP / "internal/authzkernel").glob("golden_*.go"))

    def test_agent_sources_lack_bug_hint_comments(self) -> None:
        """Starter authz kernel sources must not label defect locations."""
        for name in ("staging.go", "audit.go"):
            text = (AUTHZ_KERNEL / name).read_text(encoding="utf-8")
            assert "Broken:" not in text, f"{name} must not contain Broken: hints"

    def test_alpha_batch_matches_reference(self) -> None:
        """batch-alpha decisions must match independent reference attestation."""
        req = FIXTURES / "requests/batch-alpha.jsonl"
        out = OUTPUT
        proc = enforce(req, out)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = json.loads(out.read_text(encoding="utf-8"))
        expect = reference_enforce(VERIFIER_CONFIG, req, FIXTURES)
        assert got == expect

    def test_beta_batch_matches_reference(self) -> None:
        """batch-beta decisions must match independent reference attestation."""
        req = FIXTURES / "requests/batch-beta.jsonl"
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "beta.json"
            assert enforce(req, out).returncode == 0
            got = json.loads(out.read_text(encoding="utf-8"))
            expect = reference_enforce(VERIFIER_CONFIG, req, FIXTURES)
            assert got == expect

    def test_gamma_batch_matches_reference(self) -> None:
        """batch-gamma decisions must match independent reference attestation."""
        req = FIXTURES / "requests/batch-gamma.jsonl"
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "gamma.json"
            assert enforce(req, out).returncode == 0
            got = json.loads(out.read_text(encoding="utf-8"))
            expect = reference_enforce(VERIFIER_CONFIG, req, FIXTURES)
            assert got == expect

    def test_deny_overrides_allow_on_conflict(self) -> None:
        """Direct deny must beat inherited allow for alice records write."""
        req = FIXTURES / "requests/batch-alpha.jsonl"
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.json"
            assert enforce(req, out).returncode == 0
            doc = json.loads(out.read_text(encoding="utf-8"))
            row = result_row(doc, "alice", "tenant1", "records", "write")
            assert row["decision"] == "deny"
            assert row["match_count"] == 2

    def test_priority_low_and_high_rules_both_match(self) -> None:
        """Priority-1 admin allow and priority-3 alice deny must both match before effect."""
        req = FIXTURES / "requests/batch-alpha.jsonl"
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.json"
            assert enforce(req, out).returncode == 0
            row = result_row(json.loads(out.read_text(encoding="utf-8")), "alice", "tenant1", "records", "write")
            assert row["match_count"] == 2
            assert row["decision"] == "deny"

    def test_transitive_role_inheritance_allow(self) -> None:
        """alice must inherit admin via editor chain for admin-panel read."""
        req = FIXTURES / "requests/batch-alpha.jsonl"
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.json"
            assert enforce(req, out).returncode == 0
            doc = json.loads(out.read_text(encoding="utf-8"))
            row = result_row(doc, "alice", "tenant1", "admin-panel", "read")
            assert row["decision"] == "allow"

    def test_domain_isolation_cross_tenant(self) -> None:
        """alice tenant2 request must deny without tenant2 role linkage."""
        req = FIXTURES / "requests/batch-beta.jsonl"
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.json"
            assert enforce(req, out).returncode == 0
            doc = json.loads(out.read_text(encoding="utf-8"))
            row = result_row(doc, "alice", "tenant2", "records", "read")
            assert row["decision"] == "deny"
            assert row["match_count"] == 0

    def test_domain_scoped_deny_exception(self) -> None:
        """nina shared read allowed in tenant1 but denied in tenant2."""
        req = FIXTURES / "requests/batch-gamma.jsonl"
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.json"
            assert enforce(req, out).returncode == 0
            doc = json.loads(out.read_text(encoding="utf-8"))
            assert result_row(doc, "nina", "tenant1", "shared", "read")["decision"] == "allow"
            assert result_row(doc, "nina", "tenant2", "shared", "read")["decision"] == "deny"

    def test_policies_loaded_at_least_twenty(self) -> None:
        """Merged bundles must load 20+ policy rules."""
        req = FIXTURES / "requests/batch-alpha.jsonl"
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.json"
            assert enforce(req, out).returncode == 0
            doc = json.loads(out.read_text(encoding="utf-8"))
            assert doc["stats"]["policies_loaded"] >= 20

    def test_alternate_seed_subset_matches_reference(self) -> None:
        """Partial bundle seed must still match independent reference replay."""
        cfg = json.loads(VERIFIER_CONFIG.read_text(encoding="utf-8"))
        cfg["seed"] = "casbin-seed-0"
        with tempfile.TemporaryDirectory() as tmp:
            cfg_path = Path(tmp) / "cfg.json"
            cfg_path.write_text(json.dumps(cfg), encoding="utf-8")
            req = FIXTURES / "requests/batch-gamma.jsonl"
            out = Path(tmp) / "out.json"
            assert enforce(req, out, cfg_path).returncode == 0
            got = json.loads(out.read_text(encoding="utf-8"))
            expect = reference_enforce(cfg_path, req, FIXTURES)
            assert got == expect
            assert got["stats"]["policies_loaded"] == 16
            assert got["bundles"] == select_bundles("casbin-seed-0", cfg["bundles"])

    def test_seed_subset_changes_decision(self) -> None:
        """Fewer bundles loaded via seed must change decisions requiring absent rules."""
        req = FIXTURES / "requests/batch-gamma.jsonl"
        full_cfg = json.loads(VERIFIER_CONFIG.read_text(encoding="utf-8"))
        partial_cfg = dict(full_cfg)
        partial_cfg["seed"] = "casbin-seed-0"
        with tempfile.TemporaryDirectory() as tmp:
            full_path = Path(tmp) / "full.json"
            partial_path = Path(tmp) / "partial.json"
            full_cfg_path = Path(tmp) / "full_cfg.json"
            partial_cfg_path = Path(tmp) / "partial_cfg.json"
            full_cfg_path.write_text(json.dumps(full_cfg), encoding="utf-8")
            partial_cfg_path.write_text(json.dumps(partial_cfg), encoding="utf-8")
            assert enforce(req, full_path, full_cfg_path).returncode == 0
            assert enforce(req, partial_path, partial_cfg_path).returncode == 0
            full_doc = json.loads(full_path.read_text(encoding="utf-8"))
            partial_doc = json.loads(partial_path.read_text(encoding="utf-8"))
            assert result_row(full_doc, "nina", "tenant1", "shared", "read")["decision"] == "allow"
            assert result_row(partial_doc, "nina", "tenant1", "shared", "read")["decision"] == "deny"

    def test_auditor_inherited_deny_beats_allow(self) -> None:
        """dave logs delete must deny via auditor role deny rule."""
        req = FIXTURES / "requests/batch-alpha.jsonl"
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.json"
            assert enforce(req, out).returncode == 0
            doc = json.loads(out.read_text(encoding="utf-8"))
            row = result_row(doc, "dave", "tenant1", "logs", "delete")
            assert row["decision"] == "deny"

    def test_grace_deny_overrides_admin_allow(self) -> None:
        """grace warehouse ship must deny despite clerk-admin inheritance."""
        req = FIXTURES / "requests/batch-beta.jsonl"
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.json"
            assert enforce(req, out).returncode == 0
            doc = json.loads(out.read_text(encoding="utf-8"))
            row = result_row(doc, "grace", "tenant2", "warehouse", "ship")
            assert row["decision"] == "deny"
            assert row["match_count"] >= 2

    def test_alice_records_read_match_count_two(self) -> None:
        """alice records read must count both direct and inherited admin allows."""
        req = FIXTURES / "requests/batch-alpha.jsonl"
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.json"
            assert enforce(req, out).returncode == 0
            row = result_row(json.loads(out.read_text(encoding="utf-8")), "alice", "tenant1", "records", "read")
            assert row["decision"] == "allow"
            assert row["match_count"] == 2

    def test_eve_reports_read_same_priority_wildcard_pair(self) -> None:
        """eve reports read must count wildcard deny and read allow at same priority."""
        req = FIXTURES / "requests/batch-alpha.jsonl"
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.json"
            assert enforce(req, out).returncode == 0
            row = result_row(json.loads(out.read_text(encoding="utf-8")), "eve", "tenant1", "reports", "read")
            assert row["decision"] == "deny"
            assert row["match_count"] == 2

    def test_lisa_tickets_close_counts_support_and_direct(self) -> None:
        """lisa tickets close must count inherited support deny and direct allow."""
        req = FIXTURES / "requests/batch-gamma.jsonl"
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.json"
            assert enforce(req, out).returncode == 0
            row = result_row(json.loads(out.read_text(encoding="utf-8")), "lisa", "tenant1", "tickets", "close")
            assert row["decision"] == "deny"
            assert row["match_count"] == 2

    def test_enforce_writes_policy_snapshot(self) -> None:
        """enforce must stage policy snapshot before exporting decisions."""
        req = FIXTURES / "requests/batch-alpha.jsonl"
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.json"
            assert enforce(req, out).returncode == 0
            assert SNAPSHOT.is_file(), "policy snapshot missing"
            snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
            cfg = json.loads(VERIFIER_CONFIG.read_text(encoding="utf-8"))
            assert snap["seed"] == cfg["seed"]
            assert snap["bundles"] == select_bundles(cfg["seed"], cfg["bundles"])
            assert len(snap["policy_fingerprint"]) == 64
            assert len(snap["grouping_fingerprint"]) == 64

    def test_audit_digest_binds_snapshot_and_results(self) -> None:
        """audit_digest must bind snapshot fingerprints to exported rows."""
        req = FIXTURES / "requests/batch-beta.jsonl"
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.json"
            assert enforce(req, out).returncode == 0
            got = json.loads(out.read_text(encoding="utf-8"))
            expect = reference_enforce(VERIFIER_CONFIG, req, FIXTURES)
            assert got["audit_digest"] == expect["audit_digest"]
            assert got["audit_digest"] != ""

    def test_eve_reports_export_same_priority_pair(self) -> None:
        """eve reports export must deny with both priority-7 wildcard and direct rules counted."""
        req = FIXTURES / "requests/batch-alpha.jsonl"
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.json"
            assert enforce(req, out).returncode == 0
            row = result_row(json.loads(out.read_text(encoding="utf-8")), "eve", "tenant1", "reports", "export")
            assert row["decision"] == "deny"
            assert row["match_count"] == 2

    def test_partial_effect_only_still_fails_audit_digest(self) -> None:
        """Effect layer alone must not produce a valid audit_digest witness binding."""
        def run() -> None:
            reset_state()
            req = FIXTURES / "requests/batch-alpha.jsonl"
            with tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp) / "out.json"
                assert enforce(req, out).returncode == 0
                got = json.loads(out.read_text(encoding="utf-8"))
                expect = reference_enforce(VERIFIER_CONFIG, req, FIXTURES)
                assert got["audit_digest"] != expect["audit_digest"]

        with_partial_patch({"effect.go": VERIFIER_LAYERS / "golden_effect.go"}, run)

    def test_partial_match_only_still_fails_carol_pair(self) -> None:
        """Matcher layer alone must not count both same-priority carol rules."""
        def run() -> None:
            reset_state()
            req = FIXTURES / "requests/batch-alpha.jsonl"
            with tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp) / "out.json"
                assert enforce(req, out).returncode == 0
                row = result_row(json.loads(out.read_text(encoding="utf-8")), "carol", "tenant1", "admin-panel", "read")
                assert row["match_count"] != 2

        with_partial_patch({"match.go": VERIFIER_LAYERS / "golden_match.go"}, run)

    def test_partial_staging_only_still_fails_audit_digest(self) -> None:
        """Snapshot staging layer alone must not bind audit_digest to loaded bundles."""
        def run() -> None:
            reset_state()
            req = FIXTURES / "requests/batch-gamma.jsonl"
            with tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp) / "out.json"
                assert enforce(req, out).returncode == 0
                got = json.loads(out.read_text(encoding="utf-8"))
                expect = reference_enforce(VERIFIER_CONFIG, req, FIXTURES)
                assert got["audit_digest"] != expect["audit_digest"]

        with_partial_patch({"staging.go": VERIFIER_LAYERS / "golden_staging.go"}, run)

    def test_partial_audit_only_still_fails_reference_report(self) -> None:
        """Audit digest layer alone must not match full reference enforcement report."""
        def run() -> None:
            reset_state()
            req = FIXTURES / "requests/batch-beta.jsonl"
            with tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp) / "out.json"
                assert enforce(req, out).returncode == 0
                got = json.loads(out.read_text(encoding="utf-8"))
                expect = reference_enforce(VERIFIER_CONFIG, req, FIXTURES)
                assert got != expect

        with_partial_patch({"audit.go": VERIFIER_LAYERS / "golden_audit.go"}, run)

    def test_tb3_verifier_config_seed_subset_matches_reference(self) -> None:
        """TB3 /opt/verifier-casctl config with casbin-seed-0 must match reference replay."""
        verifier_cfg = Path("/opt/verifier-casctl/casctl.json")
        assert verifier_cfg.is_file(), "missing /opt/verifier-casctl/casctl.json"
        cfg = json.loads(verifier_cfg.read_text(encoding="utf-8"))
        cfg["seed"] = "casbin-seed-0"
        with tempfile.TemporaryDirectory() as tmp:
            cfg_path = Path(tmp) / "tb3_cfg.json"
            cfg_path.write_text(json.dumps(cfg), encoding="utf-8")
            req = FIXTURES / "requests/batch-gamma.jsonl"
            out = Path(tmp) / "tb3_out.json"
            assert enforce(req, out, cfg_path).returncode == 0
            got = json.loads(out.read_text(encoding="utf-8"))
            expect = reference_enforce(cfg_path, req, FIXTURES)
            assert got == expect
            assert got["stats"]["policies_loaded"] == 16

    def test_tb3_verifier_config_drift_breaks_audit_digest(self) -> None:
        """TB3 hidden /opt/verifier-casctl ground truth must bind audit_digest for beta batch."""
        verifier_cfg = Path("/opt/verifier-casctl/casctl.json")
        assert verifier_cfg.is_file()
        req = FIXTURES / "requests/batch-beta.jsonl"
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "tb3_beta.json"
            assert enforce(req, out).returncode == 0
            got = json.loads(out.read_text(encoding="utf-8"))
            expect = reference_enforce(verifier_cfg, req, FIXTURES)
            assert got["audit_digest"] == expect["audit_digest"]
            assert got["results"] == expect["results"]
