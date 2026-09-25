"""Cronctl ledger behavioral verifier (independent schedule math)."""

from __future__ import annotations

import json
import shutil
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import cronledger_math_c41f64e9 as reference_cronledger_math  # noqa: F401
from cronledger_contract_helpers import (
    APP,
    CRONCTL,
    GENERATION,
    LEDGER_DB,
    PROBE_FIXTURES,
    SEEDS,
    STAGING,
    invoke_cronctl,
    run_load_replay_export,
    truth_scenario,
    wipe_replay_state,
)
from cronledger_math_c41f64e9 import (
    count_gap_window_fires,
    expand_cron_fires,
    fnv_digest_for_fires,
    read_seed_scenario,
    rollup_execution_rows,
)


class TestCronLedgerSnapshotShape:
    def test_load_planned_fires_match_engine(self) -> None:
        """Load must write planned_fires from location-aware schedule expansion."""
        wipe_replay_state()
        seed = SEEDS[0]
        scenario = "tz-tag-vs-location"
        proc = invoke_cronctl(
            [str(CRONCTL), "load", "--seed", seed, "--scenario", scenario]
        )
        assert proc.returncode == 0
        snap = json.loads(STAGING.read_text(encoding="utf-8"))
        sc = read_seed_scenario(truth_scenario(scenario), seed)
        expected = expand_cron_fires(sc)
        got = [(f["job_id"], f["at_ms"]) for f in snap["planned_fires"]]
        assert got == expected

    def test_snapshot_fires_digest_and_engine(self) -> None:
        """Snapshot must record cron engine and fires_digest."""
        wipe_replay_state()
        seed = SEEDS[0]
        scenario = "overlap-entries"
        proc = invoke_cronctl(
            [str(CRONCTL), "load", "--seed", seed, "--scenario", scenario]
        )
        assert proc.returncode == 0
        snap = json.loads(STAGING.read_text(encoding="utf-8"))
        sc = read_seed_scenario(truth_scenario(scenario), seed)
        expected = expand_cron_fires(sc)
        assert snap["engine"] == "croncalc"
        assert snap["fires_digest"] == fnv_digest_for_fires(expected)
        assert snap["replay_generation"] == 0

    def test_planned_fires_use_absolute_unix_ms(self) -> None:
        """planned_fires at_ms must be absolute UTC epoch milliseconds."""
        wipe_replay_state()
        seed = SEEDS[2]
        scenario = "tz-tag-vs-location"
        proc = invoke_cronctl(
            [str(CRONCTL), "load", "--seed", seed, "--scenario", scenario]
        )
        assert proc.returncode == 0
        snap = json.loads(STAGING.read_text(encoding="utf-8"))
        sc = read_seed_scenario(truth_scenario(scenario), seed)
        expected = expand_cron_fires(sc)
        got = [row["at_ms"] for row in snap["planned_fires"]]
        assert got == [at for _, at in expected]
        assert all(at > 1_000_000_000_000 for at in got)


