"""Behavioral verifier for atd batch queue slot release order repair."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from reference_replay import reference_run
from scenario_builder import build_crash_seq_fixture, build_hidden_slot_trap

APP = Path("/app")
OUTPUT = APP / "output"
CLI = "/app/bin/at-replay"
RESET = APP / "scripts/reset-state.sh"
LIB = APP / "lib"

BROKEN_SNAPSHOT = Path("/opt/verifier-broken-atd")

LIB_MODULES = ("spool", "slots", "mail", "atq", "seq")

CLOCK_DEFAULT = 1_700_000_000


def _golden_lib_dir() -> Path:
    """Verifier-only golden modules staged by tests/test.sh (not in agent image)."""
    raw = os.environ.get("VERIFIER_GOLDEN_LIB", "").strip()
    if not raw:
        pytest.fail("VERIFIER_GOLDEN_LIB is unset; tests/test.sh must stage golden_lib before pytest")
    return Path(raw)


CATALOG = json.loads((APP / "fixtures" / "catalog.json").read_text(encoding="utf-8"))
ALL_SCENARIOS = [row["name"] for row in CATALOG["scenarios"]]


def restore_broken_lib() -> None:
    """Restore broken lib modules from verifier snapshot."""
    for mod in LIB_MODULES:
        src = BROKEN_SNAPSHOT / f"{mod}.sh"
        data = src.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        (LIB / f"{mod}.sh").write_bytes(data)


def install_lib_module(src: Path, dest: Path) -> None:
    data = src.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    dest.write_bytes(data)


def install_modules(only_broken: set[str]) -> None:
    golden = _golden_lib_dir()
    for mod in LIB_MODULES:
        dest = LIB / f"{mod}.sh"
        if mod in only_broken:
            install_lib_module(BROKEN_SNAPSHOT / f"{mod}.sh", dest)
        else:
            install_lib_module(golden / f"golden_{mod}.sh", dest)


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


def replay(
    scenario: str | Path,
    *,
    seed: str = "alpha01",
    clock_epoch: int | None = None,
    out: Path | None = None,
    env: dict | None = None,
) -> subprocess.CompletedProcess[str]:
    label = Path(scenario).name if str(scenario).startswith("/") else str(scenario)
    clock = clock_epoch if clock_epoch is not None else CLOCK_DEFAULT
    target = out or (OUTPUT / f"{label}-{seed}.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    return run(
        [CLI, "replay", "--scenario", str(scenario), "--seed", seed, "--clock", str(clock), "--export", str(target)],
        env=env,
    )


def load_export(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_matches_reference(scenario: str, seed: str = "alpha01") -> None:
    """Verify CLI export matches independent reference implementation."""
    clock = CLOCK_DEFAULT
    out = OUTPUT / f"ref-{scenario}-{seed}.json"
    proc = replay(scenario, seed=seed, clock_epoch=clock, out=out)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = load_export(out)
    expect = reference_run(scenario, seed, clock)
    assert got == expect, f"scenario={scenario} diff"


@pytest.fixture(autouse=True)
def _reset_env():
    """Reset work/output each test; image ships broken lib until agent or oracle fixes."""
    reset()
    yield
    reset()


@pytest.mark.parametrize("scenario", ALL_SCENARIOS)
def test_bundled_scenario_matches_reference(scenario: str):
    """Every bundled scenario replay matches reference scheduling math."""
    assert_matches_reference(scenario)


def test_slot_held_until_completion():
    """Second job in same batch must wait when first slot still held through spool lifetime."""
    assert_matches_reference("003-slot-hold")


def test_letter_retry_skips_occupied_spool():
    """allocate_letter advances when start letter spool file already exists."""
    assert_matches_reference("004-letter-retry")


def test_fail_mail_after_registry_delete():
    """Failure mail timeline event follows registry_delete."""
    out = OUTPUT / "mail-order.json"
    proc = replay("005-mail-fail-order", out=out)
    assert proc.returncode == 0
    doc = load_export(out)
    ref = reference_run("005-mail-fail-order", "alpha01", CLOCK_DEFAULT)
    assert doc["timeline"] == ref["timeline"]
    events = [row["event"] for row in doc["timeline"] if row["job"] == "ops:fail"]
    assert events.index("registry_delete") < events.index("mail_sent")


def test_atq_sorted_by_epoch_not_mtime():
    """Pending atq lines sort by ATQ_EPOCH from headers."""
    assert_matches_reference("006-atq-seq")


def test_seq_bump_atomic():
    """SEQ advances from partial fixture without corrupt body."""
    out = OUTPUT / "seq-check.json"
    proc = replay("006-atq-seq", out=out)
    assert proc.returncode == 0
    doc = load_export(out)
    assert doc["seq_final"] == 44


def test_tb3_clock_override():
    """TB3_CLOCK_EPOCH overrides --clock for the replay instant."""
    out = OUTPUT / "tb3.json"
    proc = replay(
        "002-not-yet",
        clock_epoch=CLOCK_DEFAULT,
        out=out,
        env={"TB3_CLOCK_EPOCH": "1700003600"},
    )
    assert proc.returncode == 0
    doc = load_export(out)
    ref = reference_run("002-not-yet", "alpha01", 1_700_003_600)
    assert doc == ref


def test_tb3_clock_epoch_without_clock_flag():
    """TB3_CLOCK_EPOCH supplies replay instant when --clock is omitted."""
    out = OUTPUT / "tb3-no-flag.json"
    proc = run(
        [
            CLI,
            "replay",
            "--scenario",
            "002-not-yet",
            "--seed",
            "alpha01",
            "--export",
            str(out),
        ],
        env={"TB3_CLOCK_EPOCH": "1700003600"},
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    doc = load_export(out)
    ref = reference_run("002-not-yet", "alpha01", 1_700_003_600)
    assert doc == ref


def test_hidden_slot_trap():
    """Hidden slot retry trap matches reference when lib is fixed."""
    hidden = build_hidden_slot_trap(Path("/tmp/atd-hidden-slot"))
    assert_matches_reference(str(hidden))


def test_hidden_slot_trap_fails_with_broken_slots():
    """Broken slots module does not retry past occupied letter on hidden trap."""
    restore_broken_lib()
    hidden = build_hidden_slot_trap(Path("/tmp/atd-hidden-broken-slots"))
    out = OUTPUT / "hidden-broken-slots.json"
    proc = replay(str(hidden), out=out)
    assert proc.returncode == 0
    got = load_export(out)
    expect = reference_run(str(hidden), "alpha01", CLOCK_DEFAULT)
    assert got != expect


def test_crash_seq_fixture():
    """Crash mid-seq fixture still bumps atomically."""
    hidden = build_crash_seq_fixture(Path("/tmp/atd-crash-seq"))
    assert_matches_reference(str(hidden))


def test_partial_atq_fix_insufficient():
    """Fixing atq alone leaves slot and seq failures on trap scenarios."""
    restore_broken_lib()
    install_modules(set(LIB_MODULES) - {"atq"})
    trap_scenarios = ("003-slot-hold", "004-letter-retry", "006-atq-seq")
    failed = 0
    for scenario in trap_scenarios:
        out = OUTPUT / f"partial-atq-{scenario}.json"
        proc = replay(scenario, out=out)
        assert proc.returncode == 0
        got = load_export(out)
        expect = reference_run(scenario, "alpha01", CLOCK_DEFAULT)
        if got != expect:
            failed += 1
    assert failed >= 2


def test_partial_spool_fix_insufficient():
    """Fixing spool alone leaves mail ordering and letter retry failures."""
    restore_broken_lib()
    install_modules(set(LIB_MODULES) - {"spool"})
    trap_scenarios = ("003-slot-hold", "005-mail-fail-order", "004-letter-retry")
    failed = 0
    for scenario in trap_scenarios:
        out = OUTPUT / f"partial-spool-{scenario}.json"
        proc = replay(scenario, out=out)
        assert proc.returncode == 0
        got = load_export(out)
        expect = reference_run(scenario, "alpha01", CLOCK_DEFAULT)
        if got != expect:
            failed += 1
    assert failed >= 2
