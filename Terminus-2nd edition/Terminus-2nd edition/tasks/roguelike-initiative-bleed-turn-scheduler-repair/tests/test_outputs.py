"""Behavioral verifier for turnctl ingest → simulate → export."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest
import reference_scheduler as reference_mod
from reference_scheduler import (
    fnv1a64,
    mutate_roster,
    reference_ingest,
    reference_pipeline,
    reference_simulate,
    transcript_hash,
)

APP = Path("/app")
CLI = "/usr/local/bin/turnctl"
FIXTURES = APP / "fixtures"
OUTPUT = APP / "output"
CATALOG = json.loads((FIXTURES / "catalog.json").read_text(encoding="utf-8"))
SEEDS = json.loads((FIXTURES / "seeds.json").read_text(encoding="utf-8"))["seeds"]
VERIFIER_SEED = os.environ.get("VERIFIER_SEED", SEEDS[0])
TB3_ROOT = Path("/opt/verifier-fixtures/turnctl")
TB3_HIDDEN_ROSTER = TB3_ROOT / "rosters" / "six_actor_bleed.json"
HIDDEN = Path("/tests/hidden_rosters")
RESET = APP / "scripts" / "reset-state.sh"
CORE = APP / "crates/combat-core/src"
BROKEN = Path("/opt/verifier-broken-combat")
GOLDEN = Path("/tests/golden_modules")
MODULES = ("ingest", "scheduler", "bleed", "export", "simulate")


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False)


def rebuild_turnctl() -> None:
    for mod in MODULES:
        (CORE / f"{mod}.rs").touch()
    proc = run(
        [
            "bash",
            "-lc",
            (
                "export PATH=\"/usr/local/cargo/bin:/usr/local/bin:${PATH}\" "
                "CARGO_INCREMENTAL=0 CARGO_NET_OFFLINE=true && "
                "cargo build --offline --locked --release --bin turnctl && "
                "install -m 0755 target/release/turnctl /usr/local/bin/turnctl"
            ),
        ]
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout


def restore_broken() -> None:
    for mod in MODULES:
        shutil.copy2(BROKEN / f"{mod}.rs", CORE / f"{mod}.rs")


def install_modules(only_broken: set[str]) -> None:
    for mod in MODULES:
        dest = CORE / f"{mod}.rs"
        if mod in only_broken:
            shutil.copy2(BROKEN / f"{mod}.rs", dest)
        else:
            shutil.copy2(GOLDEN / f"golden_{mod}.rs", dest)


def reset() -> None:
    proc = run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def roster_path(name: str) -> Path:
    entry = next(s for s in CATALOG["scenarios"] if s["name"] == name)
    return FIXTURES / entry["source"]


def hidden_roster_path() -> Path:
    """Prefer /opt/verifier-fixtures image rosters; fall back to /tests mount."""
    if TB3_HIDDEN_ROSTER.is_file():
        return TB3_HIDDEN_ROSTER
    return HIDDEN / "six_actor_bleed.json"


def paths_for(name: str, seed: str) -> tuple[Path, Path, Path]:
    staging = OUTPUT / f"{name}.staging.json"
    state = OUTPUT / f"{name}-{seed}.state.json"
    export = OUTPUT / f"{name}-{seed}.json"
    return staging, state, export


def ingest_cli(roster: Path, staging: Path) -> subprocess.CompletedProcess[str]:
    return run([CLI, "ingest", "--roster", str(roster), "--staging", str(staging)])


def simulate_cli(staging: Path, seed: str, state: Path, export: Path) -> subprocess.CompletedProcess[str]:
    return run(
        [
            CLI,
            "simulate",
            "--staging",
            str(staging),
            "--seed",
            seed,
            "--state",
            str(state),
            "--export",
            str(export),
        ]
    )


def export_cli(state: Path, export: Path) -> subprocess.CompletedProcess[str]:
    return run([CLI, "export", "--state", str(state), "--export", str(export)])


def run_pipeline(name: str, seed: str, roster: Path | None = None) -> subprocess.CompletedProcess[str]:
    roster = roster or roster_path(name)
    staging, state, export = paths_for(name, seed)
    proc = ingest_cli(roster, staging)
    if proc.returncode != 0:
        return proc
    return simulate_cli(staging, seed, state, export)


def load_export(name: str, seed: str) -> dict:
    return json.loads(paths_for(name, seed)[2].read_text(encoding="utf-8"))


def load_state(name: str, seed: str) -> dict:
    return json.loads(paths_for(name, seed)[1].read_text(encoding="utf-8"))


def expected(name: str, seed: str, roster: Path | None = None) -> dict:
    return reference_pipeline(roster or roster_path(name), seed)


@pytest.fixture(autouse=True, scope="module")
def _rebuild_turnctl_from_workspace() -> None:
    rebuild_turnctl()


@pytest.fixture(autouse=True)
def _reset_output() -> None:
    reset()


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("scenario_name", [s["name"] for s in CATALOG["scenarios"]])
def test_pipeline_matches_reference(scenario_name: str, seed: str) -> None:
    """Every catalog roster must match the independent scheduler reference."""
    proc = run_pipeline(scenario_name, seed)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert load_export(scenario_name, seed) == expected(scenario_name, seed)


def test_ingest_rejects_negative_bleed_without_staging_file() -> None:
    """Ingest must reject negative bleed and not write staging."""
    roster = FIXTURES / "rosters/negative_bleed.json"
    staging = OUTPUT / "negative.staging.json"
    if staging.exists():
        staging.unlink()
    proc = ingest_cli(roster, staging)
    assert proc.returncode != 0
    assert not staging.exists()


def test_staging_checksum_matches_reference() -> None:
    """Staging checksum must match SHA-256 of actor rows."""
    roster = roster_path("initiative_tie")
    staging = OUTPUT / "checksum.staging.json"
    proc = ingest_cli(roster, staging)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    doc = json.loads(staging.read_text(encoding="utf-8"))
    ref = reference_ingest(roster)
    assert doc["checksum"] == ref["checksum"]


def test_initiative_tie_orders_by_initiative_not_name() -> None:
    """Turn order must break initiative ties by name after sorting initiative."""
    seed = SEEDS[0]
    doc = expected("initiative_tie", seed)
    first = doc["rounds"][0]["events"][0]["actor"]
    assert first == "bravo"
    proc = run_pipeline("initiative_tie", seed)
    assert proc.returncode == 0
    got_first = load_export("initiative_tie", seed)["rounds"][0]["events"][0]["actor"]
    assert got_first == first


def test_bleed_runs_before_act_in_transcript() -> None:
    """Bleed events must appear before act events in each round transcript."""
    seed = SEEDS[0]
    proc = run_pipeline("bleed_timing", seed)
    assert proc.returncode == 0
    events = load_export("bleed_timing", seed)["rounds"][0]["events"]
    kinds = [ev["kind"] for ev in events]
    bleed_idx = kinds.index("bleed")
    act_idx = kinds.index("act")
    assert bleed_idx < act_idx


def test_stun_decrements_action_points_once() -> None:
    """Stunned striker must lose exactly one action point on stun skip."""
    seed = SEEDS[0]
    doc = expected("stun_bleed", seed)
    stun = next(ev for ev in doc["rounds"][0]["events"] if ev["kind"] == "stun_skip")
    assert stun["ap_after"] == 2
    bleed = next(ev for ev in doc["rounds"][0]["events"] if ev["kind"] == "bleed")
    assert bleed["damage"] == 2
    proc = run_pipeline("stun_bleed", seed)
    assert proc.returncode == 0
    assert load_export("stun_bleed", seed) == doc


def test_dead_actor_clears_pinned_flag() -> None:
    """Tank death from bleed must clear pinned in actors_final."""
    seed = SEEDS[2]
    doc = expected("pinned_death", seed)
    tank = next(a for a in doc["actors_final"] if a["id"] == "tank")
    assert tank["alive"] is False
    assert tank["pinned"] is False
    proc = run_pipeline("pinned_death", seed)
    assert proc.returncode == 0
    got_tank = next(a for a in load_export("pinned_death", seed)["actors_final"] if a["id"] == "tank")
    assert got_tank["pinned"] is False


def test_transcript_hash_matches_rounds_payload() -> None:
    """Export hash must be SHA-256 of compact rounds JSON from state."""
    seed = SEEDS[1]
    doc = expected("regression_full", seed)
    staging = reference_ingest(roster_path("regression_full"))
    state = reference_simulate(staging, seed)
    assert doc["transcript_hash"] == transcript_hash(state)
    proc = run_pipeline("regression_full", seed)
    assert proc.returncode == 0
    got = load_export("regression_full", seed)
    assert got["transcript_hash"] == doc["transcript_hash"]


def test_persistence_state_matches_reference() -> None:
    """Simulate must write state file matching reference combat state."""
    seed = SEEDS[2]
    proc = run_pipeline("turn_pressure", seed)
    assert proc.returncode == 0
    staging = reference_ingest(roster_path("turn_pressure"))
    ref_state = reference_simulate(staging, seed).to_dict()
    got_state = load_state("turn_pressure", seed)
    assert got_state["rounds"] == ref_state["rounds"]
    assert got_state["actors"] == ref_state["actors"]


def test_export_replay_is_idempotent() -> None:
    """Export from persisted state must match simulate export bytes."""
    seed = SEEDS[0]
    proc = run_pipeline("regression_full", seed)
    assert proc.returncode == 0
    _, state, export = paths_for("regression_full", seed)
    reexport = OUTPUT / "regression_full-reexport.json"
    proc2 = export_cli(state, reexport)
    assert proc2.returncode == 0
    assert export.read_bytes() == reexport.read_bytes()


def test_simulate_twice_is_byte_stable() -> None:
    """Running simulate twice with same inputs must produce identical export bytes."""
    seed = SEEDS[1]
    _, _, export = paths_for("regression_full", seed)
    proc1 = run_pipeline("regression_full", seed)
    assert proc1.returncode == 0
    first = export.read_bytes()
    proc2 = run_pipeline("regression_full", seed)
    assert proc2.returncode == 0
    second = export.read_bytes()
    assert first == second


def test_reference_scheduler_independent_of_cli() -> None:
    """Reference module must simulate without invoking turnctl."""
    doc = reference_pipeline(roster_path("turn_pressure"), SEEDS[0])
    assert len(doc["rounds"]) == 3
    assert doc["transcript_hash"]


def test_hidden_six_actor_bleed_matches_reference() -> None:
    """Hidden six-actor roster under /opt/verifier-fixtures must match independent reference replay."""
    hidden = hidden_roster_path()
    assert str(hidden).startswith("/opt/verifier-fixtures") or hidden.is_file()
    seed = VERIFIER_SEED
    name = "hidden-six-actor"
    staging, state, export = paths_for(name, seed)
    proc = ingest_cli(hidden, staging)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    proc = simulate_cli(staging, seed, state, export)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert json.loads(export.read_text(encoding="utf-8")) == reference_pipeline(hidden, seed)


def test_hidden_seed_changes_bleed_mutation_target() -> None:
    """Anti-hardcode: TB3 /opt/verifier-fixtures seed must change bleed mutation target."""
    hidden = hidden_roster_path()
    assert TB3_ROOT.as_posix() in hidden.as_posix() or hidden.is_file()
    targets: set[str] = set()
    for seed in SEEDS:
        staging = reference_ingest(hidden)
        actors = [reference_mod.Actor(**row) for row in deepcopy(staging["actors"])]
        reference_mod.apply_seed_mutation(actors, seed)
        idx = fnv1a64(seed) % len(actors)
        targets.add(actors[idx].id)
    assert len(targets) >= 2


def test_runtime_mutated_roster_replay() -> None:
    """Per-run roster mutation must recompute turns, not accept hardcoded exports."""
    seed = SEEDS[2]
    base = json.loads(roster_path("initiative_tie").read_text(encoding="utf-8"))
    mutated = mutate_roster(base, seed, "probe")
    mutated_path = OUTPUT / "mutated-initiative.json"
    mutated_path.write_text(json.dumps(mutated, indent=2) + "\n", encoding="utf-8")
    proc = run_pipeline("mutated-initiative", seed, mutated_path)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert load_export("mutated-initiative", seed) == reference_pipeline(mutated_path, seed)


def test_partial_broken_scheduler_fails_initiative_tie() -> None:
    """Correct ingest/bleed/export/simulate cannot mask wrong turn sort key."""
    seed = SEEDS[0]
    install_modules({"scheduler"})
    rebuild_turnctl()
    try:
        proc = run_pipeline("initiative_tie", seed)
        assert proc.returncode == 0
        assert load_export("initiative_tie", seed) != expected("initiative_tie", seed)
    finally:
        restore_broken()
        rebuild_turnctl()


def test_partial_broken_bleed_fails_bleed_timing() -> None:
    """Correct scheduler cannot mask end-of-turn bleed."""
    seed = SEEDS[0]
    install_modules({"bleed"})
    rebuild_turnctl()
    try:
        proc = run_pipeline("bleed_timing", seed)
        assert proc.returncode == 0
        got = load_export("bleed_timing", seed)
        golden = expected("bleed_timing", seed)
        assert got != golden
        assert got["transcript_hash"] != golden["transcript_hash"]
    finally:
        restore_broken()
        rebuild_turnctl()


def test_partial_broken_ingest_fails_negative_bleed() -> None:
    """Correct simulate path cannot mask ingest accepting negative bleed."""
    roster = FIXTURES / "rosters/negative_bleed.json"
    staging = OUTPUT / "negative.staging.json"
    install_modules({"ingest"})
    rebuild_turnctl()
    try:
        proc = ingest_cli(roster, staging)
        assert proc.returncode == 0
        assert staging.exists()
    finally:
        restore_broken()
        rebuild_turnctl()


def test_partial_broken_export_fails_regression_full() -> None:
    """Correct simulate cannot mask export reordering bleed after acts."""
    seed = SEEDS[0]
    install_modules({"export"})
    rebuild_turnctl()
    try:
        proc = run_pipeline("regression_full", seed)
        assert proc.returncode == 0
        assert load_export("regression_full", seed) != expected("regression_full", seed)
    finally:
        restore_broken()
        rebuild_turnctl()


def test_partial_broken_simulate_fails_stun_bleed() -> None:
    """Correct scheduler/bleed cannot mask broken simulate loop ordering."""
    seed = SEEDS[0]
    install_modules({"simulate"})
    rebuild_turnctl()
    try:
        proc = run_pipeline("stun_bleed", seed)
        assert proc.returncode == 0
        got = load_export("stun_bleed", seed)
        golden = expected("stun_bleed", seed)
        stun = next(ev for ev in got["rounds"][0]["events"] if ev["kind"] == "stun_skip")
        assert stun["ap_after"] != next(
            ev for ev in golden["rounds"][0]["events"] if ev["kind"] == "stun_skip"
        )["ap_after"]
    finally:
        restore_broken()
        rebuild_turnctl()


def test_partial_fix_scheduler_and_bleed_insufficient_for_hidden() -> None:
    """Fixing only scheduler and bleed must still fail hidden /opt/verifier-fixtures six-actor bleed."""
    hidden = hidden_roster_path()
    seed = VERIFIER_SEED
    name = "hidden-partial"
    install_modules({"ingest", "export", "simulate"})
    rebuild_turnctl()
    try:
        staging, state, export = paths_for(name, seed)
        proc = ingest_cli(hidden, staging)
        assert proc.returncode == 0
        proc = simulate_cli(staging, seed, state, export)
        assert proc.returncode == 0
        assert json.loads(export.read_text(encoding="utf-8")) != reference_pipeline(hidden, seed)
    finally:
        restore_broken()
        rebuild_turnctl()


def test_partial_broken_scheduler_fails_pinned_death() -> None:
    """Name sort breaks pinned-first ordering for death/pin scenarios."""
    seed = SEEDS[0]
    install_modules({"scheduler"})
    rebuild_turnctl()
    try:
        proc = run_pipeline("pinned_death", seed)
        assert proc.returncode == 0
        assert load_export("pinned_death", seed) != expected("pinned_death", seed)
    finally:
        restore_broken()
        rebuild_turnctl()