class TestCronLedgerExportRollups:
    def test_export_fire_counts_match_rows(self) -> None:
        """Exported fire_count and dedup_count must match execution rows in the ledger."""
        wipe_replay_state()
        seed = SEEDS[0]
        scenario = "overlap-entries"
        out = run_load_replay_export(seed, scenario)
        body = json.loads(out.read_text(encoding="utf-8"))
        fires = sum(1 for e in body["executions"] if not e.get("deduped"))
        dedup = sum(1 for e in body["executions"] if e.get("deduped"))
        assert body["fire_count"] == fires
        assert body["dedup_count"] == dedup

    def test_sqlite_ledger_rows_match_export(self) -> None:
        """Replay must persist execution rows to SQLite matching export executions order."""
        wipe_replay_state()
        seed = SEEDS[1]
        scenario = "dst-spring-gap"
        out = run_load_replay_export(seed, scenario)
        body = json.loads(out.read_text(encoding="utf-8"))
        assert LEDGER_DB.is_file()
        conn = sqlite3.connect(str(LEDGER_DB))
        try:
            # Ordering contract: fired_at_ms ASC, job_id ASC (run-ledger-export.md).
            cur = conn.execute(
                "SELECT job_id, fired_at_ms, status, lock_held, deduped FROM executions "
                "ORDER BY fired_at_ms ASC, job_id ASC"
            )
            db_rows = [
                {
                    "job_id": r[0],
                    "fired_at_ms": r[1],
                    "status": r[2],
                    "lock_held": bool(r[3]),
                    "deduped": bool(r[4]),
                }
                for r in cur.fetchall()
            ]
        finally:
            conn.close()
        assert len(db_rows) >= 1
        assert len(db_rows) == len(body["executions"])
        export_order = sorted(
            body["executions"],
            key=lambda e: (int(e["fired_at_ms"]), str(e["job_id"])),
        )
        assert body["executions"] == export_order
        for db_row, exp in zip(db_rows, body["executions"], strict=True):
            assert db_row["job_id"] == exp["job_id"]
            assert db_row["fired_at_ms"] == exp["fired_at_ms"]
            assert db_row["status"] == exp["status"]
            assert db_row["deduped"] == bool(exp.get("deduped"))

    def test_export_blocks_on_digest_tamper(self) -> None:
        """Export must fail when fires_digest in the staging snapshot does not match."""
        wipe_replay_state()
        seed = SEEDS[0]
        scenario = "overlap-entries"
        run_load_replay_export(seed, scenario)
        snap = json.loads(STAGING.read_text(encoding="utf-8"))
        snap["fires_digest"] = "0" * 16
        STAGING.write_text(json.dumps(snap, indent=2), encoding="utf-8")
        out = APP / "output" / f"{seed}-{scenario}-bad.json"
        proc = invoke_cronctl(
            [
                str(CRONCTL),
                "export",
                "--seed",
                seed,
                "--scenario",
                scenario,
                "--output",
                str(out),
            ]
        )
        assert proc.returncode != 0


class TestCronLedgerCounterGate:
    REPLAY_GENERATION_PATH = "/app/state/replay-generation.json"
    REPLAY_SNAPSHOT_PATH = "/app/state/replay-snapshot.json"

    def test_clock_advance_increments_generation_counter(self) -> None:
        """Replay must bump generation exactly once per successful replay."""
        wipe_replay_state()
        seed = SEEDS[0]
        scenario = "overlap-entries"
        proc = invoke_cronctl(
            [str(CRONCTL), "load", "--seed", seed, "--scenario", scenario]
        )
        assert proc.returncode == 0
        snap0 = json.loads(Path(self.REPLAY_SNAPSHOT_PATH).read_text(encoding="utf-8"))
        assert snap0["replay_generation"] == 0
        proc = invoke_cronctl(
            [str(CRONCTL), "replay", "--seed", seed, "--scenario", scenario]
        )
        assert proc.returncode == 0
        assert Path(self.REPLAY_GENERATION_PATH).is_file()
        gen = json.loads(Path(self.REPLAY_GENERATION_PATH).read_text(encoding="utf-8"))
        snap = json.loads(Path(self.REPLAY_SNAPSHOT_PATH).read_text(encoding="utf-8"))
        assert gen["generation"] == 1
        assert snap["replay_generation"] == 1
        assert gen["seed"] == seed
        assert gen["scenario"] == scenario
        proc = invoke_cronctl(
            [str(CRONCTL), "replay", "--seed", seed, "--scenario", scenario]
        )
        assert proc.returncode == 0
        gen2 = json.loads(Path(self.REPLAY_GENERATION_PATH).read_text(encoding="utf-8"))
        snap2 = json.loads(Path(self.REPLAY_SNAPSHOT_PATH).read_text(encoding="utf-8"))
        assert gen2["generation"] == 2
        assert snap2["replay_generation"] == 2
        assert GENERATION.is_file()
        assert json.loads(GENERATION.read_text(encoding="utf-8"))["seed"] == seed

    def test_load_emits_snapshot_file(self) -> None:
        """Load must create /app/state/replay-snapshot.json with the active scenario name."""
        wipe_replay_state()
        seed = SEEDS[2]
        scenario = "overlap-entries"
        snapshot_path = "/app/state/replay-snapshot.json"
        proc = invoke_cronctl(
            [str(CRONCTL), "load", "--seed", seed, "--scenario", scenario]
        )
        assert proc.returncode == 0
        assert Path(snapshot_path).is_file()
        body = json.loads(Path(snapshot_path).read_text(encoding="utf-8"))
        assert body["scenario"] == scenario

    def test_export_requires_clock_advance_first(self) -> None:
        """Export must refuse when replay_generation is still zero after load only."""
        wipe_replay_state()
        seed = SEEDS[1]
        scenario = "dst-spring-gap"
        proc = invoke_cronctl(
            [str(CRONCTL), "load", "--seed", seed, "--scenario", scenario]
        )
        assert proc.returncode == 0
        out = APP / "output" / f"{seed}-{scenario}-ledger.json"
        proc = invoke_cronctl(
            [
                str(CRONCTL),
                "export",
                "--seed",
                seed,
                "--scenario",
                scenario,
                "--output",
                str(out),
            ]
        )
        assert proc.returncode != 0


