"""Verifier for portage-ebuild-phase-src-install-qa-hook-order-repair (single-step)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from reference_ebuild import (
    count_dirs_not_0755,
    ledger_records,
    ledger_status,
    load_trace,
    package_root,
    reference_setuid_ok,
    reference_trace_ok,
    reset_state,
    run_full,
    run_src_install,
    symlink_resolves_inside,
)

# Phase CLI is driven through helpers that wrap run([...]) CompletedProcess calls.
CATALOG = json.loads((Path(__file__).parent / "catalog.json").read_text(encoding="utf-8"))
DEMO = Path(CATALOG["demo_suid"])
LINKFARM = Path(CATALOG["linkfarm"])
EXPECTED = CATALOG["expected_trace_prefix"]
MERGE_FAIL = CATALOG["merge_fail"]
DIE_TRAP = CATALOG["die_trap"]


@pytest.fixture(autouse=True)
def mount_hidden_packages(monkeypatch: pytest.MonkeyPatch) -> None:
    hidden = Path(__file__).parent / "verifier-fixtures" / "packages"
    target = Path("/opt/verifier-fixtures/packages")
    target.mkdir(parents=True, exist_ok=True)
    if hidden.is_dir():
        for pkg in hidden.iterdir():
            if not pkg.is_dir():
                continue
            dest = target / pkg.name
            if dest.exists():
                continue
            for src_file in pkg.rglob("*"):
                rel = src_file.relative_to(pkg)
                out = dest / rel
                out.parent.mkdir(parents=True, exist_ok=True)
                if src_file.is_file():
                    out.write_bytes(src_file.read_bytes())
    monkeypatch.setenv(CATALOG["hidden_root_env"], str(target))
    reset_state()


class TestSrcInstall:
    def test_demo_suid_src_install_exits_zero(self, tmp_path: Path) -> None:
        """src_install on demo-suid exits successfully."""
        dest = tmp_path / "root-demo"
        proc = run_src_install(DEMO, dest)
        assert proc.returncode == 0, proc.stderr + proc.stdout

    def test_phase_trace_order_matches_contract(self, tmp_path: Path) -> None:
        """phase-trace lists normalize_d before qa_preflight per ebuild-phase-order.md."""
        dest = tmp_path / "root-trace"
        proc = run_src_install(DEMO, dest)
        assert proc.returncode == 0, proc.stderr
        assert Path("/app/state/phase-trace.json").is_file()
        steps = load_trace()
        assert reference_trace_ok(steps, EXPECTED), steps

    def test_normalize_before_first_qa_in_trace(self, tmp_path: Path) -> None:
        """normalize_d step index precedes first qa_preflight in trace."""
        dest = tmp_path / "root-order"
        run_src_install(LINKFARM, dest)
        steps = load_trace()
        assert "normalize_d" in steps and "qa_preflight" in steps
        assert steps.index("normalize_d") < steps.index("qa_preflight")

    def test_fperms_before_dosbin_in_trace(self, tmp_path: Path) -> None:
        """fperms runs before dosbin so setuid survives dosbin."""
        dest = tmp_path / "root-fperms"
        run_src_install(DEMO, dest)
        steps = load_trace()
        assert steps.index("fperms") < steps.index("dosbin")

    def test_demo_suid_setuid_bit_preserved(self, tmp_path: Path) -> None:
        """setuid bit remains on usr/bin/demosuid after src_install."""
        dest = tmp_path / "root-suid"
        proc = run_src_install(DEMO, dest)
        assert proc.returncode == 0, proc.stderr
        assert reference_setuid_ok(dest, "usr/bin/demosuid")

    def test_linkfarm_symlink_contained_in_dest(self, tmp_path: Path) -> None:
        """linkfarm symlink resolves inside destination root."""
        dest = tmp_path / "root-link"
        proc = run_src_install(LINKFARM, dest)
        assert proc.returncode == 0, proc.stderr
        link = dest / "usr/share/linkfarm/readme"
        assert link.is_symlink()
        assert symlink_resolves_inside(dest, link)

    def test_demo_symlink_contained_in_dest(self, tmp_path: Path) -> None:
        """demo-suid share link resolves inside destination root."""
        dest = tmp_path / "root-demo-link"
        proc = run_src_install(DEMO, dest)
        assert proc.returncode == 0, proc.stderr
        link = dest / "usr/share/demo-link"
        assert symlink_resolves_inside(dest, link)

    def test_directories_normalized_to_0755(self, tmp_path: Path) -> None:
        """All directories under D are mode 0755 after src_install."""
        dest = tmp_path / "root-dirs"
        proc = run_src_install(LINKFARM, dest)
        assert proc.returncode == 0, proc.stderr
        assert count_dirs_not_0755(dest) == 0

    def test_linkfarm_postflight_passes(self, tmp_path: Path) -> None:
        """linkfarm package completes qa_postflight without QA errors."""
        dest = tmp_path / "root-lf"
        proc = run_src_install(LINKFARM, dest)
        assert proc.returncode == 0, proc.stderr
        steps = load_trace()
        assert steps[-1] == "qa_postflight"


class TestFullMerge:
    def test_demo_suid_full_writes_merged_record(self, tmp_path: Path) -> None:
        """Successful full run on demo-suid appends merged ledger record."""
        dest = tmp_path / "demo-full"
        proc = run_full(DEMO, dest)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        assert Path("/app/state/merge-ledger.json").is_file()
        assert ledger_status("demo-suid") == "merged"

    def test_merge_fail_full_exits_nonzero(self, tmp_path: Path) -> None:
        """merge-fail-test src_test failure makes full run exit non-zero."""
        tree = package_root() / MERGE_FAIL
        dest = tmp_path / "mf"
        proc = run_full(tree, dest)
        assert proc.returncode != 0

    def test_merge_fail_writes_no_ledger_record(self, tmp_path: Path) -> None:
        """Failed src_test must not append a merge ledger record."""
        tree = package_root() / MERGE_FAIL
        dest = tmp_path / "mf-ledger"
        run_full(tree, dest)
        assert ledger_status(MERGE_FAIL) is None
        names = {r.get("package") for r in ledger_records()}
        assert MERGE_FAIL not in names

    def test_die_trap_full_exits_nonzero(self, tmp_path: Path) -> None:
        """die-trap subshell die aborts full run with non-zero exit."""
        tree = package_root() / DIE_TRAP
        dest = tmp_path / "die"
        proc = run_full(tree, dest)
        assert proc.returncode != 0

    def test_die_trap_writes_no_ledger_record(self, tmp_path: Path) -> None:
        """Subshell die failure must not write merge ledger entry."""
        tree = package_root() / DIE_TRAP
        dest = tmp_path / "die-ledger"
        run_full(tree, dest)
        assert ledger_status(DIE_TRAP) is None

    def test_hidden_packages_only_via_tb3_root(self) -> None:
        """Verifier hidden packages resolve through TB3_PACKAGE_ROOT."""
        root = package_root()
        assert (root / MERGE_FAIL / "manifest.json").is_file()
        assert (root / DIE_TRAP / "manifest.json").is_file()
        assert os.environ.get(CATALOG["hidden_root_env"]) == str(root)

    def test_verifier_fixtures_merge_fail_manifest(self) -> None:
        """Hidden merge-fail-test package exists under tests/verifier-fixtures."""
        hidden = Path(__file__).parent / "verifier-fixtures" / "packages" / MERGE_FAIL
        assert (hidden / "manifest.json").is_file()

    def test_verifier_fixtures_die_trap_manifest(self) -> None:
        """Hidden die-trap package exists under tests/verifier-fixtures."""
        hidden = Path(__file__).parent / "verifier-fixtures" / "packages" / DIE_TRAP
        assert (hidden / "manifest.json").is_file()

    def test_merged_record_has_eapi_field(self, tmp_path: Path) -> None:
        """Merged ledger records include integer eapi from manifest."""
        dest = tmp_path / "demo-eapi"
        run_full(DEMO, dest)
        records = [r for r in ledger_records() if r.get("package") == "demo-suid"]
        assert records and records[-1].get("eapi") == 8
