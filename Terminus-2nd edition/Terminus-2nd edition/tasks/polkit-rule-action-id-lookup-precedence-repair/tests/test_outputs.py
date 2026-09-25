"""Behavioral verifier for pkctl polkit-style evaluation."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from reference_polkit import evaluate

APP = Path("/app")
FIXTURES = APP / "fixtures"
CLI = "/app/bin/pkctl"
RESET = APP / "scripts/reset-state.sh"
REBUILD = APP / "scripts/verifier-rebuild.sh"
CATALOG = json.loads((FIXTURES / "catalog.json").read_text(encoding="utf-8"))
SCENARIOS = FIXTURES / "scenarios"
TESTS_DIR = Path(__file__).resolve().parent
TB3 = "/opt/verifier-fixtures"

PROTECTED_SHA256: dict[str, str] = {}


def _init_hashes() -> None:
    for path in sorted(FIXTURES.rglob("*")):
        if path.is_file() and path.suffix in {".json", ".rules", ".js", ".xml"}:
            rel = path.relative_to(FIXTURES).as_posix()
            PROTECTED_SHA256[rel] = hashlib.sha256(path.read_bytes()).hexdigest()


_init_hashes()


def run(cmd: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False, env=merged)


def reset() -> None:
    proc = run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def rebuild() -> None:
    proc = run(["bash", str(REBUILD)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def evaluate_cli(scenario_file: str, tb3: str | None = None) -> dict:
    env = {"TB3_RULES_DIR": tb3} if tb3 else {}
    proc = run([CLI, "evaluate", "--scenario", str(SCENARIOS / scenario_file)], env=env)
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return json.loads(proc.stdout)


def _save_exec_script(path: Path) -> tuple[bytes, int]:
    st = path.stat()
    return path.read_bytes(), st.st_mode


def _restore_exec_script(path: Path, data: bytes, mode: int) -> None:
    path.write_bytes(data)
    path.chmod(mode)


@pytest.fixture
def ready() -> None:
    reset()
    rebuild()


class TestPkctl:
    """pkctl evaluate vs reference_polkit."""

    @pytest.mark.parametrize("entry", [e for e in CATALOG["scenarios"] if not e.get("tb3")])
    def test_catalog_scenario_matches_reference(self, ready: None, entry: dict) -> None:
        """Every public catalog scenario must match independent reference."""
        scenario = json.loads((SCENARIOS / entry["file"]).read_text(encoding="utf-8"))
        reset()
        rebuild()
        expect = evaluate(APP, scenario)
        reset()
        rebuild()
        got = evaluate_cli(entry["file"])
        assert got == expect

    def test_reboot_numeric_precedence_requires_admin_challenge(self, ready: None) -> None:
        """2-wheel before 10-default: later file wins with auth_admin."""
        got = evaluate_cli("reboot-local-active.json")
        assert got["decision"] == "challenge"
        assert got["challenge"] == "auth_admin"
        assert got["matched_rule"] == "10-default.rules"

    def test_mount_inactive_local_implicit_allow(self, ready: None) -> None:
        """Inactive local mount scenario must implicit-allow via 50-inactive.rules."""
        got = evaluate_cli("mount-inactive-local.json")
        assert got["decision"] == "allow"
        assert got["implicit"] is True
        assert got["matched_rule"] == "50-inactive.rules"

    def test_network_prefers_js_over_xml(self, ready: None) -> None:
        """Action lookup must use JS allow_active yes, not XML no."""
        got = evaluate_cli("network-js-default.json")
        assert got["decision"] == "allow"
        assert got["source"] == "action:js:com.example.network.set"

    def test_package_retain_grant_allows_admin_challenge(self, ready: None) -> None:
        """auth_admin_keep prior must satisfy auth_admin challenge when base allows."""
        got = evaluate_cli("package-challenge-retain.json")
        assert got["decision"] == "allow"
        assert got["matched_rule"] == "20-second.rules"

    def test_auth_self_rejects_admin_keep_retain(self, ready: None) -> None:
        """auth_self must not honor auth_admin_keep prior on same seat."""
        got = evaluate_cli("package-auth-self-no-retain.json")
        assert got["decision"] == "challenge"
        assert got["challenge"] == "auth_self"

    def test_cache_isolated_by_seat(self, ready: None) -> None:
        """Implicit yes on seat0 must not cache seat5; second seat0 hit uses cache."""
        first = evaluate_cli("cache-seat0-first.json")
        assert first["decision"] == "allow"
        other = evaluate_cli("cache-seat5-second.json")
        assert other["decision"] == "allow"
        assert other["source"] != "cache"
        cached = evaluate_cli("cache-seat0-first.json")
        assert cached["decision"] == "cached_allow"
        assert cached["source"] == "cache"

    def test_hidden_js_action_from_tb3(self, ready: None) -> None:
        """TB3 fixture must load JS action allow yes over XML no."""
        scenario = json.loads((SCENARIOS / "hidden-js-win.json").read_text(encoding="utf-8"))
        reset()
        rebuild()
        expect = evaluate(APP, scenario, tb3=TB3)
        reset()
        rebuild()
        got = evaluate_cli("hidden-js-win.json", tb3=TB3)
        assert got == expect
        assert got["decision"] == "allow"
        assert got["source"] == "action:js:com.example.hidden.service"

    def test_hidden_seat_cache_tb3_stack(self, ready: None) -> None:
        """TB3 hidden-seat-cache stack must allow then cache per seat."""
        scenario = json.loads((SCENARIOS / "hidden-seat-cache.json").read_text(encoding="utf-8"))
        reset()
        rebuild()
        expect = evaluate(APP, scenario, tb3=TB3)
        reset()
        rebuild()
        got = evaluate_cli("hidden-seat-cache.json", tb3=TB3)
        assert got == expect

    def test_fixture_integrity(self, ready: None) -> None:
        """Bundled fixtures must match baked digests."""
        for rel, digest in PROTECTED_SHA256.items():
            path = FIXTURES / rel
            assert path.is_file(), rel
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, rel

    def test_rebuild_preserves_evaluate(self, ready: None) -> None:
        """Verifier rebuild must keep corrected evaluation output."""
        scenario = json.loads((SCENARIOS / "network-js-default.json").read_text(encoding="utf-8"))
        reset()
        rebuild()
        expect = evaluate(APP, scenario)
        rebuild()
        reset()
        rebuild()
        got = evaluate_cli("network-js-default.json")
        assert got == expect

    def test_partial_broken_merge_fails_reboot_precedence(self, ready: None) -> None:
        """Only merge fix must restore 10-default auth_admin over 2-wheel yes."""
        target = APP / "lib/merge_rules.sh"
        backup = _save_exec_script(target)
        try:
            shutil.copy2(TESTS_DIR / "broken_merge_rules.sh", target)
            target.chmod(backup[1])
            got = evaluate_cli("reboot-local-active.json")
            assert got["decision"] == "deny"
        finally:
            _restore_exec_script(target, *backup)
            rebuild()

    def test_partial_broken_subject_fails_network_js(self, ready: None) -> None:
        """Only subject mapping fix must read JS allow_active for active local."""
        target = APP / "lib/subject_eval.sh"
        backup = _save_exec_script(target)
        try:
            shutil.copy2(TESTS_DIR / "broken_subject_eval.sh", target)
            target.chmod(backup[1])
            got = evaluate_cli("network-js-default.json")
            assert got["decision"] != "allow"
        finally:
            _restore_exec_script(target, *backup)
            rebuild()

    def test_partial_broken_registry_prefers_xml(self, ready: None) -> None:
        """Only registry fix must prefer JS over XML for network.set."""
        target = APP / "lib/action_registry.sh"
        backup = _save_exec_script(target)
        try:
            shutil.copy2(TESTS_DIR / "broken_action_registry.sh", target)
            target.chmod(backup[1])
            got = evaluate_cli("network-js-default.json")
            assert got["decision"] == "deny"
        finally:
            _restore_exec_script(target, *backup)
            rebuild()

    def test_partial_broken_challenge_honors_retain_on_self(self, ready: None) -> None:
        """Only challenge fix must reject auth_admin_keep prior for auth_self."""
        target = APP / "lib/challenge.sh"
        backup = _save_exec_script(target)
        try:
            shutil.copy2(TESTS_DIR / "broken_challenge.sh", target)
            target.chmod(backup[1])
            got = evaluate_cli("package-auth-self-no-retain.json")
            assert got["decision"] == "allow"
        finally:
            _restore_exec_script(target, *backup)
            rebuild()

    def test_partial_broken_cache_cross_seat(self, ready: None) -> None:
        """Only cache fix must not return cached_allow for different seat."""
        target = APP / "lib/auth_cache.sh"
        backup = _save_exec_script(target)
        try:
            shutil.copy2(TESTS_DIR / "broken_auth_cache.sh", target)
            target.chmod(backup[1])
            evaluate_cli("cache-seat0-first.json")
            got = evaluate_cli("cache-seat5-second.json")
            assert got["decision"] == "cached_allow"
        finally:
            _restore_exec_script(target, *backup)
            rebuild()