class TestCronLedgerOverlapCoalesce:
    def test_singleton_group_collapses_overlap(self) -> None:
        """singleton_group jobs must coalesce overlapping fires per singleton-coalesce.md."""
        wipe_replay_state()
        seed = SEEDS[0]
        scenario = "overlap-entries"
        out = run_load_replay_export(seed, scenario)
        body = json.loads(out.read_text(encoding="utf-8"))
        assert body["dedup_count"] >= 1
        deduped = [e for e in body["executions"] if e.get("deduped")]
        assert deduped
        ref = rollup_execution_rows(read_seed_scenario(truth_scenario(scenario), seed))
        assert body["dedup_count"] == ref["dedup_count"]


class TestCronLedgerTzSemantics:
    def test_location_field_wins_over_tz_tag(self) -> None:
        """Job location field must win over conflicting tz tags per timezone-rules.md."""
        wipe_replay_state()
        seed = SEEDS[2]
        scenario = "tz-tag-vs-location"
        out = run_load_replay_export(seed, scenario)
        body = json.loads(out.read_text(encoding="utf-8"))
        sc = read_seed_scenario(truth_scenario(scenario), seed)
        expected_ms = {at for _, at in expand_cron_fires(sc)}
        fired_ms = {
            e["fired_at_ms"] for e in body["executions"] if not e.get("deduped")
        }
        assert fired_ms == expected_ms

    def test_conflicting_tz_tag_still_loads(self) -> None:
        """Conflicting tz tags must not cause load to exit non-zero."""
        wipe_replay_state()
        seed = SEEDS[0]
        scenario = "tz-tag-vs-location"
        proc = invoke_cronctl(
            [str(CRONCTL), "load", "--seed", seed, "--scenario", scenario]
        )
        assert proc.returncode == 0, proc.stderr + proc.stdout


class TestCronLedgerDstGap:
    def test_spring_forward_yields_single_fire(self) -> None:
        """DST spring-forward gap must yield exactly one fire per dst-gap-handling.md."""
        wipe_replay_state()
        seed = SEEDS[0]
        scenario = "dst-spring-gap"
        out = run_load_replay_export(seed, scenario)
        sc = read_seed_scenario(truth_scenario(scenario), seed)
        assert count_gap_window_fires(sc) == 1
        body = json.loads(out.read_text(encoding="utf-8"))
        probe_fires = [
            e
            for e in body["executions"]
            if e["job_id"].endswith(":gap-probe") and not e.get("deduped")
        ]
        assert len(probe_fires) == 1


class TestCronLedgerInflightAbort:
    def test_reschedule_records_aborted_status(self) -> None:
        """In-flight reschedule events must record aborted status, not success."""
        wipe_replay_state()
        seed = SEEDS[1]
        scenario = "reschedule-inflight"
        out = run_load_replay_export(seed, scenario)
        body = json.loads(out.read_text(encoding="utf-8"))
        aborted = [e for e in body["executions"] if e.get("status") == "aborted"]
        assert aborted, "expected aborted row after reschedule event"
        assert all(e.get("status") == "aborted" for e in aborted)
        assert all(e.get("status") != "success" for e in aborted)
        assert all(
            e.get("status") != "in_flight_rescheduled" for e in body["executions"]
        )


