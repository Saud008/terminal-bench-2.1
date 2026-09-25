"""Behavioral verifier for workshop-plan dependency ordering."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from reference_plan import (
    build_plan,
    build_seed_manifest,
    input_fingerprint,
    load_config,
    parsed_lines_for_manifest,
    reference_staging_meta,
)

APP = Path("/app")
WORKSHOP = APP / "fixtures" / "workshop"
CONFIG = APP / "config" / "plan.json"
OUTPUT = APP / "output" / "plan.json"
CLI = APP / "bin" / "workshop-plan"
STAGING_TSV = APP / "state" / "parsed-manifest.tsv"
STAGING_META = APP / "state" / "staging-meta.json"
RUN_SEQ = APP / "state" / "run-seq.json"
DEPS_SH = APP / "lib" / "deps.sh"
TOPO_SH = APP / "lib" / "topo.sh"
STAGING_SH = APP / "lib" / "staging.sh"
EXPORT_SH = APP / "lib" / "export_plan.sh"
BROKEN_LIB = Path(__file__).resolve().parent / "broken_lib"
TB3_ROOT = Path("/opt/verifier-fixtures/workshop")
SEED = os.environ.get("VERIFIER_SEED", "bash-steamcmd-workshop-dependency-toposort-repair")

FIXTURES = sorted(WORKSHOP.iterdir())


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
        cwd=str(APP),
    )


def reset_state() -> None:
    proc = _run(["bash", str(APP / "scripts" / "reset-state.sh")])
    assert proc.returncode == 0, proc.stderr


def run_plan(
    manifest_dir: Path,
    output: Path = OUTPUT,
    config_path: Path = CONFIG,
) -> subprocess.CompletedProcess:
    return _run(
        [
            str(CLI),
            "plan",
            "--manifest-dir",
            str(manifest_dir),
            "--config",
            str(config_path),
            "--output",
            str(output),
        ]
    )


def load_plan(path: Path = OUTPUT) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def snapshot_libs() -> dict[str, str]:
    return {
        "deps": DEPS_SH.read_text(encoding="utf-8"),
        "topo": TOPO_SH.read_text(encoding="utf-8"),
        "staging": STAGING_SH.read_text(encoding="utf-8"),
        "export": EXPORT_SH.read_text(encoding="utf-8"),
        "ingest": (APP / "ingest" / "manifest_ingest.sh").read_text(encoding="utf-8"),
    }


def restore_libs(saved: dict[str, str]) -> None:
    DEPS_SH.write_text(saved["deps"], encoding="utf-8")
    TOPO_SH.write_text(saved["topo"], encoding="utf-8")
    STAGING_SH.write_text(saved["staging"], encoding="utf-8")
    EXPORT_SH.write_text(saved["export"], encoding="utf-8")
    (APP / "ingest" / "manifest_ingest.sh").write_text(saved["ingest"], encoding="utf-8")


def install_libs(
    deps_name: str,
    topo_name: str,
    staging_name: str = "broken_staging.sh",
    export_name: str = "broken_export_plan.sh",
    ingest_name: str | None = None,
) -> None:
    shutil.copy(BROKEN_LIB / deps_name, DEPS_SH)
    shutil.copy(BROKEN_LIB / topo_name, TOPO_SH)
    shutil.copy(BROKEN_LIB / staging_name, STAGING_SH)
    shutil.copy(BROKEN_LIB / export_name, EXPORT_SH)
    if ingest_name is not None:
        shutil.copy(BROKEN_LIB / ingest_name, APP / "ingest" / "manifest_ingest.sh")


class TestWorkshopPlan:
    """Verifier tests for workshop-plan."""

    def setup_method(self) -> None:
        reset_state()

    @pytest.mark.parametrize("fixture_dir", FIXTURES, ids=lambda p: p.name)
    def test_fixture_matches_reference(self, fixture_dir: Path) -> None:
        """Catalog fixtures must match independent reference plan and exit code."""
        cfg = load_config(CONFIG)
        expected, expected_rc = build_plan(fixture_dir, cfg)
        proc = run_plan(fixture_dir)
        assert proc.returncode == expected_rc, proc.stderr + proc.stdout
        got = load_plan()
        assert got == expected

    def test_missing_manifest_dir_exits_nonzero(self) -> None:
        """Missing manifest directory must exit 1."""
        reset_state()
        proc = run_plan(WORKSHOP / "missing-fixture")
        assert proc.returncode == 1

    def test_seed_anti_hardcoding(self) -> None:
        """Seeded manifest must match independent reference output."""
        cfg = load_config(CONFIG)
        with tempfile.TemporaryDirectory() as tmp:
            seed_dir = Path(tmp) / "seed-case"
            seed_dir.mkdir()
            (seed_dir / "manifest.vdf").write_text(build_seed_manifest(SEED), encoding="utf-8")
            expected, expected_rc = build_plan(seed_dir, cfg)
            proc = run_plan(seed_dir)
            assert proc.returncode == expected_rc, proc.stderr
            got = load_plan()
            assert got == expected
            assert "seed_hub" in got["mount_order"][0]
            digest = hashlib.sha256(json.dumps(got, sort_keys=True).encode()).hexdigest()
            raw = hashlib.sha256(build_seed_manifest(SEED).encode()).hexdigest()
            assert digest != raw

    def test_004_cycle_empty_mount_order(self) -> None:
        """004 must exit 2 with empty mount_order and contract cycle paths."""
        fixture = WORKSHOP / "004-cycle"
        cfg = load_config(CONFIG)
        expected, expected_rc = build_plan(fixture, cfg)
        proc = run_plan(fixture)
        assert proc.returncode == expected_rc, proc.stderr + proc.stdout
        got = load_plan()
        assert got["mount_order"] == []
        assert got["cycles"] == expected["cycles"]
        assert got["cycles"] == ["mod_a->mod_c->mod_b->mod_a"]

    def test_005_missing_dependency_error(self) -> None:
        """005 must record contract-formatted missing required dependency errors and exit 1."""
        fixture = WORKSHOP / "005-missing"
        cfg = load_config(CONFIG)
        expected, expected_rc = build_plan(fixture, cfg)
        proc = run_plan(fixture)
        assert proc.returncode == expected_rc, proc.stderr + proc.stdout
        got = load_plan()
        assert got["errors"] == expected["errors"]

    def test_include_optional_edges_false_omits_optional_resolution(self) -> None:
        """include_optional_edges false must ignore optional edges in stats."""
        fixture = WORKSHOP / "007-optional-satisfied"
        with tempfile.TemporaryDirectory() as tmp:
            cfg_path = Path(tmp) / "plan-no-optional.json"
            cfg_path.write_text(
                json.dumps(
                    {
                        "fail_on_missing": True,
                        "emit_on_cycle": False,
                        "include_optional_edges": False,
                    }
                ),
                encoding="utf-8",
            )
            cfg = load_config(cfg_path)
            expected, expected_rc = build_plan(fixture, cfg)
            proc = run_plan(fixture, config_path=cfg_path)
            assert proc.returncode == expected_rc, proc.stderr + proc.stdout
            got = load_plan()
            assert got == expected

    def test_ingest_stage_snapshot(self) -> None:
        """Ingest stage must commit parsed-manifest.tsv before dependency resolution."""
        fixture = WORKSHOP / "001-linear"
        proc = run_plan(fixture)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        expected_lines = parsed_lines_for_manifest(fixture)
        assert STAGING_TSV.read_text(encoding="utf-8").splitlines() == expected_lines

    def test_partial_golden_ingest_only_still_fails(self) -> None:
        """Anti-cheat: ingest-only fix must not pass export staging digest gate."""
        saved = snapshot_libs()
        try:
            install_libs(
                "golden_deps.sh",
                "golden_topo.sh",
                staging_name="golden_staging.sh",
                export_name="golden_export_plan.sh",
                ingest_name="broken_manifest_ingest.sh",
            )
            fixture = WORKSHOP / "001-linear"
            expected, _expected_rc = build_plan(fixture, load_config(CONFIG))
            proc = run_plan(fixture)
            assert proc.returncode != 0 or load_plan() != expected
        finally:
            restore_libs(saved)

    def test_staging_artifact_matches_reference(self) -> None:
        """Stage 2 must write parsed-manifest.tsv and staging-meta.json per staging-schema."""
        fixture = WORKSHOP / "001-linear"
        expected_lines = parsed_lines_for_manifest(fixture)
        expected_meta = reference_staging_meta(expected_lines)
        proc = run_plan(fixture)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        assert STAGING_TSV.is_file()
        assert STAGING_META.is_file()
        got_lines = STAGING_TSV.read_text(encoding="utf-8").splitlines()
        assert got_lines == expected_lines
        got_meta = json.loads(STAGING_META.read_text(encoding="utf-8"))
        assert got_meta == expected_meta

    def test_staging_digest_binds_export(self) -> None:
        """Export must reject when staging-meta digest does not match parsed-manifest.tsv."""
        fixture = WORKSHOP / "001-linear"
        proc = run_plan(fixture)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        STAGING_TSV.write_text("corrupt\n", encoding="utf-8")
        check = _run(
            [
                "bash",
                "-lc",
                (
                    "source /app/lib/export_plan.sh && "
                    "TOPO_ORDER=(alpha beta) && DEPS_ERRORS=() && TOPO_CYCLES=() && "
                    "export_plan_emit /app/output/plan.json "
                    f"{fixture} {fixture / 'manifest.vdf'} /app/config/plan.json 2 1 0"
                ),
            ]
        )
        assert check.returncode != 0, check.stderr + check.stdout

    def test_instruction_output_paths_exist(self) -> None:
        """Successful plan must write /app/output/plan.json and /app/state staging artifacts."""
        fixture = WORKSHOP / "001-linear"
        proc = run_plan(fixture)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        assert Path("/app/output/plan.json").is_file()
        assert Path("/app/state/parsed-manifest.tsv").is_file()
        assert Path("/app/state/staging-meta.json").is_file()
        assert Path("/app/state/run-seq.json").is_file()
        assert OUTPUT.is_file()
        assert STAGING_TSV.is_file()
        assert STAGING_META.is_file()
        assert RUN_SEQ.is_file()

    def test_run_seq_unchanged_on_idempotent_rerun(self) -> None:
        """Identical manifest inputs must keep run_seq stable across consecutive runs."""
        fixture = WORKSHOP / "001-linear"
        proc1 = run_plan(fixture)
        assert proc1.returncode == 0, proc1.stderr + proc1.stdout
        first = load_plan()
        proc2 = run_plan(fixture)
        assert proc2.returncode == 0, proc2.stderr + proc2.stdout
        second = load_plan()
        assert first == second
        assert second["footer"]["run_seq"] == 1
        assert json.loads(RUN_SEQ.read_text(encoding="utf-8"))["seq"] == 1

    def test_run_seq_increments_on_different_manifest(self) -> None:
        """Changing manifest contents must bump run_seq."""
        proc1 = run_plan(WORKSHOP / "001-linear")
        assert proc1.returncode == 0, proc1.stderr + proc1.stdout
        assert load_plan()["footer"]["run_seq"] == 1
        proc2 = run_plan(WORKSHOP / "003-optional")
        assert proc2.returncode == 0, proc2.stderr + proc2.stdout
        assert load_plan()["footer"]["run_seq"] == 2

    def test_tb3_hidden_fixture_directory_present(self) -> None:
        """Hidden verifier fixtures are mounted under /opt/verifier-fixtures/workshop."""
        assert TB3_ROOT.is_dir()

    def test_tb3_semver_trap_matches_reference(self) -> None:
        """Hidden semver trap must use numeric comparison, not ASCII ordering."""
        assert (TB3_ROOT / "tb3-semver-trap" / "manifest.vdf").is_file()
        with tempfile.TemporaryDirectory() as tmp:
            trap_dir = Path(tmp) / "tb3-semver-trap"
            trap_dir.mkdir()
            shutil.copy2(TB3_ROOT / "tb3-semver-trap" / "manifest.vdf", trap_dir / "manifest.vdf")
            cfg = load_config(CONFIG)
            expected, expected_rc = build_plan(trap_dir, cfg)
            proc = run_plan(trap_dir)
            assert proc.returncode == expected_rc, proc.stderr + proc.stdout
            assert load_plan() == expected
            assert expected["mount_order"] == ["tb3_hub", "tb3_leaf"]

    def test_tb3_four_mod_cycle_path(self) -> None:
        """Hidden four-mod cycle must emit dependency-first walk order."""
        assert (TB3_ROOT / "tb3-cycle-four" / "manifest.vdf").is_file()
        with tempfile.TemporaryDirectory() as tmp:
            trap_dir = Path(tmp) / "tb3-cycle-four"
            trap_dir.mkdir()
            shutil.copy2(TB3_ROOT / "tb3-cycle-four" / "manifest.vdf", trap_dir / "manifest.vdf")
            cfg = load_config(CONFIG)
            expected, expected_rc = build_plan(trap_dir, cfg)
            proc = run_plan(trap_dir)
            assert proc.returncode == expected_rc, proc.stderr + proc.stdout
            got = load_plan()
            assert got["cycles"] == expected["cycles"]
            assert got["cycles"] == ["tb3_a->tb3_d->tb3_c->tb3_b->tb3_a"]

    def test_partial_golden_deps_only_still_fails(self) -> None:
        """Anti-cheat: dependency fix alone must not pass linear mount order."""
        saved = snapshot_libs()
        try:
            install_libs(
                "golden_deps.sh",
                "broken_topo.sh",
                staging_name="golden_staging.sh",
                export_name="golden_export_plan.sh",
                ingest_name="golden_manifest_ingest.sh",
            )
            fixture = WORKSHOP / "001-linear"
            expected, _expected_rc = build_plan(fixture, load_config(CONFIG))
            proc = run_plan(fixture)
            assert proc.returncode == 0, proc.stderr
            got = load_plan()
            assert got != expected
        finally:
            restore_libs(saved)

    def test_partial_golden_topo_only_still_fails(self) -> None:
        """Anti-cheat: topo fix alone must not pass semver fixture reference."""
        saved = snapshot_libs()
        try:
            install_libs(
                "broken_deps.sh",
                "golden_topo.sh",
                staging_name="golden_staging.sh",
                export_name="golden_export_plan.sh",
                ingest_name="golden_manifest_ingest.sh",
            )
            fixture = WORKSHOP / "002-semver"
            expected, _expected_rc = build_plan(fixture, load_config(CONFIG))
            proc = run_plan(fixture)
            assert proc.returncode == 0, proc.stderr
            got = load_plan()
            assert got != expected
        finally:
            restore_libs(saved)

    def test_partial_golden_staging_only_still_fails(self) -> None:
        """Anti-cheat: staging fix alone must not pass export staging digest gate."""
        saved = snapshot_libs()
        try:
            install_libs(
                "golden_deps.sh",
                "golden_topo.sh",
                staging_name="broken_staging.sh",
                export_name="golden_export_plan.sh",
                ingest_name="golden_manifest_ingest.sh",
            )
            fixture = WORKSHOP / "003-optional"
            proc = run_plan(fixture)
            assert proc.returncode != 0, proc.stderr + proc.stdout
        finally:
            restore_libs(saved)

    def test_partial_golden_export_only_still_fails_tb3(self) -> None:
        """Anti-cheat: export-only fix must fail hidden semver trap."""
        saved = snapshot_libs()
        try:
            install_libs(
                "broken_deps.sh",
                "golden_topo.sh",
                staging_name="golden_staging.sh",
                export_name="golden_export_plan.sh",
                ingest_name="golden_manifest_ingest.sh",
            )
            with tempfile.TemporaryDirectory() as tmp:
                trap_dir = Path(tmp) / "tb3-semver-trap"
                trap_dir.mkdir()
                shutil.copy2(TB3_ROOT / "tb3-semver-trap" / "manifest.vdf", trap_dir / "manifest.vdf")
                expected, expected_rc = build_plan(trap_dir, load_config(CONFIG))
                proc = run_plan(trap_dir)
                got = load_plan() if OUTPUT.is_file() else {}
                assert got != expected or proc.returncode != expected_rc
        finally:
            restore_libs(saved)

    def test_input_fingerprint_recorded_on_success(self) -> None:
        """Successful export must persist input_fingerprint in run-seq.json."""
        fixture = WORKSHOP / "001-linear"
        cfg = load_config(CONFIG)
        proc = run_plan(fixture)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        stored = json.loads(RUN_SEQ.read_text(encoding="utf-8"))
        assert stored["input_fingerprint"] == input_fingerprint(fixture, cfg)

    def test_partial_golden_topo_only_still_fails_cycle_path(self) -> None:
        """Anti-cheat: topo-only fix must not emit contract cycle traversal."""
        saved = snapshot_libs()
        try:
            install_libs(
                "golden_deps.sh",
                "broken_topo.sh",
                staging_name="golden_staging.sh",
                export_name="golden_export_plan.sh",
                ingest_name="golden_manifest_ingest.sh",
            )
            fixture = WORKSHOP / "004-cycle"
            expected, _expected_rc = build_plan(fixture, load_config(CONFIG))
            proc = run_plan(fixture)
            assert proc.returncode == _expected_rc, proc.stderr
            got = load_plan()
            assert got.get("cycles") != expected.get("cycles")
        finally:
            restore_libs(saved)
