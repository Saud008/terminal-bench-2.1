"""Behavioral verifier for dosbox-plan remount lineage replay."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from reference_dosbox import (
    CATALOG,
    build_plan,
    build_seed_conf_text,
    build_seed_manifest,
    load_config,
)

APP = Path("/app")
CONFS = APP / "fixtures" / "confs"
CONFIG = APP / "config" / "plan.json"
OUTPUT = APP / "output" / "plan.json"
CLI = APP / "bin" / "dosbox-plan"
LIB_DIR = APP / "lib"
BROKEN_LIB = Path(__file__).resolve().parent / "broken_lib"
SEED = os.environ.get("VERIFIER_SEED", "dosbox-conf-remount-lineage-replay-repair")

LIB_FILES = ("conf_parse.sh", "section_order.sh", "remount.sh", "validate.sh")


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


def run_render(
    conf_dir: Path,
    profile: str = "default",
    output: Path = OUTPUT,
    config_path: Path = CONFIG,
) -> subprocess.CompletedProcess:
    return _run(
        [
            str(CLI),
            "render",
            "--conf-dir",
            str(conf_dir),
            "--profile",
            profile,
            "--config",
            str(config_path),
            "--output",
            str(output),
        ]
    )


def load_plan(path: Path = OUTPUT) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def snapshot_libs() -> dict[str, str]:
    return {name: (LIB_DIR / name).read_text(encoding="utf-8") for name in LIB_FILES}


def restore_libs(saved: dict[str, str]) -> None:
    for name, content in saved.items():
        (LIB_DIR / name).write_text(content, encoding="utf-8")


def install_libs(**patch: str) -> None:
    alias = {
        "conf_parse_sh": "conf_parse.sh",
        "section_order_sh": "section_order.sh",
        "remount_sh": "remount.sh",
        "validate_sh": "validate.sh",
    }
    for key, broken_name in patch.items():
        target = alias.get(key, key)
        shutil.copy(BROKEN_LIB / broken_name, LIB_DIR / target)


class TestDosboxPlan:
    """Verifier tests for dosbox-plan render."""

    def setup_method(self) -> None:
        reset_state()

    @pytest.mark.parametrize("fixture_id", list(CATALOG.keys()), ids=list(CATALOG.keys()))
    def test_catalog_fixture_matches_reference(self, fixture_id: str) -> None:
        """Catalog fixtures must match independent reference output and exit code."""
        fixture_dir = CONFS / fixture_id
        cfg = load_config(CONFIG)
        expected, expected_rc = build_plan(fixture_dir, "default", cfg)
        proc = run_render(fixture_dir)
        assert proc.returncode == expected_rc, proc.stderr + proc.stdout
        got = load_plan()
        assert got == expected

    def test_missing_conf_dir_exits_nonzero(self) -> None:
        """Missing conf directory must exit 1."""
        proc = run_render(CONFS / "missing-fixture")
        assert proc.returncode == 1

    def test_missing_manifest_exits_one(self) -> None:
        """Missing manifest.txt must exit 1 with an error in output."""
        with tempfile.TemporaryDirectory() as tmp:
            conf_dir = Path(tmp) / "no-manifest"
            conf_dir.mkdir()
            proc = run_render(conf_dir)
            assert proc.returncode == 1
            got = load_plan()
            assert any("missing manifest" in err for err in got["errors"])

    def test_missing_listed_conf_exits_one(self) -> None:
        """Manifest referencing an absent conf file must exit 1."""
        with tempfile.TemporaryDirectory() as tmp:
            conf_dir = Path(tmp) / "bad-manifest"
            conf_dir.mkdir()
            (conf_dir / "manifest.txt").write_text("missing.conf\n", encoding="utf-8")
            proc = run_render(conf_dir)
            assert proc.returncode == 1
            got = load_plan()
            assert any("missing conf file" in err for err in got["errors"])

    def test_empty_manifest_exits_one(self) -> None:
        """Manifest with no conf filenames must exit 1."""
        with tempfile.TemporaryDirectory() as tmp:
            conf_dir = Path(tmp) / "empty-manifest"
            conf_dir.mkdir()
            (conf_dir / "manifest.txt").write_text("# only comments\n", encoding="utf-8")
            proc = run_render(conf_dir)
            assert proc.returncode == 1
            got = load_plan()
            assert any("empty manifest" in err for err in got["errors"])

    def test_seed_anti_hardcoding(self) -> None:
        """Seeded conf must match reference with section-order and imgmount traps."""
        cfg = load_config(CONFIG)
        with tempfile.TemporaryDirectory() as tmp:
            seed_dir = Path(tmp) / "seed-case"
            seed_dir.mkdir()
            (seed_dir / "manifest.txt").write_text(build_seed_manifest(), encoding="utf-8")
            (seed_dir / "seed.conf").write_text(build_seed_conf_text(SEED), encoding="utf-8")
            expected, expected_rc = build_plan(seed_dir, "default", cfg)
            proc = run_render(seed_dir)
            assert proc.returncode == expected_rc, proc.stderr + proc.stdout
            got = load_plan()
            assert got == expected
            if got["lineage"]:
                assert got["lineage"][0]["op"] in ("mount", "imgmount")
            digest = hashlib.sha256(json.dumps(got, sort_keys=True).encode()).hexdigest()
            raw = hashlib.sha256(build_seed_conf_text(SEED).encode()).hexdigest()
            assert digest != raw

    def test_002_config_precedence_drive_remap(self) -> None:
        """002 must remap D to E when config precedes autoexec replay."""
        fixture = CONFS / "002-config-precedence"
        cfg = load_config(CONFIG)
        expected, expected_rc = build_plan(fixture, "default", cfg)
        proc = run_render(fixture)
        assert proc.returncode == expected_rc
        got = load_plan()
        assert len(got["lineage"]) == 1
        assert got["lineage"][0]["drive"] == "E"
        assert got == expected

    def test_003_imgmount_path_and_drive_remap(self) -> None:
        """003 must remap imgmount drive and D: path prefix."""
        fixture = CONFS / "003-imgmount-remap"
        cfg = load_config(CONFIG)
        expected, expected_rc = build_plan(fixture, "default", cfg)
        proc = run_render(fixture)
        assert proc.returncode == expected_rc
        got = load_plan()
        assert got["lineage"][0]["drive"] == "F"
        assert got["lineage"][0]["path"].startswith("F:")
        assert got == expected

    def test_004_duplicate_stack_depth(self) -> None:
        """004 must stack duplicate C mounts with stack_depth 2."""
        proc = run_render(CONFS / "004-duplicate-stack")
        assert proc.returncode == 0
        got = load_plan()
        assert len(got["lineage"]) == 2
        assert got["stats"]["stack_depth"] == 2
        assert got["lineage"][0]["path"] != got["lineage"][1]["path"]

    def test_005_line_continuation_joins_path(self) -> None:
        """005 must join backslash continuation into one mount path."""
        proc = run_render(CONFS / "005-line-continuation")
        assert proc.returncode == 0
        got = load_plan()
        assert got["lineage"][0]["path"] == "/data/long/folder/game"

    def test_006_invalid_drive_exits_two(self) -> None:
        """006 must exit 2 on invalid drive letter."""
        proc = run_render(CONFS / "006-invalid-drive")
        assert proc.returncode == 2
        got = load_plan()
        assert any("invalid drive letter" in err for err in got["errors"])

    def test_008_interleaved_sections_global_config_first(self) -> None:
        """008 must apply config remap before both autoexec mounts despite interleaving."""
        fixture = CONFS / "008-interleaved-sections"
        cfg = load_config(CONFIG)
        expected, expected_rc = build_plan(fixture, "default", cfg)
        proc = run_render(fixture)
        assert proc.returncode == expected_rc
        got = load_plan()
        drives = [e["drive"] for e in got["lineage"]]
        assert drives == ["H", "H"]
        assert got == expected

    def test_partial_golden_section_order_only_still_fails(self) -> None:
        """Anti-cheat: section-order fix alone must not pass imgmount remap fixture."""
        saved = snapshot_libs()
        try:
            install_libs(
                section_order_sh="golden_section_order.sh",
                conf_parse_sh="broken_conf_parse.sh",
                remount_sh="broken_remount.sh",
                validate_sh="broken_validate.sh",
            )
            fixture = CONFS / "003-imgmount-remap"
            expected, _rc = build_plan(fixture, "default", load_config(CONFIG))
            run_render(fixture)
            got = load_plan()
            assert got != expected
        finally:
            restore_libs(saved)

    def test_partial_golden_remount_only_still_fails(self) -> None:
        """Anti-cheat: remount fix alone cannot fix line continuation parsing."""
        saved = snapshot_libs()
        try:
            install_libs(
                remount_sh="golden_remount.sh",
                conf_parse_sh="broken_conf_parse.sh",
                section_order_sh="broken_section_order.sh",
                validate_sh="broken_validate.sh",
            )
            fixture = CONFS / "005-line-continuation"
            expected, _rc = build_plan(fixture, "default", load_config(CONFIG))
            run_render(fixture)
            got = load_plan()
            assert got != expected
        finally:
            restore_libs(saved)

    def test_partial_golden_validate_only_still_fails(self) -> None:
        """Anti-cheat: validate fix alone must not pass config precedence."""
        saved = snapshot_libs()
        try:
            install_libs(
                validate_sh="golden_validate.sh",
                conf_parse_sh="broken_conf_parse.sh",
                section_order_sh="broken_section_order.sh",
                remount_sh="broken_remount.sh",
            )
            fixture = CONFS / "002-config-precedence"
            expected, _rc = build_plan(fixture, "default", load_config(CONFIG))
            run_render(fixture)
            got = load_plan()
            assert got != expected
        finally:
            restore_libs(saved)

    def test_partial_golden_conf_parse_only_still_fails(self) -> None:
        """Anti-cheat: conf_parse fix alone must not pass duplicate stack behavior."""
        saved = snapshot_libs()
        try:
            install_libs(
                conf_parse_sh="golden_conf_parse.sh",
                section_order_sh="broken_section_order.sh",
                remount_sh="broken_remount.sh",
                validate_sh="broken_validate.sh",
            )
            fixture = CONFS / "004-duplicate-stack"
            expected, _rc = build_plan(fixture, "default", load_config(CONFIG))
            run_render(fixture)
            got = load_plan()
            assert got != expected
        finally:
            restore_libs(saved)