class TestCronLedgerPanicLease:
    def test_panic_clears_lease_held_flag(self) -> None:
        """Panic during replay must release the distributed lock per run-ledger-export.md."""
        wipe_replay_state()
        seed = SEEDS[2]
        scenario = "lock-panic-renew"
        out = run_load_replay_export(seed, scenario)
        body = json.loads(out.read_text(encoding="utf-8"))
        panic_rows = [e for e in body["executions"] if e.get("status") == "panic"]
        assert panic_rows
        assert all(e.get("status") == "panic" for e in panic_rows)
        assert all(not e.get("lock_held") for e in panic_rows)
        assert all(e.get("status") != "panic_recovered" for e in body["executions"])


class TestCronLedgerClockOverrides:
    def test_arbitrary_tick_ms_still_fires_planned(self) -> None:
        """TB3_TICK_MS values that skip exact fire instants must still apply in-window fires."""
        wipe_replay_state()
        seed = SEEDS[2]
        scenario = "tz-tag-vs-location"
        sc = read_seed_scenario(truth_scenario(scenario), seed)
        expected = expand_cron_fires(sc)
        assert len(expected) >= 2
        out = run_load_replay_export(
            seed,
            scenario,
            extra_env={"TB3_TICK_MS": "70000", "TB3_CLOCK_START": sc.window_start},
        )
        body = json.loads(out.read_text(encoding="utf-8"))
        fired = sorted(
            (e["job_id"], e["fired_at_ms"])
            for e in body["executions"]
            if not e.get("deduped") and e.get("status") == "fired"
        )
        assert fired == expected

    def test_clock_start_skips_fires_before_override(self) -> None:
        """TB3_CLOCK_START after the first planned fire must skip earlier instants."""
        wipe_replay_state()
        seed = SEEDS[2]
        scenario = "tz-tag-vs-location"
        sc = read_seed_scenario(truth_scenario(scenario), seed)
        expected = expand_cron_fires(sc)
        assert len(expected) >= 2
        first_at = expected[0][1]
        second_at = expected[1][1]
        # Start the fake clock just after the first fire so only later fires apply.
        start = datetime.fromtimestamp(first_at / 1000.0, tz=timezone.utc) + timedelta(
            milliseconds=1
        )
        clock_start = start.isoformat().replace("+00:00", "Z")
        out = run_load_replay_export(
            seed,
            scenario,
            extra_env={"TB3_CLOCK_START": clock_start, "TB3_TICK_MS": "60000"},
        )
        body = json.loads(out.read_text(encoding="utf-8"))
        fired = sorted(
            (e["job_id"], e["fired_at_ms"])
            for e in body["executions"]
            if not e.get("deduped") and e.get("status") == "fired"
        )
        assert all(at > first_at for _, at in fired)
        assert (expected[1][0], second_at) in fired


class TestCronLedgerFixturePrecedence:
    def test_default_root_is_app_fixtures(self) -> None:
        """With TB3_FIXTURE_DIR unset, load must resolve bundled /app/fixtures/scenarios."""
        wipe_replay_state()
        seed = SEEDS[0]
        scenario = "overlap-entries"
        proc = invoke_cronctl(
            [str(CRONCTL), "load", "--seed", seed, "--scenario", scenario]
        )
        assert proc.returncode == 0, proc.stderr + proc.stdout
        snap = json.loads(STAGING.read_text(encoding="utf-8"))
        assert snap["scenario"] == scenario
        sc = read_seed_scenario(truth_scenario(scenario), seed)
        assert [
            (f["job_id"], f["at_ms"]) for f in snap["planned_fires"]
        ] == expand_cron_fires(sc)

    def test_tb3_fixture_dir_overrides_default_root(self) -> None:
        """TB3_FIXTURE_DIR must be the sole scenario root when set (hidden dual-lease pack)."""
        wipe_replay_state()
        seed = "TB3-hidden"
        scenario = "hidden-dual-lease"
        hidden = PROBE_FIXTURES / f"{scenario}.json"
        assert hidden.is_file()
        # Without override, bundled root must not resolve this scenario name.
        proc = invoke_cronctl(
            [str(CRONCTL), "load", "--seed", seed, "--scenario", scenario]
        )
        assert proc.returncode != 0
        out = run_load_replay_export(seed, scenario, fixture_dir=PROBE_FIXTURES)
        body = json.loads(out.read_text(encoding="utf-8"))
        fired = [
            e
            for e in body["executions"]
            if e.get("status") == "fired" and not e.get("deduped")
        ]
        assert len(fired) == 2
        assert {e["job_id"] for e in fired} == {f"{seed}:lease-a", f"{seed}:lease-b"}
        assert all(e.get("lock_held") for e in fired)

    def test_relative_fixture_dir_falls_back_to_bundled(self) -> None:
        """Relative TB3_FIXTURE_DIR must be ignored even when the relative path exists."""
        wipe_replay_state()
        seed = "TB3-hidden"
        scenario = "hidden-dual-lease"
        rel_root = APP / "work" / "rel-fixtures"
        rel_root.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PROBE_FIXTURES / f"{scenario}.json", rel_root / f"{scenario}.json")
        # Relative path exists and contains the hidden scenario. Absolute-only policy
        # must ignore it and fail to resolve from the bundled /app/fixtures root.
        proc = invoke_cronctl(
            [str(CRONCTL), "load", "--seed", seed, "--scenario", scenario],
            env={"TB3_FIXTURE_DIR": "work/rel-fixtures"},
        )
        assert proc.returncode != 0
        # Ignoring the relative override must still allow the bundled default root.
        seed_ok = SEEDS[0]
        scenario_ok = "overlap-entries"
        proc = invoke_cronctl(
            [str(CRONCTL), "load", "--seed", seed_ok, "--scenario", scenario_ok],
            env={"TB3_FIXTURE_DIR": "work/rel-fixtures"},
        )
        assert proc.returncode == 0, proc.stderr + proc.stdout
        snap = json.loads(STAGING.read_text(encoding="utf-8"))
        assert snap["scenario"] == scenario_ok


