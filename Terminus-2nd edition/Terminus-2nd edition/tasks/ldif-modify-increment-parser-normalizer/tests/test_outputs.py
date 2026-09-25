"""Behavioral verifier for ldif-apply."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from reference_apply import materialize_ldif, reference_apply, reference_audit

APP = Path("/app")
CLI = "/usr/local/bin/ldif-apply"
FIXTURES = APP / "fixtures"
OUTPUT = APP / "output"
CATALOG = json.loads((FIXTURES / "catalog.json").read_text(encoding="utf-8"))
SEEDS = json.loads((FIXTURES / "seeds.json").read_text(encoding="utf-8"))["seeds"]
RESET = APP / "scripts" / "reset-state.sh"
CORE = APP / "crates/ldif-core" / "src"
BROKEN = Path("/opt/verifier-broken-ldif")
CANONICAL = Path("/tests/canonical_ldif")
MODULES = ("parser", "apply", "audit")
CANONICAL_FILES = {
    "parser": "canonical_token_parser.rs",
    "apply": "canonical_directory_apply.rs",
    "audit": "canonical_audit_log.rs",
}


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False)


def rebuild_ldif_apply() -> None:
    for mod in MODULES:
        (CORE / f"{mod}.rs").touch()
    proc = run(
        [
            "bash",
            "-lc",
            "cargo build --locked --release --bin ldif-apply && install -m 0755 target/release/ldif-apply /usr/local/bin/ldif-apply",
        ]
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout


def restore_broken() -> None:
    for mod in MODULES:
        shutil.copy2(BROKEN / f"{mod}.rs", CORE / f"{mod}.rs")


def install_boundary_sources(faulty: set[str]) -> None:
    """Swap ldif-core module files per /app/docs/ldif-core-public-api.md."""
    for mod in MODULES:
        dest = CORE / f"{mod}.rs"
        if mod in faulty:
            shutil.copy2(BROKEN / f"{mod}.rs", dest)
        else:
            shutil.copy2(CANONICAL / CANONICAL_FILES[mod], dest)


def reset() -> None:
    proc = run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def log_path(name: str) -> Path:
    entry = next(s for s in CATALOG["scenarios"] if s["name"] == name)
    return FIXTURES / entry["source"]


def write_materialized(name: str, seed: str) -> Path:
    dest = OUTPUT / f"{name}-{seed}.ldif"
    dest.write_text(materialize_ldif(log_path(name), seed), encoding="utf-8")
    return dest


def apply_cli(name: str, seed: str) -> subprocess.CompletedProcess[str]:
    ldif_path = write_materialized(name, seed)
    export_path = OUTPUT / f"{name}-{seed}.json"
    audit_db = OUTPUT / f"audit-{name}-{seed}.db"
    return run(
        [
            CLI,
            "apply",
            "--input",
            str(ldif_path),
            "--seed",
            seed,
            "--export",
            str(export_path),
            "--audit-db",
            str(audit_db),
        ]
    )


def load_export(name: str, seed: str) -> dict:
    return json.loads((OUTPUT / f"{name}-{seed}.json").read_text(encoding="utf-8"))


def audit_query_cli(name: str, seed: str) -> subprocess.CompletedProcess[str]:
    audit_db = OUTPUT / f"audit-{name}-{seed}.db"
    export_path = OUTPUT / f"audit-{name}-{seed}.json"
    return run(
        [
            CLI,
            "audit-query",
            "--audit-db",
            str(audit_db),
            "--seed",
            seed,
            "--export",
            str(export_path),
        ]
    )


@pytest.fixture(autouse=True)
def _reset_output() -> None:
    reset()


class TestLdifScenarioParity:
    @pytest.mark.parametrize("seed", SEEDS)
    @pytest.mark.parametrize("scenario_name", [s["name"] for s in CATALOG["scenarios"]])
    def test_ldif_export_parity(self, scenario_name: str, seed: str) -> None:
        """Each catalog LDIF must match the independent expectation engine."""
        expected = reference_apply(log_path(scenario_name), seed)
        proc = apply_cli(scenario_name, seed)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        assert load_export(scenario_name, seed) == expected

    @pytest.mark.parametrize("seed", SEEDS)
    @pytest.mark.parametrize("scenario_name", [s["name"] for s in CATALOG["scenarios"]])
    def test_ldif_audit_trail_parity(self, scenario_name: str, seed: str) -> None:
        """Audit SQLite rows must match the independent expectation engine."""
        expected = reference_audit(log_path(scenario_name), seed)
        proc_apply = apply_cli(scenario_name, seed)
        assert proc_apply.returncode == 0, proc_apply.stderr or proc_apply.stdout
        proc = audit_query_cli(scenario_name, seed)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = json.loads((OUTPUT / f"audit-{scenario_name}-{seed}.json").read_text(encoding="utf-8"))
        assert got == expected


class TestLdifFocusedSemantics:
    def test_modify_sequence_changes_attributes(self) -> None:
        """Modify operation file order must change the final attribute set."""
        seed = SEEDS[0]
        expected = reference_apply(log_path("modify-op-order"), seed)
        proc = apply_cli("modify-op-order", seed)
        assert proc.returncode == 0
        got = load_export("modify-op-order", seed)
        assert got == expected
        entry = next(e for e in got["entries"] if e["dn"] == "cn=Member,dc=example,dc=com")
        assert entry["attributes"]["cn"] == ["Updated Member"]
        assert "description" not in entry["attributes"]

    def test_unpadded_base64_token(self) -> None:
        """Unpadded base64 attributes must decode correctly."""
        seed = SEEDS[0]
        expected = reference_apply(log_path("base64-token"), seed)
        proc = apply_cli("base64-token", seed)
        assert proc.returncode == 0
        got = load_export("base64-token", seed)
        assert got == expected
        entry = got["entries"][0]
        assert entry["attributes"]["apptoken"] == ["secret-token"]

    def test_expectation_engine_standalone(self) -> None:
        """Expectation engine must apply LDIF without invoking ldif-apply."""
        doc = reference_apply(log_path("multi-record"), SEEDS[0])
        assert len(doc["entries"]) == 1
        assert doc["entries"][0]["dn"] == "cn=A,dc=example,dc=com"


class TestLdifModuleFaultInjection:
    def test_faulty_token_parser_breaks_unfold(self) -> None:
        """Broken parser.rs (unfold_lines) must fail even when apply/audit are canonical."""
        install_boundary_sources({"parser"})
        rebuild_ldif_apply()
        proc = apply_cli("continuation-fold", SEEDS[0])
        assert proc.returncode == 0
        got = load_export("continuation-fold", SEEDS[0])
        expected = reference_apply(log_path("continuation-fold"), SEEDS[0])
        assert got != expected
        restore_broken()
        rebuild_ldif_apply()

    def test_faulty_token_parser_breaks_base64(self) -> None:
        """Broken parser.rs (decode_value) must fail even when apply/audit are canonical."""
        install_boundary_sources({"parser"})
        rebuild_ldif_apply()
        proc = apply_cli("base64-token", SEEDS[0])
        assert proc.returncode == 0
        got = load_export("base64-token", SEEDS[0])
        expected = reference_apply(log_path("base64-token"), SEEDS[0])
        assert got != expected
        restore_broken()
        rebuild_ldif_apply()

    def test_faulty_directory_apply_breaks_modify_order(self) -> None:
        """Broken apply.rs must fail even when parser/audit are canonical."""
        install_boundary_sources({"apply"})
        rebuild_ldif_apply()
        proc = apply_cli("modify-op-order", SEEDS[0])
        assert proc.returncode == 0
        got = load_export("modify-op-order", SEEDS[0])
        expected = reference_apply(log_path("modify-op-order"), SEEDS[0])
        assert got != expected
        restore_broken()
        rebuild_ldif_apply()

    def test_faulty_directory_apply_breaks_add_replace(self) -> None:
        """Broken apply.rs (add DN replace) must fail even when parser/audit are canonical."""
        install_boundary_sources({"apply"})
        rebuild_ldif_apply()
        proc = apply_cli("add-replace-dn", SEEDS[0])
        assert proc.returncode == 0
        got = load_export("add-replace-dn", SEEDS[0])
        expected = reference_apply(log_path("add-replace-dn"), SEEDS[0])
        assert got != expected
        restore_broken()
        rebuild_ldif_apply()

    def test_faulty_directory_apply_breaks_value_delete(self) -> None:
        """Broken apply.rs (value delete) must fail even when parser/audit are canonical."""
        install_boundary_sources({"apply"})
        rebuild_ldif_apply()
        proc = apply_cli("delete-value-vs-attr", SEEDS[0])
        assert proc.returncode == 0
        got = load_export("delete-value-vs-attr", SEEDS[0])
        expected = reference_apply(log_path("delete-value-vs-attr"), SEEDS[0])
        assert got != expected
        restore_broken()
        rebuild_ldif_apply()
