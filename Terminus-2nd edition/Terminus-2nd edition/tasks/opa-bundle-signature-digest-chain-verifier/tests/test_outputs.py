"""Verifier tests for bundlectl verify/eval contract acceptance."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest
from reference_bundle import reference_eval, reference_verify

APP = Path("/app")
CLI = Path("/usr/local/bin/bundlectl")
BUNDLES = APP / "fixtures" / "bundles"
SEEDS = json.loads((APP / "fixtures" / "seeds.json").read_text(encoding="utf-8"))
OUTPUT = APP / "output"
STATE = APP / "state"
PREVIEW_LEDGER = STATE / "preview-ledger.json"
EVAL_AUDIT = STATE / "eval-audit.json"
TB3_BUNDLES = Path("/opt/verifier-fixtures/tb3-bundles")

GOOD = ["allow-basic", "deny-edge", "multi-scope", "path-normalize"]
TRAPS = ["tampered-member", "revoked-signer", "bad-scope-chain", "path-escape"]


def run(cmd: list[str], check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=check, capture_output=True, text=True)


def build_install() -> None:
    proc = run(["bash", "/app/scripts/rebuild-bundlectl.sh"])
    assert proc.returncode == 0, proc.stdout + proc.stderr


def verify(name: str) -> subprocess.CompletedProcess[str]:
    return run([str(CLI), "verify", "--bundle", str(BUNDLES / name)])


def eval_bundle(name: str, seed: str, export: Path) -> subprocess.CompletedProcess[str]:
    inp = BUNDLES / name / "input" / "default.json"
    return run(
        [
            str(CLI),
            "eval",
            "--bundle",
            str(BUNDLES / name),
            "--seed",
            seed,
            "--input",
            str(inp),
            "--export",
            str(export),
        ]
    )


def assert_trace_matches(got: dict, ref: dict) -> None:
    assert got["allow"] == ref["allow"]
    assert got["trace"]["steps"] == ref["trace"]["steps"]
    got_b = {b["ref"]: b["value"] for b in got["trace"]["bindings"]}
    ref_b = {b["ref"]: b["value"] for b in ref["trace"]["bindings"]}
    assert set(got_b) == set(ref_b)
    for ref_name, rval in ref_b.items():
        assert got_b[ref_name] == rval


class TestBundlectl:
    def setup_method(self) -> None:
        OUTPUT.mkdir(parents=True, exist_ok=True)
        STATE.mkdir(parents=True, exist_ok=True)
        build_install()

    def test_fixture_integrity(self) -> None:
        for name in GOOD + TRAPS:
            assert (BUNDLES / name / "MANIFEST.json").is_file()
            assert (BUNDLES / name / ".signatures.json").is_file()

    @pytest.mark.parametrize("name", GOOD)
    def test_verify_good_bundles(self, name: str) -> None:
        proc = verify(name)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        out = json.loads(proc.stdout)
        ref = reference_verify(BUNDLES / name)
        assert out["ok"] is True
        assert out["chain_root"] == ref["chain_root"]
        assert out["digests"] == ref["digests"]

    @pytest.mark.parametrize("name", TRAPS)
    def test_verify_trap_bundles_fail(self, name: str) -> None:
        proc = verify(name)
        assert proc.returncode != 0

    def test_revoked_signer_flags_revoked(self) -> None:
        proc = verify("revoked-signer")
        assert proc.returncode != 0
        out = json.loads(proc.stdout)
        assert out.get("revoked") is True

    @pytest.mark.parametrize("seed", SEEDS)
    @pytest.mark.parametrize("name", ["allow-basic", "multi-scope", "path-normalize"])
    def test_eval_allow_with_trace(self, seed: str, name: str) -> None:
        export = OUTPUT / f"eval-{name}-{seed}.json"
        proc = eval_bundle(name, seed, export)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = json.loads(proc.stdout)
        exported = json.loads(export.read_text(encoding="utf-8"))
        assert got == exported
        ref = reference_eval(BUNDLES / name, seed, BUNDLES / name / "input" / "default.json")
        assert_trace_matches(got, ref)
        assert got["allow"] == ref["allow"]

    @pytest.mark.parametrize("seed", SEEDS)
    def test_eval_deny_edge(self, seed: str) -> None:
        export = OUTPUT / f"deny-{seed}.json"
        proc = eval_bundle("deny-edge", seed, export)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = json.loads(proc.stdout)
        ref = reference_eval(
            BUNDLES / "deny-edge", seed, BUNDLES / "deny-edge" / "input" / "default.json"
        )
        assert_trace_matches(got, ref)
        assert got["allow"] is False

    def test_eval_seed_changes_threshold_outcome(self) -> None:
        """Seed substitution must change allow when threshold crosses data.foo."""
        # allow-basic data.foo=950; tag_numeric ranges 100-999
        results = []
        for seed in SEEDS:
            export = OUTPUT / f"seed-outcome-{seed}.json"
            proc = eval_bundle("allow-basic", seed, export)
            assert proc.returncode == 0
            results.append(json.loads(proc.stdout)["allow"])
        # All seeds should allow for foo=950 with tags in 100-999, but values differ in threshold
        thresholds = []
        for seed in SEEDS:
            export = OUTPUT / f"seed-outcome-{seed}.json"
            got = json.loads(export.read_text(encoding="utf-8"))
            thr = next(b["value"] for b in got["trace"]["bindings"] if b["ref"] == "input.threshold")
            thresholds.append(thr)
        assert len({json.dumps(t) for t in thresholds}) == len(SEEDS)

    def test_verify_rejects_seed_flag(self) -> None:
        proc = run(
            [str(CLI), "verify", "--bundle", str(BUNDLES / "allow-basic"), "--seed", "3"]
        )
        assert proc.returncode != 0

    def test_bad_scope_chain_reports_scope_reason(self) -> None:
        proc = verify("bad-scope-chain")
        assert proc.returncode != 0
        out = json.loads(proc.stdout)
        assert out["ok"] is False
        assert "scope" in out.get("reason", "").lower()

    def test_chain_order_matches_reference_not_manifest(self) -> None:
        proc = verify("multi-scope")
        assert proc.returncode == 0, proc.stdout + proc.stderr
        out = json.loads(proc.stdout)
        ref = reference_verify(BUNDLES / "multi-scope")
        assert out["chain_root"] == ref["chain_root"]

    def test_path_normalize_canonical_member(self) -> None:
        proc = verify("path-normalize")
        assert proc.returncode == 0, proc.stdout + proc.stderr
        out = json.loads(proc.stdout)
        assert "data/data.json" in out["digests"]
        assert "./data/../data/data.json" not in out["digests"]

    def test_tampered_member_fails_verify(self) -> None:
        proc = verify("tampered-member")
        assert proc.returncode != 0

    def test_preview_staging_ledger_written_on_verify(self) -> None:
        proc = verify("allow-basic")
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert PREVIEW_LEDGER.is_file(), "/app/state/preview-ledger.json missing"
        ledger = json.loads(PREVIEW_LEDGER.read_text(encoding="utf-8"))
        assert ledger["order"] == sorted(ledger["order"])
        assert "data/data.json" in ledger["order"]

    def test_staging_snapshot_lex_order_multi_scope(self) -> None:
        proc = verify("multi-scope")
        assert proc.returncode == 0, proc.stdout + proc.stderr
        ledger = json.loads(PREVIEW_LEDGER.read_text(encoding="utf-8"))
        data_paths = [p for p in ledger["order"] if p.startswith("data/")]
        assert data_paths == sorted(data_paths)
        assert data_paths != ["data/data.json", "data/z-extra.json", "data/a-extra.json"]

    def test_eval_audit_records_binding_count(self) -> None:
        export = OUTPUT / "audit-check.json"
        proc = eval_bundle("allow-basic", "3", export)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        assert EVAL_AUDIT.is_file(), "/app/state/eval-audit.json missing"
        audit = json.loads(EVAL_AUDIT.read_text(encoding="utf-8"))
        ref = reference_eval(
            BUNDLES / "allow-basic", "3", BUNDLES / "allow-basic" / "input" / "default.json"
        )
        assert audit["binding_count"] == len(ref["trace"]["bindings"])
        assert audit["seed"] == "3"

    def test_verify_rejects_path_escape(self) -> None:
        proc = verify("path-escape")
        assert proc.returncode != 0

    def test_state_artifact_paths_created(self) -> None:
        verify("allow-basic")
        assert PREVIEW_LEDGER.is_file()
        export = OUTPUT / "state-paths.json"
        eval_bundle("allow-basic", "7", export)
        assert EVAL_AUDIT.is_file()
        audit = json.loads(EVAL_AUDIT.read_text(encoding="utf-8"))
        assert audit["seed"] == "7"

    def test_tb3_hidden_fixture_directory_present(self) -> None:
        assert TB3_BUNDLES.is_dir()
        assert (TB3_BUNDLES / "ledger-trap").is_dir()

    def test_tb3_hidden_ledger_trap_verify(self) -> None:
        bundle_dir = TB3_BUNDLES / "ledger-trap"
        proc = run([str(CLI), "verify", "--bundle", str(bundle_dir)])
        assert proc.returncode == 0, proc.stdout + proc.stderr
        out = json.loads(proc.stdout)
        ref = reference_verify(bundle_dir)
        assert out["chain_root"] == ref["chain_root"]

    def test_partial_digest_fix_still_fails_eval_trace(self) -> None:
        stubs = Path(__file__).parent / "stubs"
        shutil.copy(stubs / "golden_digest.go", APP / "internal/verify/digest.go")
        shutil.copy(stubs / "broken_trace.go", APP / "internal/eval/trace.go")
        build_install()
        export = OUTPUT / "partial-eval.json"
        proc = eval_bundle("allow-basic", "3", export)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = json.loads(proc.stdout)
        ref = reference_eval(
            BUNDLES / "allow-basic", "3", BUNDLES / "allow-basic" / "input" / "default.json"
        )
        with pytest.raises(AssertionError):
            assert_trace_matches(got, ref)

    def test_partial_eval_fix_still_fails_verify(self) -> None:
        stubs = Path(__file__).parent / "stubs"
        shutil.copy(stubs / "broken_digest.go", APP / "internal/verify/digest.go")
        shutil.copy(stubs / "golden_trace.go", APP / "internal/eval/trace.go")
        build_install()
        proc = verify("multi-scope")
        assert proc.returncode != 0

    def test_partial_ingest_staging_fix_still_fails_verify(self) -> None:
        stubs = Path(__file__).parent / "stubs"
        shutil.copy(stubs / "golden_preview_ledger.go", APP / "internal/bundle/preview_ledger.go")
        shutil.copy(stubs / "broken_digest.go", APP / "internal/verify/digest.go")
        build_install()
        proc = verify("multi-scope")
        assert proc.returncode != 0