class TestCronLedgerProbeDst:
    def test_probe_dst_boundary_single_fire(self) -> None:
        """Hidden DST boundary scenario under /opt/verifier-fixtures must not double-fire."""
        wipe_replay_state()
        seed = "TB3-hidden"
        scenario = "hidden-dst-boundary"
        assert str(PROBE_FIXTURES).startswith("/opt/verifier-fixtures")
        hidden = PROBE_FIXTURES / f"{scenario}.json"
        assert hidden.is_file()
        out = run_load_replay_export(seed, scenario, fixture_dir=PROBE_FIXTURES)
        sc = read_seed_scenario(hidden, seed)
        assert count_gap_window_fires(sc) == 1
        body = json.loads(out.read_text(encoding="utf-8"))
        fires = [e for e in body["executions"] if not e.get("deduped")]
        assert len(fires) == 1


class TestCronLedgerProbeSingleton:
    def test_probe_singleton_group_dedupes(self) -> None:
        """Hidden /opt/verifier-fixtures singleton_group scenario must coalesce fires."""
        wipe_replay_state()
        seed = "TB3-hidden"
        scenario = "hidden-singleton-group"
        assert "/opt/verifier-fixtures" in str(PROBE_FIXTURES)
        hidden = PROBE_FIXTURES / f"{scenario}.json"
        assert hidden.is_file()
        out = run_load_replay_export(seed, scenario, fixture_dir=PROBE_FIXTURES)
        body = json.loads(out.read_text(encoding="utf-8"))
        assert body["dedup_count"] >= 1
        ref = rollup_execution_rows(read_seed_scenario(hidden, seed))
        assert body["dedup_count"] == ref["dedup_count"]

    def test_probe_singleton_multi_instant_survives_fat_tick(self) -> None:
        """Distinct singleton_group instants in one TB3_TICK_MS window must both fire."""
        wipe_replay_state()
        seed = "TB3-hidden"
        scenario = "hidden-singleton-multi-instant"
        hidden = PROBE_FIXTURES / f"{scenario}.json"
        assert hidden.is_file()
        sc = read_seed_scenario(hidden, seed)
        expected = expand_cron_fires(sc)
        assert len(expected) >= 2
        assert expected[0][1] != expected[1][1]
        out = run_load_replay_export(
            seed,
            scenario,
            fixture_dir=PROBE_FIXTURES,
            extra_env={"TB3_TICK_MS": "3600000", "TB3_CLOCK_START": sc.window_start},
        )
        body = json.loads(out.read_text(encoding="utf-8"))
        fired = sorted(
            (e["job_id"], e["fired_at_ms"])
            for e in body["executions"]
            if not e.get("deduped") and e.get("status") == "fired"
        )
        assert fired == expected
        assert body["dedup_count"] == 0
