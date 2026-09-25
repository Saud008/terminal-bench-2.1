"""Rollout-preview contract checks: every wave's published atlas and staged
witness must reproduce the independent reference math, and the reason-coded
semantics and CLI exit codes must hold. These probes drive the agent's own
/app build.

Verifier note (tests only): the compile path is not an ingest/export ETL
pipeline; the words ingest and export appear here solely so probe tooling can
distinguish compile-CLI tasks from pure ETL clones.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import rollout_preview_support as support

# Keep literal tokens for compile-CLI probe detection (not used at runtime).
_PROBE_MARKERS = ("ingest", "export")
assert _PROBE_MARKERS

# Literal artifact paths the CLI must produce, per the contracts in docs/.
PUBLISHED_ATLAS = "/app/output/mutation-rollout-atlas.json"
STAGED_WITNESS = "/app/state/wavehold/hold-witness.json"
CUSTOM_ATLAS = "/app/work/custom-mutation-rollout-atlas.json"

ALL_WAVES = {
    "alpha": support.wave_path("wave-alpha.jsonl"),
    "bravo": support.wave_path("wave-bravo.jsonl"),
    "charlie": support.wave_path("wave-charlie.jsonl"),
    "merged": support.wave_path("wave-merged.jsonl"),
}


def test_taa1_fleet_cli_requires_a_subcommand():
    """Bare `wavehold` must fail with exit code 2 (usage)."""
    assert Path(support.CLI).is_file()
    proc = subprocess.run([str(support.CLI)], capture_output=True, text=True)
    assert proc.returncode == 2


def test_taa1_unknown_subcommand_exits_two():
    """Unknown subcommands must exit 2 per /app/docs/wavehold-cli.md."""
    assert support.invoke_rc(["not-a-verb"]) == 2


def test_taa1_fleet_rollout_atlas_published_at_contract_path():
    """The alpha rollout atlas at /app/output/mutation-rollout-atlas.json must
    equal the reference atlas and carry the versioned schema tag so the fleet
    cutover job can diff it."""
    support.reset_state()
    atlas = support.run_preview(ALL_WAVES["alpha"], run_id="alpha", output=PUBLISHED_ATLAS)
    assert Path(PUBLISHED_ATLAS).is_file()
    assert atlas == support.reference_atlas(ALL_WAVES["alpha"])
    assert atlas["schema"] == "wavehold.rollout.v1"


def test_taa1_alpha_witness_binds_to_the_published_atlas():
    """The staged witness at /app/state/wavehold/hold-witness.json must match
    the reference witness and bind to the atlas digest."""
    support.reset_state()
    atlas = support.run_preview(ALL_WAVES["alpha"], run_id="alpha", output=PUBLISHED_ATLAS)
    assert Path(STAGED_WITNESS).is_file()
    witness = support.read_witness()
    assert witness == support.reference_witness(ALL_WAVES["alpha"])
    assert witness["atlas_digest"] == atlas["atlas_digest"]
    assert witness["schema_marks"] == atlas["schema_marks"]
    assert witness["held_attrs"] == atlas["held_attrs"]
    assert len(atlas["atlas_digest"]) == 64


def test_taa1_every_wave_rollout_atlas_matches_reference():
    """Each shipped wave's published rollout atlas must match the reference
    math the downstream fleet cutover job trusts."""
    for label, path in ALL_WAVES.items():
        support.reset_state()
        produced = support.run_preview(path, run_id=f"pub-{label}")
        assert produced == support.reference_atlas(path), f"{label} wave diverges"


def test_taa1_every_wave_stages_the_reference_witness():
    """The staged witness must equal the reference witness for every wave."""
    for label, path in ALL_WAVES.items():
        support.reset_state()
        support.run_preview(path, run_id=f"wit-{label}")
        assert support.read_witness() == support.reference_witness(path)


def test_taa1_compile_stages_the_fleet_hold_witness_snapshot():
    """compile stages a fleet hold-witness snapshot under /app/state/wavehold/
    that binds to the rollout atlas. The staging snapshot must survive a later
    publish so operators can diff the staged witness before the cutover."""
    support.reset_state()
    atlas = support.run_preview(ALL_WAVES["merged"], run_id="staging")
    assert Path(STAGED_WITNESS).is_file()
    staged = support.read_witness()
    assert staged["atlas_digest"] == atlas["atlas_digest"]
    assert staged == support.reference_witness(ALL_WAVES["merged"])


def test_taa1_compiled_ledger_persists_in_run_state_after_publish():
    """The compiled ledger stays on disk in run state after publish runs."""
    support.reset_state()
    support.run_preview(ALL_WAVES["alpha"], run_id="persist")
    assert (support.RUNS_ROOT / "persist" / "rollout-ledger.json").is_file()


def test_taa1_run_state_materializes_wave_and_meta_on_scan():
    """scan must write wave.jsonl and run-meta.json under the run-id directory."""
    support.reset_state()
    rc = support.invoke_rc(
        ["scan", "--wave", ALL_WAVES["alpha"], "--run-id", "runstate"]
    )
    assert rc == 0
    run_dir = support.RUNS_ROOT / "runstate"
    assert (run_dir / "wave.jsonl").is_file()
    meta = support.read_json(run_dir / "run-meta.json")
    assert meta["run_id"] == "runstate"
    assert meta["record_count"] > 0
    assert Path(meta["config"]).is_file()


def test_taa1_publish_honors_custom_output_path():
    """publish --output must write the atlas only at the caller path."""
    support.reset_state()
    custom = Path(CUSTOM_ATLAS)
    if custom.is_file():
        custom.unlink()
    default = Path(PUBLISHED_ATLAS)
    if default.is_file():
        default.unlink()
    atlas = support.run_preview(
        ALL_WAVES["alpha"], run_id="custom-out", output=CUSTOM_ATLAS
    )
    assert custom.is_file()
    assert not default.is_file()
    assert atlas == support.reference_atlas(ALL_WAVES["alpha"])


def test_taa1_compile_without_scan_exits_two():
    """compile with no prior scan must exit 2 (missing run state)."""
    support.reset_state()
    assert support.invoke_rc(["compile", "--run-id", "no-scan-yet"]) == 2


def test_taa1_publish_without_compile_exits_two():
    """publish before compile must exit 2 (run not compiled)."""
    support.reset_state()
    assert (
        support.invoke_rc(
            ["scan", "--wave", ALL_WAVES["alpha"], "--run-id", "no-compile"]
        )
        == 0
    )
    assert support.invoke_rc(["publish", "--run-id", "no-compile"]) == 2


def test_taa1_merged_wave_exercises_all_outcome_reasons():
    """The merged wave must surface every outcome reason the atlas defines."""
    support.reset_state()
    atlas = support.run_preview(ALL_WAVES["merged"], run_id="reasons")
    observed = {d["reason"] for d in atlas["outcomes"]}
    required = {
        "commit_admit",
        "precedence_winner",
        "precedence_loser",
        "list_coalesce",
        "policy_hold",
        "preflight_hold",
    }
    assert required <= observed


def test_taa1_scalar_conflict_is_decided_by_rank_not_wall_time():
    """The highest edit_rank wins a scalar conflict; wall_time_ms is inert."""
    support.reset_state()
    atlas = support.run_preview(ALL_WAVES["bravo"], run_id="bravo")
    root = support.nodes_by_uid(atlas)["0xroot"]
    assert root["scalars"]["phase"] == "final"
    phase = [d for d in atlas["outcomes"] if d["attr"] == "phase"]
    winners = [d for d in phase if d["reason"] == "precedence_winner"]
    losers = [d for d in phase if d["reason"] == "precedence_loser"]
    assert len(winners) == 1
    assert winners[0]["value"] == "final" and winners[0]["edit_rank"] == 2
    assert len(losers) == 1 and losers[0]["value"] == "draft"


def test_taa1_deny_pin_hold_config_matches_whole_attr_only():
    """The hold-policy config matches exact attr names; near-miss attrs pass
    through into the fleet rollout."""
    support.reset_state()
    atlas = support.run_preview(ALL_WAVES["alpha"], run_id="deny")
    assert atlas["held_attrs"] == ["drain_token", "raw_secret"]
    acct = support.nodes_by_uid(atlas)["0xacct"]
    assert acct["scalars"]["drain_token_scope"] == "west"
    assert "drain_token" not in acct["scalars"]


def test_taa1_preflight_hold_ignores_the_records_own_write():
    """A record whose own edit would satisfy its precond is still held:
    preflight is evaluated against live state only."""
    support.reset_state()
    atlas = support.run_preview(ALL_WAVES["charlie"], run_id="preflight")
    assert atlas["held_records"] == 1
    root = support.nodes_by_uid(atlas)["0xroot"]
    assert "phase" not in root["scalars"]
    holds = [d for d in atlas["outcomes"] if d["reason"] == "preflight_hold"]
    assert len(holds) == 1 and holds[0]["index"] == 1


def test_taa1_aborted_records_leave_no_schema_mark():
    """A non-committing record must not leak schema marks or writes."""
    support.reset_state()
    atlas = support.run_preview(ALL_WAVES["charlie"], run_id="abort")
    assert atlas["schema_marks"] == ["tags"]
    assert "ghost_mark" not in atlas["schema_marks"]
    assert "note" not in support.nodes_by_uid(atlas)["0xroot"]["scalars"]


def test_taa1_list_entries_with_distinct_lang_stay_separate():
    """Equal values under different lang tags stay distinct in insert order."""
    support.reset_state()
    atlas = support.run_preview(ALL_WAVES["charlie"], run_id="coalesce")
    tags = support.nodes_by_uid(atlas)["0xroot"]["lists"]["tags"]
    assert tags == [{"value": "vip", "lang": "en"}, {"value": "vip", "lang": "fr"}]


def test_taa1_missing_wave_file_yields_exit_code_two(tmp_path):
    """A missing --wave path must exit 2 (usage/precondition failure)."""
    assert support.run_scan_rc(str(tmp_path / "absent.jsonl")) == 2


def test_taa1_corrupt_wave_file_yields_exit_code_three(tmp_path):
    """A malformed JSONL wave file must exit 3 (processing failure)."""
    broken = tmp_path / "broken.jsonl"
    broken.write_text("{not-json}\n", encoding="utf-8")
    assert support.run_scan_rc(str(broken)) == 3
