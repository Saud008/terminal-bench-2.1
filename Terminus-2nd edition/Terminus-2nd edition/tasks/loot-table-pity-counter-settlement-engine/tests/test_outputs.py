"""Behavioral verifier for lootsettle pity settlement pipeline."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path

import pytest

from reference_settlement import (
    events_digest,
    mutate_carry_ratio,
    mutate_duplicate_shards,
    reference_replay,
    reference_staging,
)

APP = Path("/app")
CLI = "/usr/local/bin/lootsettle"
REPORT = Path("/app/output/settlement-report.json")
STAGING = Path("/app/state/settlement-staging.json")
STAGING_SEQ = Path("/app/state/staging-seq.json")
GENERATION = Path("/app/state/replay-generation.json")
PITY_LEDGER = Path("/app/state/pity-ledger.json")
PROCESSED = Path("/app/state/processed-events.json")
SEASON = APP / "fixtures" / "seasons" / "winter-alpha.json"
EVENTS = APP / "fixtures" / "events" / "alpha-stream.jsonl"
SEASONS_DIR = APP / "fixtures" / "seasons"
RESET = APP / "scripts" / "reset-state.sh"
TB3_SEASON = Path("/opt/verifier-fixtures/loot-gamma/season-gamma.json")
TB3_EVENTS = Path("/opt/verifier-fixtures/loot-gamma/gamma-stream.jsonl")
CATALOG = json.loads((APP / "fixtures" / "catalog.json").read_text(encoding="utf-8"))
SEEDS = CATALOG["seeds"]
CORE = APP / "crates" / "lootsettle-core" / "src"
PATCHES = Path(__file__).resolve().parent / "patches"

PATCH_TARGETS = {
    "envelope": CORE / "envelope.rs",
    "pity": CORE / "pity.rs",
    "pool": CORE / "pool" / "mod.rs",
    "duplicate": CORE / "duplicate.rs",
    "idempotent": CORE / "idempotent.rs",
    "staging": CORE / "staging.rs",
    "export": CORE / "export.rs",
}
PATCH_MODULES = tuple(PATCH_TARGETS.keys())
PIPELINE_MODULES = ["envelope", "pity", "pool", "duplicate", "idempotent", "staging"]

PROTECTED = [
    "fixtures/catalog.json",
    "fixtures/seasons/winter-alpha.json",
    "fixtures/seasons/spring-beta.json",
    "fixtures/events/alpha-stream.jsonl",
    "docs/event-envelope.md",
    "docs/pity-carryover.md",
    "docs/pool-epoch.md",
    "docs/duplicate-shards.md",
    "docs/replay-idempotency.md",
    "docs/settlement-export.md",
    "docs/cli-surface.md",
    "docs/module-interface-contract.md",
]


def _sha256(rel: str) -> str:
    return hashlib.sha256((APP / rel).read_bytes()).hexdigest()


PROTECTED_SHA256 = {rel: _sha256(rel) for rel in PROTECTED}


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False)


def reset() -> None:
    proc = run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def rebuild_cli() -> None:
    proc = run(["cargo", "build", "--release", "--locked", "-p", "lootsettle-cli"])
    assert proc.returncode == 0, proc.stderr or proc.stdout
    proc = run(["install", "-m", "0755", "/app/target/release/lootsettle", CLI])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def ingest_cli(*, season: Path = SEASON, events: Path = EVENTS) -> subprocess.CompletedProcess[str]:
    return run([CLI, "ingest", "--season", str(season), "--events", str(events)])


def settle_cli(*, seasons_dir: Path = SEASONS_DIR) -> subprocess.CompletedProcess[str]:
    return run([CLI, "settle", "--seasons-dir", str(seasons_dir)])


def export_cli(*, output: Path = REPORT) -> subprocess.CompletedProcess[str]:
    return run([CLI, "export", "--output", str(output)])


def replay_cli(
    *,
    season: Path = SEASON,
    events: Path = EVENTS,
    seasons_dir: Path = SEASONS_DIR,
    output: Path = REPORT,
) -> subprocess.CompletedProcess[str]:
    return run(
        [
            CLI,
            "replay",
            "--season",
            str(season),
            "--events",
            str(events),
            "--seasons-dir",
            str(seasons_dir),
            "--output",
            str(output),
        ]
    )


def read_staging() -> dict:
    assert STAGING.is_file(), "settlement-staging.json missing"
    return json.loads(STAGING.read_text(encoding="utf-8"))


def read_report() -> dict:
    assert REPORT.is_file(), "settlement-report.json missing"
    return json.loads(REPORT.read_text(encoding="utf-8"))


def restore_shipping_modules() -> None:
    for name in PATCH_MODULES:
        shutil.copy(PATCHES / f"broken_{name}.rs", PATCH_TARGETS[name])


@contextmanager
def patched_modules(names: list[str]):
    originals = {mod: PATCH_TARGETS[mod].read_text(encoding="utf-8") for mod in PATCH_MODULES}
    try:
        restore_shipping_modules()
        for name in names:
            shutil.copy(PATCHES / f"golden_{name}.rs", PATCH_TARGETS[name])
        rebuild_cli()
        yield
    finally:
        for mod, content in originals.items():
            PATCH_TARGETS[mod].write_text(content, encoding="utf-8")
        rebuild_cli()


@contextmanager
def patched_module(name: str):
    with patched_modules([name]):
        yield


@pytest.fixture(autouse=True)
def _reset_state() -> None:
    reset()


def test_fixture_integrity() -> None:
    """Protected docs and fixture bytes must remain unchanged."""
    for rel, expected in PROTECTED_SHA256.items():
        assert _sha256(rel) == expected


def test_output_artifact_paths_written() -> None:
    """Instruction output paths exist after a successful replay run."""
    proc = replay_cli()
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert str(REPORT) == "/app/output/settlement-report.json"
    assert REPORT.is_file()
    assert STAGING.is_file()
    assert STAGING_SEQ.is_file()
    assert PITY_LEDGER.is_file()
    assert GENERATION.is_file()


def test_ingest_writes_staging_seq_counter() -> None:
    """Ingest bumps /app/state/staging-seq.json staging_generation counter."""
    proc = ingest_cli()
    assert proc.returncode == 0, proc.stderr or proc.stdout
    seq = json.loads(STAGING_SEQ.read_text(encoding="utf-8"))
    staging = read_staging()
    assert seq["staging_generation"] == staging["staging_generation"]
    assert seq["staging_generation"] >= 1


def test_replay_exit_success() -> None:
    """Replay exits 0 and writes settlement report."""
    proc = replay_cli()
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert REPORT.is_file()


def test_ingest_writes_staging_digest() -> None:
    """Ingest writes staging snapshot with events_digest binding."""
    proc = ingest_cli()
    assert proc.returncode == 0, proc.stderr or proc.stdout
    staging = read_staging()
    season = json.loads(SEASON.read_text(encoding="utf-8"))
    events = [
        json.loads(line)
        for line in EVENTS.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    expected = reference_staging(events, season, staging_generation=staging["staging_generation"])
    assert staging["events_digest"] == expected["events_digest"]
    assert staging["pool_epoch"] == season["pool_epoch"]


def test_staging_digest_matches_reference() -> None:
    """Staging digest uses canonical bodies in timestamp order."""
    proc = ingest_cli()
    assert proc.returncode == 0, proc.stderr or proc.stdout
    staging = read_staging()
    assert staging["events_digest"] == events_digest(staging["events"])


def test_report_matches_reference() -> None:
    """Settlement report matches independent reference replay."""
    expected = reference_replay(SEASON, EVENTS, SEASONS_DIR, staging_generation=1, generation_start=0)
    proc = replay_cli()
    assert proc.returncode == 0, proc.stderr or proc.stdout
    actual = read_report()
    assert actual == expected


def test_partial_pipeline_settle_ok_export_wrong() -> None:
    """Correct ingest/settle stages still fail export validation when export stays broken."""
    with patched_modules(PIPELINE_MODULES):
        reset()
        expected = reference_replay(SEASON, EVENTS, SEASONS_DIR, staging_generation=1, generation_start=0)
        proc = replay_cli()
        assert proc.returncode == 0, proc.stderr or proc.stdout
        actual = read_report()
        assert actual != expected
        assert not actual.get("settlement_digest")


def test_partial_export_only_still_wrong() -> None:
    """Golden export alone cannot fix broken envelope signatures on bundled fixtures."""
    with patched_module("export"):
        reset()
        proc = replay_cli()
        assert proc.returncode != 0, proc.stderr or proc.stdout


def test_duplicate_shards_alpha_stream() -> None:
    """Second iron-ring pull converts to common duplicate shards."""
    expected = reference_replay(SEASON, EVENTS, SEASONS_DIR, staging_generation=1, generation_start=0)
    proc = replay_cli()
    assert proc.returncode == 0, proc.stderr or proc.stdout
    player = read_report()["players"]["player-aurora-7"]
    assert player["shards"] == expected["players"]["player-aurora-7"]["shards"] == 5
    assert player["inventory"].count("iron-ring") == 1


def test_pity_resets_on_legendary_pull() -> None:
    """Legendary grant zeroes pity before spring season pull increments it."""
    expected = reference_replay(SEASON, EVENTS, SEASONS_DIR, staging_generation=1, generation_start=0)
    proc = replay_cli()
    assert proc.returncode == 0, proc.stderr or proc.stdout
    pity = read_report()["players"]["player-aurora-7"]["pity_legendary"]
    assert pity == expected["players"]["player-aurora-7"]["pity_legendary"] == 1


def test_generation_gate_blocks_export_before_settle() -> None:
    """Export rejects generation 0 before settle bumps replay-generation."""
    proc = ingest_cli()
    assert proc.returncode == 0, proc.stderr or proc.stdout
    proc = export_cli()
    assert proc.returncode != 0, proc.stderr or proc.stdout


def test_idempotent_resettle_skips_duplicate_event_ids() -> None:
    """Second settle pass records duplicate_skip without double credit."""
    proc = replay_cli()
    assert proc.returncode == 0, proc.stderr or proc.stdout
    first = read_report()
    proc = settle_cli()
    assert proc.returncode == 0, proc.stderr or proc.stdout
    proc = export_cli()
    assert proc.returncode == 0, proc.stderr or proc.stdout
    second = read_report()
    assert second["players"] == first["players"]
    assert any(row.get("action") == "duplicate_skip" for row in second["audit_log"])


def test_stale_staging_digest_blocks_export() -> None:
    """Export rejects staging when events_digest is tampered."""
    proc = ingest_cli()
    assert proc.returncode == 0, proc.stderr or proc.stdout
    proc = settle_cli()
    assert proc.returncode == 0, proc.stderr or proc.stdout
    staging = read_staging()
    staging["events_digest"] = "0" * 64
    STAGING.write_text(json.dumps(staging, indent=2), encoding="utf-8")
    proc = export_cli()
    assert proc.returncode != 0, proc.stderr or proc.stdout


def test_tb3_gamma_duplicate_shards_hidden() -> None:
    """Hidden gamma fixture converts duplicate vault-key pulls into rare shards."""
    assert TB3_SEASON.is_file(), "TB3 season fixture missing"
    expected = reference_replay(
        TB3_SEASON,
        TB3_EVENTS,
        TB3_SEASON.parent,
        staging_generation=1,
        generation_start=0,
    )
    proc = replay_cli(season=TB3_SEASON, events=TB3_EVENTS, seasons_dir=TB3_SEASON.parent)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    player = read_report()["players"]["player-vault-13"]
    assert player["shards"] == expected["players"]["player-vault-13"]["shards"] == 25


def test_tb3_gamma_report_matches_reference_hidden() -> None:
    """Hidden gamma stream matches independent reference settlement report."""
    assert TB3_EVENTS.is_file(), "TB3 events fixture missing"
    expected = reference_replay(
        TB3_SEASON,
        TB3_EVENTS,
        TB3_SEASON.parent,
        staging_generation=1,
        generation_start=0,
    )
    proc = replay_cli(season=TB3_SEASON, events=TB3_EVENTS, seasons_dir=TB3_SEASON.parent)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert read_report() == expected


def test_decoy_weight_merge_not_on_export_hot_path() -> None:
    """decoy.rs is off the export hot path; decoy edits must not change settlement output."""
    decoy_path = CORE / "decoy.rs"
    original = decoy_path.read_text(encoding="utf-8")
    decoy = original + "\npub fn export_merge_hook(report_players: usize) -> usize { report_players + 99 }\n"
    decoy_path.write_text(decoy, encoding="utf-8")
    rebuild_cli()
    try:
        expected = reference_replay(SEASON, EVENTS, SEASONS_DIR, staging_generation=1, generation_start=0)
        proc = replay_cli()
        assert proc.returncode == 0, proc.stderr or proc.stdout
        assert read_report() == expected
    finally:
        decoy_path.write_text(original, encoding="utf-8")
        rebuild_cli()


def test_audit_log_sorted_by_timestamp_seq_event() -> None:
    """Audit log is sorted by timestamp_ms, seq, event_id."""
    expected = reference_replay(SEASON, EVENTS, SEASONS_DIR, staging_generation=1, generation_start=0)
    proc = replay_cli()
    assert proc.returncode == 0, proc.stderr or proc.stdout
    actual = read_report()["audit_log"]
    assert actual == expected["audit_log"]
    keys = [(row["timestamp_ms"], row["seq"], row["event_id"]) for row in actual]
    assert keys == sorted(keys)


def test_settlement_digest_present_and_stable() -> None:
    """Report includes non-empty settlement_digest matching reference."""
    expected = reference_replay(SEASON, EVENTS, SEASONS_DIR, staging_generation=1, generation_start=0)
    proc = replay_cli()
    assert proc.returncode == 0, proc.stderr or proc.stdout
    actual = read_report()
    assert actual["settlement_digest"] == expected["settlement_digest"]
    assert len(actual["settlement_digest"]) == 64


def test_inventory_sorted_lexicographic() -> None:
    """Granted inventory lists stay lexicographically sorted."""
    proc = replay_cli()
    assert proc.returncode == 0, proc.stderr or proc.stdout
    inventory = read_report()["players"]["player-aurora-7"]["inventory"]
    assert inventory == sorted(inventory)


@pytest.mark.parametrize("seed", SEEDS)
def test_seed_mutated_carry_ratio_matches_reference(seed: str) -> None:
    """Mutated carry_ratio per seed blocks static pity output."""
    season = json.loads(SEASON.read_text(encoding="utf-8"))
    mutated = mutate_carry_ratio(season, seed)
    with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
        tmp_path = Path(tmp)
        seasons_dir = tmp_path / "seasons"
        seasons_dir.mkdir()
        for path in SEASONS_DIR.glob("*.json"):
            shutil.copy(path, seasons_dir / path.name)
        season_path = seasons_dir / "winter-alpha.json"
        season_path.write_text(json.dumps(mutated), encoding="utf-8")
        expected = reference_replay(season_path, EVENTS, seasons_dir, staging_generation=1, generation_start=0)
        proc = replay_cli(season=season_path, seasons_dir=seasons_dir)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        assert read_report() == expected


@pytest.mark.parametrize("seed", SEEDS)
def test_seed_mutated_duplicate_shards_matches_reference(seed: str) -> None:
    """Mutated duplicate shard table per seed blocks hardcoded shard totals."""
    season = json.loads(SEASON.read_text(encoding="utf-8"))
    mutated = mutate_duplicate_shards(season, seed)
    with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
        tmp_path = Path(tmp)
        seasons_dir = tmp_path / "seasons"
        seasons_dir.mkdir()
        for path in SEASONS_DIR.glob("*.json"):
            shutil.copy(path, seasons_dir / path.name)
        season_path = seasons_dir / "winter-alpha.json"
        season_path.write_text(json.dumps(mutated), encoding="utf-8")
        expected = reference_replay(season_path, EVENTS, seasons_dir, staging_generation=1, generation_start=0)
        proc = replay_cli(season=season_path, seasons_dir=seasons_dir)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        assert read_report() == expected


@pytest.mark.parametrize("module_name", PATCH_MODULES)
def test_isolated_module_fix_required(module_name: str) -> None:
    """Golden module patch must satisfy module-specific settlement checks."""
    modules = [module_name] if module_name == "envelope" else ["envelope", module_name]
    with patched_modules(modules):
        reset()
        expected = reference_replay(SEASON, EVENTS, SEASONS_DIR, staging_generation=1, generation_start=0)
        proc = replay_cli()
        assert proc.returncode == 0, proc.stderr or proc.stdout
        actual = read_report()
        if module_name == "export":
            audit_keys = [(a["timestamp_ms"], a["seq"], a["event_id"]) for a in actual["audit_log"]]
            assert audit_keys == sorted(audit_keys)
            assert len(actual["settlement_digest"]) == 64
            assert actual["settlement_digest"] != "0" * 64
        elif module_name == "staging":
            staging = read_staging()
            assert staging["events_digest"] == events_digest(staging["events"])
        elif module_name == "duplicate":
            assert actual["players"]["player-aurora-7"]["shards"] == 5
        elif module_name == "idempotent":
            proc = settle_cli()
            assert proc.returncode == 0, proc.stderr or proc.stdout
            proc = export_cli()
            assert proc.returncode == 0, proc.stderr or proc.stdout
            dup = read_report()
            assert any(r.get("action") == "duplicate_skip" for r in dup["audit_log"])
        elif module_name == "envelope":
            proc = ingest_cli()
            assert proc.returncode == 0, proc.stderr or proc.stdout
        elif module_name == "pool":
            bad = EVENTS.read_text(encoding="utf-8").replace('"pool_epoch":2', '"pool_epoch":99', 1)
            with tempfile.NamedTemporaryFile("w", suffix=".jsonl", dir="/tmp", delete=False) as fh:
                fh.write(bad)
                bad_path = Path(fh.name)
            try:
                proc = ingest_cli(events=bad_path)
                assert proc.returncode != 0, proc.stderr or proc.stdout
            finally:
                bad_path.unlink(missing_ok=True)
        elif module_name == "pity":
            assert (
                actual["players"]["player-aurora-7"]["pity_legendary"]
                == expected["players"]["player-aurora-7"]["pity_legendary"]
            )
        else:
            assert actual["players"] == expected["players"]
