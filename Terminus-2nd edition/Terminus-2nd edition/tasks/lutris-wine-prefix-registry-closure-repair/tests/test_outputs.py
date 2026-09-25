"""Behavioral verifier for lutris-resolve registry closure."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from reference_resolve import (
    CATALOG,
    build_resolve,
    build_seed_registry_text,
    load_config,
)

APP = Path("/app")
REGISTRY = APP / "fixtures" / "registry"
CONFIG = APP / "config" / "resolve.json"
OUTPUT = APP / "output" / "resolve.json"
CLI = APP / "bin" / "lutris-resolve"
LIB_DIR = APP / "lib"
BROKEN_LIB = Path(__file__).resolve().parent / "broken_lib"
SEED = os.environ.get("VERIFIER_SEED", "lutris-wine-prefix-registry-closure-repair")

LIB_FILES = ("registry.sh", "closure.sh", "prefix.sh", "semver.sh")


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
        cwd=str(APP),
    )


def reset_state() -> None:
    proc = _run(["bash", str(APP / "scripts/reset-state.sh")])
    assert proc.returncode == 0, proc.stderr


def run_resolve(
    registry_dir: Path,
    root_slug: str,
    output: Path = OUTPUT,
    config_path: Path = CONFIG,
) -> subprocess.CompletedProcess:
    return _run(
        [
            str(CLI),
            "resolve",
            "--registry-dir",
            str(registry_dir),
            "--root-slug",
            root_slug,
            "--config",
            str(config_path),
            "--output",
            str(output),
        ]
    )


def load_resolve(path: Path = OUTPUT) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def snapshot_libs() -> dict[str, str]:
    return {name: (LIB_DIR / name).read_text(encoding="utf-8") for name in LIB_FILES}


def restore_libs(saved: dict[str, str]) -> None:
    for name, content in saved.items():
        (LIB_DIR / name).write_text(content, encoding="utf-8")


def install_libs(**patch: str) -> None:
    alias = {
        "registry_sh": "registry.sh",
        "closure_sh": "closure.sh",
        "prefix_sh": "prefix.sh",
        "semver_sh": "semver.sh",
    }
    for key, broken_name in patch.items():
        target = alias.get(key, key)
        shutil.copy(BROKEN_LIB / broken_name, LIB_DIR / target)


class TestLutrisResolve:
    """Verifier tests for lutris-resolve."""

    def setup_method(self) -> None:
        reset_state()

    @pytest.mark.parametrize(
        "fixture_id,root_slug",
        list(CATALOG.items()),
        ids=list(CATALOG.keys()),
    )
    def test_catalog_fixture_matches_reference(self, fixture_id: str, root_slug: str) -> None:
        """Catalog fixtures must match independent reference output and exit code."""
        fixture_dir = REGISTRY / fixture_id
        cfg = load_config(CONFIG)
        expected, expected_rc = build_resolve(fixture_dir, root_slug, cfg)
        proc = run_resolve(fixture_dir, root_slug)
        assert proc.returncode == expected_rc, proc.stderr + proc.stdout
        got = load_resolve()
        assert got == expected

    def test_missing_registry_dir_exits_nonzero(self) -> None:
        """Missing registry directory must exit 1."""
        proc = run_resolve(REGISTRY / "missing-fixture", "any-slug")
        assert proc.returncode == 1

    def test_seed_anti_hardcoding(self) -> None:
        """Seeded registry must match independent reference with symlink and semver traps."""
        cfg = load_config(CONFIG)
        with tempfile.TemporaryDirectory() as tmp:
            seed_dir = Path(tmp) / "seed-case"
            seed_dir.mkdir()
            (seed_dir / "registry.yml").write_text(
                build_seed_registry_text(SEED), encoding="utf-8"
            )
            expected, expected_rc = build_resolve(seed_dir, "seed-game", cfg)
            proc = run_resolve(seed_dir, "seed-game")
            assert proc.returncode == expected_rc, proc.stderr + proc.stdout
            got = load_resolve()
            assert got == expected
            assert got["runner"] and got["runner"].startswith("seed-wine-")
            assert got["prefix"] == "/app/prefixes/canonical/stellaris"
            digest = hashlib.sha256(json.dumps(got, sort_keys=True).encode()).hexdigest()
            raw = hashlib.sha256(build_seed_registry_text(SEED).encode()).hexdigest()
            assert digest != raw

    def test_006_deep_chain_max_depth(self) -> None:
        """006 must report max_depth at least 5 for the deep requires chain."""
        fixture = REGISTRY / "006-deep-chain"
        cfg = load_config(CONFIG)
        expected, expected_rc = build_resolve(fixture, "deep-root", cfg)
        proc = run_resolve(fixture, "deep-root")
        assert proc.returncode == expected_rc
        got = load_resolve()
        assert got["stats"]["max_depth"] >= 5
        assert got == expected

    def test_007_cycle_empty_closure(self) -> None:
        """007 must exit 2 with empty closure and recorded cycles."""
        fixture = REGISTRY / "007-requires-cycle"
        cfg = load_config(CONFIG)
        expected, expected_rc = build_resolve(fixture, "cycle-root", cfg)
        proc = run_resolve(fixture, "cycle-root")
        assert proc.returncode == expected_rc, proc.stderr + proc.stdout
        got = load_resolve()
        assert got["closure"] == []
        assert got["cycles"] == expected["cycles"]

    def test_005_missing_runner_exits_one(self) -> None:
        """005 must exit 1 when no runner is inherited."""
        proc = run_resolve(REGISTRY / "005-missing-runner", "orphan-game")
        assert proc.returncode == 1
        got = load_resolve()
        assert any("missing runner" in err for err in got["errors"])

    def test_004_duplicate_merge_warning(self) -> None:
        """004 must merge duplicate slugs and emit a warning."""
        proc = run_resolve(REGISTRY / "004-duplicate-merge", "dup-game")
        assert proc.returncode == 0
        got = load_resolve()
        assert any("duplicate slug shared-lib merged" in w for w in got["warnings"])
        assert "lib-a" in got["closure"] and "lib-b" in got["closure"]

    def test_008_missing_slug_exits_one(self) -> None:
        """008 must exit 1 when a requires entry references an absent slug."""
        proc = run_resolve(REGISTRY / "008-missing-slug", "ghost-game")
        assert proc.returncode == 1
        got = load_resolve()
        assert any("missing slug phantom-pack" in err for err in got["errors"])

    def test_009_conflicting_duplicate_exits_two(self) -> None:
        """009 must exit 2 when duplicate slugs have conflicting runners."""
        proc = run_resolve(REGISTRY / "009-conflicting-duplicate", "clash-game")
        assert proc.returncode == 2
        got = load_resolve()
        assert any("conflicting runner" in err for err in got["errors"])

    def test_partial_golden_registry_only_still_fails(self) -> None:
        """Anti-cheat: registry merge fix alone must not pass transitive runner fixture."""
        saved = snapshot_libs()
        try:
            install_libs(registry_sh="golden_registry.sh", closure_sh="broken_closure.sh")
            fixture = REGISTRY / "001-transitive-runner"
            expected, _rc = build_resolve(fixture, "frontier-rpg", load_config(CONFIG))
            proc = run_resolve(fixture, "frontier-rpg")
            assert proc.returncode == 0 or proc.returncode == 1
            got = load_resolve()
            assert got != expected
        finally:
            restore_libs(saved)

    def test_partial_golden_closure_only_still_fails(self) -> None:
        """Anti-cheat: closure fix alone cannot fix duplicate-slug merge behavior."""
        saved = snapshot_libs()
        try:
            install_libs(
                registry_sh="broken_registry.sh",
                closure_sh="golden_closure.sh",
                prefix_sh="broken_prefix.sh",
                semver_sh="broken_semver.sh",
            )
            fixture = REGISTRY / "004-duplicate-merge"
            expected, _rc = build_resolve(fixture, "dup-game", load_config(CONFIG))
            run_resolve(fixture, "dup-game")
            got = load_resolve()
            assert got != expected
        finally:
            restore_libs(saved)

    def test_partial_golden_prefix_only_still_fails(self) -> None:
        """Anti-cheat: prefix fix alone must not pass duplicate merge closure."""
        saved = snapshot_libs()
        try:
            install_libs(
                registry_sh="broken_registry.sh",
                closure_sh="broken_closure.sh",
                prefix_sh="golden_prefix.sh",
            )
            fixture = REGISTRY / "004-duplicate-merge"
            expected, _rc = build_resolve(fixture, "dup-game", load_config(CONFIG))
            run_resolve(fixture, "dup-game")
            got = load_resolve()
            assert got != expected
        finally:
            restore_libs(saved)
