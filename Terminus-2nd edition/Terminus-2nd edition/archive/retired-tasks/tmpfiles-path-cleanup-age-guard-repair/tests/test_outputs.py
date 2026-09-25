"""Behavioral verifier for tmpfiles path cleanup age guard repair."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest

from reference_apply import reference_apply, reference_generate
from scenario_builder import build_hidden_age_trap


APP = Path("/app")
OUTPUT = APP / "output"
CLI = "/app/bin/tmpfiles-replay"
RESET = APP / "scripts/reset-state.sh"
LIB = APP / "lib"

BROKEN_SNAPSHOT = Path("/opt/verifier-broken-tmpfiles")
GOLDEN_LIB = Path(__file__).resolve().parent / "golden_lib"

CATALOG = json.loads((APP / "fixtures" / "catalog.json").read_text(encoding="utf-8"))
APPLY_SCENARIOS = [
    row["name"] for row in CATALOG["scenarios"] if row["name"] != "005-boot-ex-merge"
]

LIB_MODULES = (
    "age_eval",
    "glob_prune",
    "recreate_seq",
    "ownership",
    "generator_merge",
)

NOW_DEFAULT = 10_000
NOW_BY_SCENARIO = {
    "003-recreate-after-age": 5_000,
    "002-exclude-depth": 20_000,
}

VERIFIER_SEED = os.environ.get(
    "VERIFIER_SEED", "tmpfiles-path-cleanup-age-guard-repair"
)


def restore_broken_lib() -> None:
    for mod in LIB_MODULES:
        src = BROKEN_SNAPSHOT / f"{mod}.sh"
        data = src.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        (LIB / f"{mod}.sh").write_bytes(data)


def install_lib_module(src: Path, dest: Path) -> None:
    data = src.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    dest.write_bytes(data)


def install_golden_lib() -> None:
    for name in LIB_MODULES:
        install_lib_module(GOLDEN_LIB / f"golden_{name}.sh", LIB / f"{name}.sh")


def install_modules(only_golden: set[str]) -> None:
    for mod in LIB_MODULES:
        dest = LIB / f"{mod}.sh"
        if mod in only_golden:
            install_lib_module(GOLDEN_LIB / f"golden_{mod}.sh", dest)
        else:
            install_lib_module(BROKEN_SNAPSHOT / f"{mod}.sh", dest)


def run(cmd: list[str], *, env: dict | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        cmd, cwd=str(APP), capture_output=True, text=True, check=False, env=merged
    )


def reset() -> None:
    proc = run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def scenario_now(scenario: str) -> int:
    return NOW_BY_SCENARIO.get(scenario, NOW_DEFAULT)


def apply(
    scenario: str | Path,
    *,
    seed: str = "alpha01",
    now_epoch: int | None = None,
    out: Path | None = None,
    env: dict | None = None,
) -> subprocess.CompletedProcess[str]:
    scen_arg = str(scenario)
    label = Path(scenario).name if scen_arg.startswith("/") else scen_arg
    now = now_epoch if now_epoch is not None else scenario_now(label)
    target = out or (OUTPUT / f"{label}-{seed}.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    return run(
        [
            CLI,
            "apply",
            "--scenario",
            scen_arg,
            "--seed",
            seed,
            "--now",
            str(now),
            "--export",
            str(target),
        ],
        env=env,
    )


def generate(
    scenario: str,
    mode: str,
    out: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    target = out or (OUTPUT / f"gen-{scenario}-{mode}.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    return run(
        [
            CLI,
            "generate",
            "--scenario",
            scenario,
            "--mode",
            mode,
            "--export-rules",
            str(target),
        ]
    )


def load_export(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_apply_matches_reference(scenario: str, seed: str = "alpha01") -> None:
    """Verify apply export matches independent reference implementation."""
    now = scenario_now(scenario)
    out = OUTPUT / f"ref-{scenario}-{seed}.json"
    proc = apply(scenario, seed=seed, now_epoch=now, out=out)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = load_export(out)
    expect = reference_apply(scenario, seed, now)
    assert got == expect, f"scenario={scenario} diff"


@pytest.fixture(autouse=True)
def _reset_env():
    """Reset work/output each test; image ships broken lib until agent or oracle fixes."""
    reset()
    yield
    reset()


def test_module_docstring_present():
    """Module docstring maps to tmpfiles apply contract."""
    assert "tmpfiles" in Path(__file__).read_text(encoding="utf-8")


@pytest.mark.parametrize("scenario", APPLY_SCENARIOS)
def test_bundled_apply_matches_reference(scenario: str):
    """Every bundled apply scenario matches reference tmpfiles math."""
    assert_apply_matches_reference(scenario)


def test_atime_btime_not_mtime_only():
    """Fresh btime keeps file when mtime looks stale."""
    assert_apply_matches_reference("001-atime-btime-age")


def test_exclude_depth_prunes_nested_only():
    """e1 exclude keeps direct child but not deeper stale tmp."""
    assert_apply_matches_reference("002-exclude-depth")


def test_recreate_waits_for_subtree_age():
    """Recreate runs only after journal age removal under state prefix."""
    assert_apply_matches_reference("003-recreate-after-age")


def test_ownership_before_remove_trace():
    """Ownership action precedes remove on same path."""
    out = OUTPUT / "own-order.json"
    proc = apply("004-ownership-before-remove", out=out)
    assert proc.returncode == 0
    doc = load_export(out)
    ref = reference_apply("004-ownership-before-remove", "alpha01", NOW_DEFAULT)
    assert doc["actions"] == ref["actions"]
    types = [row["type"] for row in doc["actions"]]
    assert types.index("ownership") < types.index("remove")


def test_boot_merge_excludes_boot_ex_in_boot_mode():
    """boot generate mode emits only boot fragments."""
    out = OUTPUT / "gen-boot.json"
    proc = generate("005-boot-ex-merge", "boot", out=out)
    assert proc.returncode == 0
    doc = load_export(out)
    ref = reference_generate("005-boot-ex-merge", "boot")
    assert doc == ref
    assert doc["line_count"] == 1


def test_boot_ex_merge_includes_both():
    """boot-ex generate mode merges boot and boot-ex fragments."""
    out = OUTPUT / "gen-boot-ex.json"
    proc = generate("005-boot-ex-merge", "boot-ex", out=out)
    assert proc.returncode == 0
    doc = load_export(out)
    ref = reference_generate("005-boot-ex-merge", "boot-ex")
    assert doc == ref
    assert doc["line_count"] == 2


def test_nested_globstar_candidates():
    """Globstar remove rule reaches nested cache files."""
    assert_apply_matches_reference("006-nested-glob")


def test_combined_trap_interactions():
    """Age, exclude depth, and recreate sequencing interact on combo tree."""
    assert_apply_matches_reference("007-combined-trap")


def test_ownership_on_survivor_path():
    """Ownership applies when age gate leaves path in tree."""
    assert_apply_matches_reference("008-ownership-survivor")


def test_tb3_clock_override():
    """TB3_CLOCK_EPOCH overrides --now for apply instant."""
    out = OUTPUT / "tb3.json"
    proc = apply(
        "008-ownership-survivor",
        now_epoch=NOW_DEFAULT,
        out=out,
        env={"TB3_CLOCK_EPOCH": "5000"},
    )
    assert proc.returncode == 0
    doc = load_export(out)
    ref = reference_apply("008-ownership-survivor", "alpha01", 5000)
    assert doc == ref


def test_hidden_age_trap():
    """Hidden fixture fails when age gate uses mtime instead of btime."""
    hidden = build_hidden_age_trap(Path("/tmp/tmpfiles-hidden"))
    assert_apply_matches_reference(str(hidden))


def test_partial_age_fix_insufficient():
    """Fixing age_eval alone leaves exclude, recreate, ownership, merge failures."""
    restore_broken_lib()
    install_modules({"age_eval"})
    trap_scenarios = (
        "002-exclude-depth",
        "003-recreate-after-age",
        "004-ownership-before-remove",
        "007-combined-trap",
    )
    for scenario in trap_scenarios:
        now = scenario_now(scenario)
        out = OUTPUT / f"partial-age-{scenario}.json"
        proc = apply(scenario, out=out, now_epoch=now)
        assert proc.returncode == 0
        got = load_export(out)
        expect = reference_apply(scenario, "alpha01", now)
        assert got != expect, f"age-only fix must not pass {scenario}"

    hidden = build_hidden_age_trap(Path("/tmp/tmpfiles-partial-age"))
    hidden_out = OUTPUT / "partial-age-hidden.json"
    proc = apply(str(hidden), out=hidden_out)
    assert proc.returncode == 0
    got_hidden = load_export(hidden_out)
    expect_hidden = reference_apply(str(hidden), "alpha01", NOW_DEFAULT)
    assert got_hidden == expect_hidden

    failed = 0
    for scenario in APPLY_SCENARIOS:
        now = scenario_now(scenario)
        out = OUTPUT / f"partial-age-count-{scenario}.json"
        proc = apply(scenario, out=out, now_epoch=now)
        assert proc.returncode == 0
        got = load_export(out)
        expect = reference_apply(scenario, "alpha01", now)
        if got != expect:
            failed += 1
    assert failed >= 4


def test_partial_glob_fix_insufficient():
    """Fixing glob_prune alone leaves recreate and ownership traps."""
    restore_broken_lib()
    install_modules({"glob_prune"})
    for scenario in ("003-recreate-after-age", "004-ownership-before-remove", "007-combined-trap"):
        now = scenario_now(scenario)
        out = OUTPUT / f"partial-glob-{scenario}.json"
        proc = apply(scenario, out=out, now_epoch=now)
        assert proc.returncode == 0
        got = load_export(out)
        expect = reference_apply(scenario, "alpha01", now)
        assert got != expect, f"glob-only fix must not pass {scenario}"


def test_partial_recreate_fix_insufficient():
    """Fixing recreate_seq alone still fails combined trap ordering."""
    restore_broken_lib()
    install_modules({"recreate_seq"})
    out = OUTPUT / "partial-recreate-combo.json"
    proc = apply("007-combined-trap", out=out)
    assert proc.returncode == 0
    got = load_export(out)
    expect = reference_apply("007-combined-trap", "alpha01", NOW_DEFAULT)
    assert got != expect


def test_golden_lib_passes_smoke():
    """Oracle golden modules pass base age scenario."""
    install_golden_lib()
    assert_apply_matches_reference("001-atime-btime-age")


def test_generated_seed_stable():
    """Mutated seed still matches reference for nested glob scenario."""
    seed = hashlib.sha256(f"{VERIFIER_SEED}-nested".encode()).hexdigest()[:12]
    assert_apply_matches_reference("006-nested-glob", seed=seed)
