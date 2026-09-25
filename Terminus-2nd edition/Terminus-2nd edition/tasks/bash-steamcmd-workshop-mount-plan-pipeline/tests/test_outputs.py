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
TB3_ROOT = Path("/opt/verifier-fixtures/workshop")
SEED = os.environ.get("VERIFIER_SEED", "bash-steamcmd-workshop-mount-plan-pipeline")

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


def write_manifest(tmp: Path, name: str, body: str) -> Path:
    manifest_dir = tmp / name
    manifest_dir.mkdir(parents=True, exist_ok=True)
    (manifest_dir / "manifest.vdf").write_text(body, encoding="utf-8")
    return manifest_dir


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

    def test_staging_digest_binds_across_varied_epochs(self) -> None:
        """Across varied epochs, staging-meta.parsed_sha256 must bind the staged TSV bytes."""
        epochs = [
            WORKSHOP / "001-linear",
            WORKSHOP / "002-semver",
            WORKSHOP / "003-optional",
            WORKSHOP / "007-optional-satisfied",
        ]
        for fixture in epochs:
            reset_state()
            proc = run_plan(fixture)
            assert proc.returncode == 0, fixture.name + ": " + proc.stderr + proc.stdout
            lines = STAGING_TSV.read_text(encoding="utf-8").splitlines()
            assert lines == parsed_lines_for_manifest(fixture)
            meta = json.loads(STAGING_META.read_text(encoding="utf-8"))
            assert meta == reference_staging_meta(lines)
            blob = STAGING_TSV.read_bytes()
            assert meta["parsed_sha256"] == hashlib.sha256(blob).hexdigest()

    def test_staging_snapshot_replaced_across_epochs(self) -> None:
        """A later epoch must fully replace the prior staging snapshot and meta digest."""
        first = WORKSHOP / "001-linear"
        second = WORKSHOP / "003-optional"
        proc1 = run_plan(first)
        assert proc1.returncode == 0, proc1.stderr + proc1.stdout
        first_lines = STAGING_TSV.read_text(encoding="utf-8").splitlines()
        proc2 = run_plan(second)
        assert proc2.returncode == 0, proc2.stderr + proc2.stdout
        second_lines = STAGING_TSV.read_text(encoding="utf-8").splitlines()
        assert second_lines == parsed_lines_for_manifest(second)
        assert second_lines != first_lines
        meta = json.loads(STAGING_META.read_text(encoding="utf-8"))
        assert meta == reference_staging_meta(second_lines)

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

    def test_failed_run_footer_run_seq_one_without_prior_state(self) -> None:
        """With no prior run-seq.json, a failing plan still seals footer.run_seq=1 and skips persist."""
        fixture = WORKSHOP / "005-missing"
        assert not RUN_SEQ.exists()
        proc = run_plan(fixture)
        assert proc.returncode == 1, proc.stderr + proc.stdout
        got = load_plan()
        assert got["footer"]["run_seq"] == 1
        assert not RUN_SEQ.exists()

    def test_failed_cycle_run_footer_run_seq_one_without_prior_state(self) -> None:
        """With no prior run-seq.json, an exit-2 cycle plan seals footer.run_seq=1 without persist."""
        fixture = WORKSHOP / "004-cycle"
        assert not RUN_SEQ.exists()
        proc = run_plan(fixture)
        assert proc.returncode == 2, proc.stderr + proc.stdout
        got = load_plan()
        assert got["footer"]["run_seq"] == 1
        assert got["mount_order"] == []
        assert not RUN_SEQ.exists()

    def test_failed_run_retains_prior_seq_without_increment(self) -> None:
        """After a successful seq=1 seal, a later failing epoch keeps footer and on-disk seq at 1."""
        ok = WORKSHOP / "001-linear"
        bad = WORKSHOP / "005-missing"
        proc1 = run_plan(ok)
        assert proc1.returncode == 0, proc1.stderr + proc1.stdout
        stored_before = json.loads(RUN_SEQ.read_text(encoding="utf-8"))
        assert stored_before["seq"] == 1
        proc2 = run_plan(bad)
        assert proc2.returncode == 1, proc2.stderr + proc2.stdout
        got = load_plan()
        assert got["footer"]["run_seq"] == 1
        stored_after = json.loads(RUN_SEQ.read_text(encoding="utf-8"))
        assert stored_after == stored_before

    def test_kahn_batch_ascii_order_end_to_end(self) -> None:
        """Ready-batch ASCII sorting must order independent roots before dependents."""
        body = (
            '"WorkshopCollection"\n'
            "{\n"
            '\t"mods"\n'
            "\t{\n"
            '\t\t"mod_z"\n'
            "\t\t{\n"
            '\t\t\t"version"\t"1.0.0"\n'
            "\t\t}\n"
            '\t\t"mod_a"\n'
            "\t\t{\n"
            '\t\t\t"version"\t"1.0.0"\n'
            "\t\t}\n"
            '\t\t"mod_m"\n'
            "\t\t{\n"
            '\t\t\t"version"\t"1.0.0"\n'
            "\t\t}\n"
            '\t\t"mod_leaf"\n'
            "\t\t{\n"
            '\t\t\t"version"\t"1.0.0"\n'
            "\t\t\t\"depends\"\n"
            "\t\t\t{\n"
            '\t\t\t\t"mod_z"\n'
            "\t\t\t\t{\n"
            '\t\t\t\t\t"version"\t">=1.0.0"\n'
            '\t\t\t\t\t"optional"\t"0"\n'
            "\t\t\t\t}\n"
            '\t\t\t\t"mod_a"\n'
            "\t\t\t\t{\n"
            '\t\t\t\t\t"version"\t">=1.0.0"\n'
            '\t\t\t\t\t"optional"\t"0"\n'
            "\t\t\t\t}\n"
            '\t\t\t\t"mod_m"\n'
            "\t\t\t\t{\n"
            '\t\t\t\t\t"version"\t">=1.0.0"\n'
            '\t\t\t\t\t"optional"\t"0"\n'
            "\t\t\t\t}\n"
            "\t\t\t}\n"
            "\t\t}\n"
            "\t}\n"
            "}\n"
        )
        cfg = load_config(CONFIG)
        with tempfile.TemporaryDirectory() as tmp:
            manifest_dir = write_manifest(Path(tmp), "kahn-batch", body)
            expected, expected_rc = build_plan(manifest_dir, cfg)
            proc = run_plan(manifest_dir)
            assert proc.returncode == expected_rc, proc.stderr + proc.stdout
            got = load_plan()
            assert got == expected
            assert got["mount_order"] == ["mod_a", "mod_m", "mod_z", "mod_leaf"]

    def test_semver_failure_and_numeric_admit_end_to_end(self) -> None:
        """Numeric semver must admit 1.10 under >=1.2 and reject 1.1 under >=1.2."""
        ok_body = (
            '"WorkshopCollection"\n'
            "{\n"
            '\t"mods"\n'
            "\t{\n"
            '\t\t"leaf"\n'
            "\t\t{\n"
            '\t\t\t"version"\t"1.0.0"\n'
            "\t\t\t\"depends\"\n"
            "\t\t\t{\n"
            '\t\t\t\t"hub"\n'
            "\t\t\t\t{\n"
            '\t\t\t\t\t"version"\t">=1.2.0"\n'
            '\t\t\t\t\t"optional"\t"0"\n'
            "\t\t\t\t}\n"
            "\t\t\t}\n"
            "\t\t}\n"
            '\t\t"hub"\n'
            "\t\t{\n"
            '\t\t\t"version"\t"1.10.0"\n'
            "\t\t}\n"
            "\t}\n"
            "}\n"
        )
        bad_body = ok_body.replace('"1.10.0"', '"1.1.0"')
        cfg = load_config(CONFIG)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ok_dir = write_manifest(root, "semver-ok", ok_body)
            bad_dir = write_manifest(root, "semver-bad", bad_body)
            expected_ok, rc_ok = build_plan(ok_dir, cfg)
            proc_ok = run_plan(ok_dir)
            assert proc_ok.returncode == rc_ok, proc_ok.stderr + proc_ok.stdout
            assert load_plan() == expected_ok
            assert expected_ok["mount_order"] == ["hub", "leaf"]

            reset_state()
            expected_bad, rc_bad = build_plan(bad_dir, cfg)
            proc_bad = run_plan(bad_dir)
            assert proc_bad.returncode == rc_bad == 1, proc_bad.stderr + proc_bad.stdout
            got_bad = load_plan()
            assert got_bad == expected_bad
            assert got_bad["errors"]
            assert "semver constraint failed" in got_bad["errors"][0]

    def test_diamond_mount_order_end_to_end(self) -> None:
        """Diamond graphs must emit dependency-first order with ASCII-ready batches."""
        body = (
            '"WorkshopCollection"\n'
            "{\n"
            '\t"mods"\n'
            "\t{\n"
            '\t\t"hub"\n'
            "\t\t{\n"
            '\t\t\t"version"\t"1.0.0"\n'
            "\t\t}\n"
            '\t\t"branch_b"\n'
            "\t\t{\n"
            '\t\t\t"version"\t"1.0.0"\n'
            "\t\t\t\"depends\"\n"
            "\t\t\t{\n"
            '\t\t\t\t"hub"\n'
            "\t\t\t\t{\n"
            '\t\t\t\t\t"version"\t">=1.0.0"\n'
            '\t\t\t\t\t"optional"\t"0"\n'
            "\t\t\t\t}\n"
            "\t\t\t}\n"
            "\t\t}\n"
            '\t\t"branch_a"\n'
            "\t\t{\n"
            '\t\t\t"version"\t"1.0.0"\n'
            "\t\t\t\"depends\"\n"
            "\t\t\t{\n"
            '\t\t\t\t"hub"\n'
            "\t\t\t\t{\n"
            '\t\t\t\t\t"version"\t">=1.0.0"\n'
            '\t\t\t\t\t"optional"\t"0"\n'
            "\t\t\t\t}\n"
            "\t\t\t}\n"
            "\t\t}\n"
            '\t\t"tip"\n'
            "\t\t{\n"
            '\t\t\t"version"\t"1.0.0"\n'
            "\t\t\t\"depends\"\n"
            "\t\t\t{\n"
            '\t\t\t\t"branch_a"\n'
            "\t\t\t\t{\n"
            '\t\t\t\t\t"version"\t">=1.0.0"\n'
            '\t\t\t\t\t"optional"\t"0"\n'
            "\t\t\t\t}\n"
            '\t\t\t\t"branch_b"\n'
            "\t\t\t\t{\n"
            '\t\t\t\t\t"version"\t">=1.0.0"\n'
            '\t\t\t\t\t"optional"\t"0"\n'
            "\t\t\t\t}\n"
            "\t\t\t}\n"
            "\t\t}\n"
            "\t}\n"
            "}\n"
        )
        cfg = load_config(CONFIG)
        with tempfile.TemporaryDirectory() as tmp:
            manifest_dir = write_manifest(Path(tmp), "diamond", body)
            expected, expected_rc = build_plan(manifest_dir, cfg)
            proc = run_plan(manifest_dir)
            assert proc.returncode == expected_rc, proc.stderr + proc.stdout
            got = load_plan()
            assert got == expected
            assert got["mount_order"] == ["hub", "branch_a", "branch_b", "tip"]
            assert got["stats"]["edge_count"] == 4

    def test_cycle_path_varied_three_mod_end_to_end(self) -> None:
        """Varied three-mod cycle must emit dependency-first first-outgoing path."""
        body = (
            '"WorkshopCollection"\n'
            "{\n"
            '\t"mods"\n'
            "\t{\n"
            '\t\t"x_mod"\n'
            "\t\t{\n"
            '\t\t\t"version"\t"1.0.0"\n'
            "\t\t\t\"depends\"\n"
            "\t\t\t{\n"
            '\t\t\t\t"y_mod"\n'
            "\t\t\t\t{\n"
            '\t\t\t\t\t"version"\t">=1.0.0"\n'
            '\t\t\t\t\t"optional"\t"0"\n'
            "\t\t\t\t}\n"
            "\t\t\t}\n"
            "\t\t}\n"
            '\t\t"y_mod"\n'
            "\t\t{\n"
            '\t\t\t"version"\t"1.0.0"\n'
            "\t\t\t\"depends\"\n"
            "\t\t\t{\n"
            '\t\t\t\t"z_mod"\n'
            "\t\t\t\t{\n"
            '\t\t\t\t\t"version"\t">=1.0.0"\n'
            '\t\t\t\t\t"optional"\t"0"\n'
            "\t\t\t\t}\n"
            "\t\t\t}\n"
            "\t\t}\n"
            '\t\t"z_mod"\n'
            "\t\t{\n"
            '\t\t\t"version"\t"1.0.0"\n'
            "\t\t\t\"depends\"\n"
            "\t\t\t{\n"
            '\t\t\t\t"x_mod"\n'
            "\t\t\t\t{\n"
            '\t\t\t\t\t"version"\t">=1.0.0"\n'
            '\t\t\t\t\t"optional"\t"0"\n'
            "\t\t\t\t}\n"
            "\t\t\t}\n"
            "\t\t}\n"
            "\t}\n"
            "}\n"
        )
        cfg = load_config(CONFIG)
        with tempfile.TemporaryDirectory() as tmp:
            manifest_dir = write_manifest(Path(tmp), "cycle-xyz", body)
            expected, expected_rc = build_plan(manifest_dir, cfg)
            proc = run_plan(manifest_dir)
            assert proc.returncode == expected_rc == 2, proc.stderr + proc.stdout
            got = load_plan()
            assert got == expected
            assert got["mount_order"] == []
            assert got["cycles"] == ["x_mod->z_mod->y_mod->x_mod"]

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

    def test_input_fingerprint_recorded_on_success(self) -> None:
        """Successful export must persist input_fingerprint in run-seq.json."""
        fixture = WORKSHOP / "001-linear"
        cfg = load_config(CONFIG)
        proc = run_plan(fixture)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        stored = json.loads(RUN_SEQ.read_text(encoding="utf-8"))
        assert stored["input_fingerprint"] == input_fingerprint(fixture, cfg)
