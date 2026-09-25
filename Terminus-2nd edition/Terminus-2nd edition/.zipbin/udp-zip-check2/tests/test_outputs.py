"""Behavioral verifier for udpctl ingest → staging → export."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest

from reference_replayer import reference_replay, reference_staging

APP = Path("/app")
CLI = "/usr/local/bin/udpctl"
BUNDLES = APP / "fixtures/bundles"
OUTPUT = APP / "output"
STATE = APP / "state"
STAGING = STATE / "replay-staging.json"
RESET = APP / "scripts/reset-state.sh"
SEEDS = json.loads((APP / "fixtures/seeds.json").read_text(encoding="utf-8"))
PRIMARY_SEED = SEEDS[0]
HIDDEN_ROOT = Path("/tests/hidden_fixtures/bundles")

ALL_REFERENCE_BUNDLES = [
    "baseline.json",
    "wrap-u32-edge.json",
    "dup-resend.json",
    "out-of-order.json",
    "loss-bitmask.json",
    "partial-tick-batch.json",
]

HIDDEN_BUNDLES = [
    "poison-peer-order.json",
    "staging-gap-recompute.json",
]

PROTECTED_SHA256: dict[str, str] = {
    "bundles/baseline.json": "a2ee566a921aecec4e264751c977f9912f9ac5470cd0abed2aa685817ce885d7",
    "bundles/dup-resend.json": "7079e4ce5d2ed7593e915e058b06d722b61e4e66870541be416be535fd6b2b5a",
    "bundles/loss-bitmask.json": "8a7b019af6675dc0388e2c1b9902202126c2a5094f6c789ffabbf9a36a511c2c",
    "bundles/out-of-order.json": "de2754b79d17e634e1971cc464fcaed2ae72452f6f542f3bfba72a1781bdeaab",
    "bundles/partial-tick-batch.json": "65594367b42ac8b5317fca56607d9084ded8f84f22516c7152ba59ca8c96a117",
    "bundles/wrap-u32-edge.json": "406f90927be45c397f0041b5cccce019c2e55400ef884c5601f232a9ce6ab387",
    "seeds.json": "507afd8488c54ad4db707a35fa1254a7d7c6ab368076c074e1e40f4fcca44862",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False)


def reset() -> None:
    proc = run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def build_cli() -> None:
    proc = run(["cargo", "build", "--release", "--locked", "-p", "udpctl"])
    assert proc.returncode == 0, proc.stderr
    run(["install", "-m", "0755", str(APP / "target/release/udpctl"), CLI])


def ingest_cli(bundle: Path, seed: int) -> subprocess.CompletedProcess[str]:
    return run([CLI, "ingest", "--bundle", str(bundle), "--seed", str(seed)])


def export_cli(out_name: str) -> dict:
    out = OUTPUT / out_name
    proc = run([CLI, "export", "--export", str(out)])
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return json.loads(out.read_text(encoding="utf-8"))


def replay_cli(bundle: str, seed: int, out_name: str) -> dict:
    out = OUTPUT / out_name
    proc = run(
        [
            CLI,
            "replay",
            "--bundle",
            str(BUNDLES / bundle),
            "--seed",
            str(seed),
            "--export",
            str(out),
        ]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return json.loads(out.read_text(encoding="utf-8"))


def load_staging() -> dict:
    return json.loads(STAGING.read_text(encoding="utf-8"))


class TestUdpctl:
    """End-to-end udpctl ingest → staging → export against independent reference."""

    @classmethod
    def setup_class(cls) -> None:
        reset()
        build_cli()

    def test_fixture_integrity(self) -> None:
        """Bundled fixtures must match baked SHA256."""
        assert PROTECTED_SHA256, "PROTECTED_SHA256 not populated"
        for rel, digest in PROTECTED_SHA256.items():
            path = APP / "fixtures" / rel
            assert path.is_file(), rel
            assert sha256_file(path) == digest, rel

    @pytest.mark.parametrize("bundle", ALL_REFERENCE_BUNDLES)
    def test_replay_matches_reference(self, bundle: str) -> None:
        """Each bundled replay fixture must match the independent reference for seed 7."""
        reset()
        got = replay_cli(bundle, PRIMARY_SEED, f"report-{bundle}-{PRIMARY_SEED}.json")
        exp = reference_replay(BUNDLES / bundle, PRIMARY_SEED)
        assert got == exp

    def test_duplicate_resend_applies_sim_on_every_receipt(self) -> None:
        """Duplicate frame_seq resends must still apply sim inputs; only ledger gaps/playhead are idempotent."""
        reset()
        got = replay_cli("dup-resend.json", PRIMARY_SEED, "dup-sim.json")
        exp = reference_replay(BUNDLES / "dup-resend.json", PRIMARY_SEED)
        assert got["ledger"]["duplicate_acks"] == 1
        assert got["sim"]["inputs_applied"] == 4
        assert got["sim"]["inputs_applied"] == exp["sim"]["inputs_applied"]
        assert got["ledger"]["duplicate_acks"] == exp["ledger"]["duplicate_acks"]

    def test_seed_mutates_client_id_and_state_hash(self) -> None:
        """Distinct seeds must change client_id and state_hash on baseline replay."""
        reset()
        base = replay_cli("baseline.json", PRIMARY_SEED, "seed-base.json")
        exp = reference_replay(BUNDLES / "baseline.json", PRIMARY_SEED)
        assert base == exp
        alt = replay_cli("baseline.json", SEEDS[1], "seed-alt.json")
        assert base["client_id"] != alt["client_id"]
        assert base["state_hash"] != alt["state_hash"]

    def test_ingest_writes_staging_snapshot(self) -> None:
        """Ingest must persist replay-staging.json with raw ledger tuples."""
        reset()
        bundle = BUNDLES / "baseline.json"
        assert ingest_cli(bundle, PRIMARY_SEED).returncode == 0
        assert STAGING.is_file()
        got = load_staging()
        exp = reference_staging(bundle, PRIMARY_SEED)
        assert got["bundle_id"] == exp["bundle_id"]
        assert got["seed"] == exp["seed"]
        assert got["ledger_raw"]["gaps_raw"] == exp["ledger_raw"]["gaps_raw"]
        assert got["ledger_raw"]["peer_loss_raw"] == exp["ledger_raw"]["peer_loss_raw"]
        assert got["sim"] == exp["sim"]

    def test_staging_preserves_descending_peer_loss_tuples(self) -> None:
        """Staging must not normalize peer-loss tuples before export merge."""
        reset()
        bundle = BUNDLES / "loss-bitmask.json"
        assert ingest_cli(bundle, PRIMARY_SEED).returncode == 0
        staging = load_staging()
        exp = reference_staging(bundle, PRIMARY_SEED)
        assert staging["ledger_raw"]["peer_loss_raw"] == [list(t) for t in exp["ledger_raw"]["peer_loss_raw"]]
        assert any(s > e for s, e in staging["ledger_raw"]["peer_loss_raw"])

    def test_export_reads_staging_not_bundle(self) -> None:
        """Export must derive the report from staging only."""
        reset()
        bundle = BUNDLES / "baseline.json"
        assert ingest_cli(bundle, PRIMARY_SEED).returncode == 0
        got = export_cli("export-from-staging.json")
        exp = reference_replay(bundle, PRIMARY_SEED)
        assert got == exp

    def test_ingest_export_split_matches_replay(self) -> None:
        """Separate ingest and export must match combined replay."""
        reset()
        bundle = BUNDLES / "out-of-order.json"
        assert ingest_cli(bundle, PRIMARY_SEED).returncode == 0
        split = export_cli("split-export.json")
        reset()
        combined = replay_cli("out-of-order.json", PRIMARY_SEED, "combined.json")
        assert split == combined

    def test_export_without_ingest_fails(self) -> None:
        """Export must fail when staging file is missing."""
        reset()
        proc = run([CLI, "export", "--export", str(OUTPUT / "no-staging.json")])
        assert proc.returncode != 0

    def test_cross_run_reset_clears_staging(self) -> None:
        """Reset script must remove prior staging before a new ingest."""
        reset()
        assert ingest_cli(BUNDLES / "baseline.json", PRIMARY_SEED).returncode == 0
        assert STAGING.is_file()
        reset()
        assert not STAGING.exists()

    def test_partial_tick_batch_staging_sim(self) -> None:
        """Non-contiguous tick_offset batches must still apply every input."""
        reset()
        bundle = BUNDLES / "partial-tick-batch.json"
        assert ingest_cli(bundle, PRIMARY_SEED).returncode == 0
        staging = load_staging()
        exp = reference_staging(bundle, PRIMARY_SEED)
        assert staging["sim"]["inputs_applied"] == exp["sim"]["inputs_applied"]

    def test_wrap_u32_staging_playhead(self) -> None:
        """u32 wrap bundles must stage correct playhead after ingest."""
        reset()
        bundle = BUNDLES / "wrap-u32-edge.json"
        assert ingest_cli(bundle, PRIMARY_SEED).returncode == 0
        staging = load_staging()
        exp = reference_staging(bundle, PRIMARY_SEED)
        assert staging["ledger_raw"]["playhead"] == exp["ledger_raw"]["playhead"]

    def test_peer_loss_export_merge_from_staging(self) -> None:
        """Export merge must use lexicographic tuple order from staged peer_loss_raw."""
        reset()
        bundle = BUNDLES / "loss-bitmask.json"
        assert ingest_cli(bundle, PRIMARY_SEED).returncode == 0
        got = export_cli("loss-export.json")
        exp = reference_replay(bundle, PRIMARY_SEED)
        assert got["ledger"]["peer_loss_gaps"] == exp["ledger"]["peer_loss_gaps"]

    def test_instruction_output_paths_exist(self) -> None:
        """Replay must write /app/output/replay-report.json and ingest /app/state/replay-staging.json."""
        reset()
        report = Path("/app/output/replay-report.json")
        staging = Path("/app/state/replay-staging.json")
        assert ingest_cli(BUNDLES / "baseline.json", PRIMARY_SEED).returncode == 0
        assert staging.is_file()
        proc = run([CLI, "export", "--export", str(report)])
        assert proc.returncode == 0, proc.stderr + proc.stdout
        assert report.is_file()
        assert json.loads(report.read_text(encoding="utf-8"))["bundle_id"] == "baseline"

    def test_replay_export_schema_fields(self) -> None:
        """Replay export must include ledger and sim sections per replay-export doc."""
        reset()
        got = replay_cli("baseline.json", PRIMARY_SEED, "schema-check.json")
        assert "ledger" in got and "sim" in got
        assert "gaps" in got["ledger"] and "peer_loss_gaps" in got["ledger"]
        assert "inputs_applied" in got["sim"]

    def test_out_of_order_received_gaps(self) -> None:
        """Out-of-order delivery must recompute received gaps before export merge."""
        reset()
        got = replay_cli("out-of-order.json", PRIMARY_SEED, "ooo-gaps.json")
        exp = reference_replay(BUNDLES / "out-of-order.json", PRIMARY_SEED)
        assert got["ledger"]["gaps"] == exp["ledger"]["gaps"]

    @pytest.mark.parametrize("bundle", HIDDEN_BUNDLES)
    def test_hidden_bundle_replay_matches_reference(self, bundle: str) -> None:
        """Hidden /tests/hidden_fixtures and /opt/verifier-fixtures bundles match reference."""
        reset()
        path = HIDDEN_ROOT / bundle
        override = os.environ.get("HIDDEN_BUNDLE_ROOT")
        if override:
            alt = Path(override) / bundle
            if alt.is_file():
                path = alt
        opt = Path("/opt/verifier-fixtures/bundles") / bundle
        if opt.is_file():
            path = opt
        assert path.is_file(), bundle
        assert ingest_cli(path, PRIMARY_SEED).returncode == 0
        got = export_cli(f"hidden-{bundle}")
        exp = reference_replay(path, PRIMARY_SEED)
        assert got == exp

    def test_hidden_poison_peer_order_staging_raw(self) -> None:
        """Hidden poison-peer-order traps export-only normalization fixes."""
        reset()
        root = os.environ.get("HIDDEN_BUNDLE_ROOT", str(HIDDEN_ROOT))
        path = Path(root) / "poison-peer-order.json"
        if Path("/opt/verifier-fixtures/bundles/poison-peer-order.json").is_file():
            path = Path("/opt/verifier-fixtures/bundles/poison-peer-order.json")
        assert ingest_cli(path, PRIMARY_SEED).returncode == 0
        staging = load_staging()
        exp = reference_staging(path, PRIMARY_SEED)
        assert staging["ledger_raw"]["peer_loss_raw"] == [list(t) for t in exp["ledger_raw"]["peer_loss_raw"]]

    def test_hidden_gap_recompute_staging(self) -> None:
        """Hidden staging-gap-recompute requires full gap recompute at ingest."""
        reset()
        root = os.environ.get("HIDDEN_BUNDLE_ROOT", str(HIDDEN_ROOT))
        path = Path(root) / "staging-gap-recompute.json"
        if Path("/opt/verifier-fixtures/bundles/staging-gap-recompute.json").is_file():
            path = Path("/opt/verifier-fixtures/bundles/staging-gap-recompute.json")
        assert ingest_cli(path, PRIMARY_SEED).returncode == 0
        staging = load_staging()
        exp = reference_staging(path, PRIMARY_SEED)
        assert staging["ledger_raw"]["gaps_raw"] == exp["ledger_raw"]["gaps_raw"]
        got = export_cli("hidden-gap-export.json")
        assert got["ledger"]["gaps"] == reference_replay(path, PRIMARY_SEED)["ledger"]["gaps"]
