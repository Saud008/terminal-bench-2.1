"""Behavioral verifier for FIX drop-copy session bust ledger."""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
from pathlib import Path

import pytest
from reference_replay import reference_compliance

APP = Path("/app")
CLI = "/app/bin/dropcopyctl"
RESET = APP / "scripts" / "reset-state.sh"
STAGE = APP / "state/dropcopy-stage.json"
GENERATION = APP / "state/replay-generation.json"
DB = APP / "work/dropcopy.db"
FIXTURES = APP / "fixtures"
HIDDEN = Path("/opt/verifier-fixtures/dropcopy")
STAGE_PATH = "/app/state/dropcopy-stage.json"
GENERATION_PATH = "/app/state/replay-generation.json"
DB_PATH = "/app/work/dropcopy.db"
SEEDS = json.loads((FIXTURES / "seeds.json").read_text(encoding="utf-8"))["seeds"]

SCENARIOS = ["bust-chain", "cancel-correct", "seq-reset", "execid-dup"]


def run(cmd: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False, env=merged)


def reset() -> None:
    proc = run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def pipeline(seed: str, scenario: str, fixture_dir: Path | None = None, out_name: str | None = None) -> Path:
    root = fixture_dir or FIXTURES
    env = {}
    if fixture_dir is not None:
        env["TB3_FIXTURE_DIR"] = str(fixture_dir)
    for step in (
        [CLI, "ingest", "--seed", seed, "--scenario", scenario, "--fixture-dir", str(root)],
        [CLI, "replay", "--scenario", scenario],
    ):
        proc = run(step, env=env)
        assert proc.returncode == 0, proc.stderr + proc.stdout
    out = APP / "output" / (out_name or f"{seed}-{scenario}-compliance.json")
    proc = run(
        [CLI, "export", "--scenario", scenario, "--output", str(out), "--fixture-dir", str(root)],
        env=env,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return out


class TestOutputPaths:
    def test_ingest_writes_dropcopy_stage_json(self) -> None:
        """Instruction requires ingest to write /app/state/dropcopy-stage.json."""
        reset()
        assert str(STAGE) == STAGE_PATH
        proc = run([CLI, "ingest", "--seed", SEEDS[0], "--scenario", "bust-chain", "--fixture-dir", str(FIXTURES)])
        assert proc.returncode == 0
        assert Path(STAGE_PATH).is_file()

    def test_replay_writes_replay_generation_json(self) -> None:
        """Replay must bump /app/state/replay-generation.json after ledger replay."""
        reset()
        assert str(GENERATION) == GENERATION_PATH
        pipeline(SEEDS[0], "bust-chain")
        assert Path(GENERATION_PATH).is_file()
        assert json.loads(Path(GENERATION_PATH).read_text(encoding="utf-8"))["replay_generation"] >= 1

    def test_replay_persists_sqlite_dropcopy_db(self) -> None:
        """Replay must persist rows into /app/work/dropcopy.db for export."""
        reset()
        assert str(DB) == DB_PATH
        pipeline(SEEDS[1], "execid-dup")
        assert Path(DB_PATH).is_file()
        con = sqlite3.connect(DB_PATH)
        try:
            n = con.execute("SELECT COUNT(*) FROM ledger_rows").fetchone()[0]
        finally:
            con.close()
        assert n >= 1


class TestIngestStaging:
    def test_staging_events_sorted_by_sending_time(self) -> None:
        """Staging snapshot events must be sorted by sending_time then msg_seq."""
        reset()
        run([CLI, "ingest", "--seed", SEEDS[0], "--scenario", "seq-reset", "--fixture-dir", str(FIXTURES)])
        snap = json.loads(STAGE.read_text(encoding="utf-8"))
        times = [(e["sending_time"], e.get("msg_seq", 0)) for e in snap["events"]]
        assert times == sorted(times)

    def test_staging_records_reset_seq_flag(self) -> None:
        """Sequence reset logon rows must set reset_seq true in staging."""
        reset()
        run([CLI, "ingest", "--seed", SEEDS[0], "--scenario", "seq-reset", "--fixture-dir", str(FIXTURES)])
        snap = json.loads(STAGE.read_text(encoding="utf-8"))
        assert any(e.get("reset_seq") for e in snap["events"])


class TestReplayLifecycle:
    @pytest.mark.parametrize("scenario", SCENARIOS)
    def test_compliance_export_matches_reference(self, scenario: str) -> None:
        """Export compliance rollup must match independent reference replay."""
        reset()
        seed = SEEDS[0]
        out = pipeline(seed, scenario)
        body = json.loads(out.read_text(encoding="utf-8"))
        ref = reference_compliance(FIXTURES, scenario)
        assert body["net_positions"] == ref["net_positions"]
        assert body["active_exec_ids"] == ref["active_exec_ids"]
        assert body["audit_digest"] == ref["audit_digest"]

    def test_bust_chain_zeros_net_position(self) -> None:
        """Trade bust ExecType H must reverse prior fill signed quantity."""
        reset()
        out = pipeline(SEEDS[1], "bust-chain")
        body = json.loads(out.read_text(encoding="utf-8"))
        assert body["net_positions"].get("AAPL", 0) == 0
        assert body["bust_count"] >= 1

    def test_cancel_correct_precedence(self) -> None:
        """Correct ExecTransType 2 must supersede earlier cancel on same chain."""
        reset()
        out = pipeline(SEEDS[2], "cancel-correct")
        body = json.loads(out.read_text(encoding="utf-8"))
        assert body["net_positions"].get("MSFT", 0) == -30
        assert body["correction_count"] >= 1

    def test_execid_idempotency_ignores_duplicate(self) -> None:
        """Duplicate ExecID rows must not double-count net qty."""
        reset()
        out = pipeline(SEEDS[0], "execid-dup")
        body = json.loads(out.read_text(encoding="utf-8"))
        assert body["net_positions"].get("GOOG", 0) == 5

    def test_export_refuses_before_replay(self) -> None:
        """Export must fail when replay_generation gate is unset."""
        reset()
        run([CLI, "ingest", "--seed", SEEDS[0], "--scenario", "bust-chain", "--fixture-dir", str(FIXTURES)])
        out = APP / "output" / "early.json"
        proc = run([CLI, "export", "--scenario", "bust-chain", "--output", str(out)])
        assert proc.returncode != 0


class TestHiddenTraps:
    def test_tb3_seq_bias_hidden_scenario(self) -> None:
        """TB3_SEQ_BIAS hidden trap must shift msg_seq and preserve reference net."""
        reset()
        hidden_root = "/opt/verifier-fixtures/dropcopy"
        env = {"TB3_SEQ_BIAS": "3", "TB3_FIXTURE_DIR": hidden_root}
        proc = run(
            [CLI, "ingest", "--seed", SEEDS[3], "--scenario", "seq-bias-trap", "--fixture-dir", hidden_root],
            env=env,
        )
        assert proc.returncode == 0
        proc = run([CLI, "replay", "--scenario", "seq-bias-trap"], env=env)
        assert proc.returncode == 0
        out = APP / "output" / "tb3.json"
        proc = run(
            [CLI, "export", "--scenario", "seq-bias-trap", "--output", str(out), "--fixture-dir", hidden_root],
            env=env,
        )
        assert proc.returncode == 0
        body = json.loads(out.read_text(encoding="utf-8"))
        ref = reference_compliance(HIDDEN, "seq-bias-trap", seq_bias=3)
        assert body["net_positions"] == ref["net_positions"]

    def test_rollback_trap_leaves_db_empty(self) -> None:
        """SQLite batch rollback must leave /app/work/dropcopy.db empty on seq failure."""
        reset()
        hidden_root = "/opt/verifier-fixtures/dropcopy"
        run([CLI, "ingest", "--seed", "alpha", "--scenario", "rollback-trap", "--fixture-dir", hidden_root])
        proc = run([CLI, "replay", "--scenario", "rollback-trap"])
        assert proc.returncode != 0
        if DB.exists():
            con = sqlite3.connect(DB)
            try:
                n = con.execute("SELECT COUNT(*) FROM ledger_rows").fetchone()[0]
            finally:
                con.close()
            assert n == 0

    def test_bad_checksum_ingest_rejects_staging(self) -> None:
        """Invalid FIX checksum stream must fail ingest without leaving staging artifact."""
        reset()
        hidden_root = "/opt/verifier-fixtures/dropcopy"
        assert not STAGE.exists()
        proc = run(
            [CLI, "ingest", "--seed", "beta", "--scenario", "bad-checksum", "--fixture-dir", hidden_root]
        )
        assert proc.returncode != 0
        assert not STAGE.exists()


class TestPersistence:
    def test_second_replay_increments_generation(self) -> None:
        """Second replay command must increment persisted replay_generation counter."""
        reset()
        pipeline(SEEDS[0], "bust-chain")
        gen1 = json.loads(GENERATION.read_text(encoding="utf-8"))["replay_generation"]
        proc = run([CLI, "replay", "--scenario", "bust-chain"])
        assert proc.returncode == 0
        gen2 = json.loads(GENERATION.read_text(encoding="utf-8"))["replay_generation"]
        assert gen2 == gen1 + 1

    def test_stale_generation_blocks_export(self) -> None:
        """Export must fail when staging replay_generation drifts from generation file."""
        reset()
        pipeline(SEEDS[1], "cancel-correct")
        gen = json.loads(GENERATION.read_text(encoding="utf-8"))["replay_generation"]
        STAGE.write_text(
            STAGE.read_text(encoding="utf-8").replace(
                f'"replay_generation": {gen}',
                f'"replay_generation": {gen - 1}',
            ),
            encoding="utf-8",
        )
        proc = run(
            [CLI, "export", "--scenario", "cancel-correct", "--output", str(APP / "output/stale.json")]
        )
        assert proc.returncode != 0

    def test_seq_reset_allows_low_sequence_after_reset(self) -> None:
        """Sequence reset must allow MsgSeqNum restart after reset_seq staging row."""
        reset()
        out = pipeline(SEEDS[2], "seq-reset")
        body = json.loads(out.read_text(encoding="utf-8"))
        assert body["net_positions"].get("IBM", 0) == 30

    def test_compliance_audit_digest_stable(self) -> None:
        """Compliance export audit_digest must match canonical net/active hash."""
        reset()
        out = pipeline(SEEDS[3], "bust-chain")
        body = json.loads(out.read_text(encoding="utf-8"))
        ref = reference_compliance(FIXTURES, "bust-chain")
        assert body["audit_digest"] == ref["audit_digest"]

    def test_staging_event_count_matches_scenario_streams(self) -> None:
        """Staging event_count must equal number of replayable rows ingested from streams."""
        reset()
        run([CLI, "ingest", "--seed", SEEDS[0], "--scenario", "cancel-correct", "--fixture-dir", str(FIXTURES)])
        snap = json.loads(STAGE.read_text(encoding="utf-8"))
        assert snap["event_count"] == len(snap["events"])
        assert snap["event_count"] == 3
