"""Bundled callout roster contract tests."""

from __future__ import annotations

import json
import sqlite3
import subprocess
from pathlib import Path

from ref_dispatch_math import reference_assignments, reference_roster, reference_scores
from callout_pipeline import CALLOUT_BIN, DB_PATH, FIXTURE_ROOT, ROSTER_JSON, invoke, run_pipeline


class TestCalloutRosterContracts:
    def test_calloutd_load_roster_materializes_callout_db(self, fresh_callout_state) -> None:
        """load-roster must persist faults and technicians into /app/state/callout.db."""
        proc = invoke(
            ["load-roster", "--scenario", "clean-dispatch", "--fixture-dir", str(FIXTURE_ROOT)]
        )
        assert proc.returncode == 0, proc.stderr + proc.stdout
        con = sqlite3.connect(DB_PATH)
        try:
            assert con.execute("SELECT COUNT(*) FROM faults").fetchone()[0] == 1
            assert con.execute("SELECT COUNT(*) FROM technicians").fetchone()[0] == 2
        finally:
            con.close()

    def test_calloutd_emit_callout_roster_matches_ref_math(self, fresh_callout_state) -> None:
        """emit-callout roster must match independent reference math for clean-dispatch."""
        run_pipeline("clean-dispatch")
        body = json.loads(ROSTER_JSON.read_text(encoding="utf-8"))
        ref = reference_roster(FIXTURE_ROOT, "clean-dispatch")
        assert body["assignments"] == ref["assignments"]
        assert body["breach_horizon_summary"] == ref["breach_horizon_summary"]
        assert body["roster_digest"] == ref["roster_digest"]

    def test_calloutd_subprocess_cli_load_roster_ingest_stage(self, fresh_callout_state) -> None:
        """Ingest stage must run calloutd via subprocess before export."""
        proc = subprocess.run(
            [CALLOUT_BIN, "load-roster", "--scenario", "clean-dispatch", "--fixture-dir", str(FIXTURE_ROOT)],
            cwd="/app",
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0, proc.stderr + proc.stdout

    def test_calloutd_ingest_only_blocks_export_emit_callout(self, fresh_callout_state) -> None:
        """Ingest-only load-roster must block emit-callout export stage."""
        subprocess.run(
            [CALLOUT_BIN, "load-roster", "--scenario", "clean-dispatch", "--fixture-dir", str(FIXTURE_ROOT)],
            cwd="/app",
            check=True,
        )
        proc = subprocess.run(
            [CALLOUT_BIN, "emit-callout", "--scenario", "clean-dispatch"],
            cwd="/app",
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode != 0

    def test_calloutd_export_roster_digest_after_emit_callout(self, fresh_callout_state) -> None:
        """Export stage emit-callout must publish roster_digest."""
        run_pipeline("clean-dispatch")
        body = json.loads(ROSTER_JSON.read_text(encoding="utf-8"))
        ref = reference_roster(FIXTURE_ROOT, "clean-dispatch")
        assert body["roster_digest"] == ref["roster_digest"]

    def test_calloutd_trapped_escalation_assignment_export(self, fresh_callout_state) -> None:
        """trapped-escalation scenario assignments must match reference bind rows."""
        run_pipeline("trapped-escalation")
        body = json.loads(ROSTER_JSON.read_text(encoding="utf-8"))
        ref = reference_assignments(FIXTURE_ROOT, "trapped-escalation")
        assert body["assignments"] == ref

    def test_calloutd_skill_floor_edge_assignment_export(self, fresh_callout_state) -> None:
        """skill-floor-edge scenario must honor certification floor matching."""
        run_pipeline("skill-floor-edge")
        body = json.loads(ROSTER_JSON.read_text(encoding="utf-8"))
        ref = reference_assignments(FIXTURE_ROOT, "skill-floor-edge")
        assert body["assignments"] == ref

    def test_calloutd_access_window_inclusive_assignment_export(self, fresh_callout_state) -> None:
        """access-window-inclusive scenario must allow arrival at inclusive end_minute."""
        run_pipeline("access-window-inclusive")
        body = json.loads(ROSTER_JSON.read_text(encoding="utf-8"))
        ref = reference_assignments(FIXTURE_ROOT, "access-window-inclusive")
        assert body["assignments"] == ref

    def test_calloutd_sla_tier_gold_assignment_export(self, fresh_callout_state) -> None:
        """sla-tier-gold scenario must pick highest tier_rank SLA contract."""
        run_pipeline("sla-tier-gold")
        body = json.loads(ROSTER_JSON.read_text(encoding="utf-8"))
        ref = reference_assignments(FIXTURE_ROOT, "sla-tier-gold")
        assert body["assignments"] == ref

    def test_calloutd_stable_order_tie_assignment_export(self, fresh_callout_state) -> None:
        """stable-order-tie scenario must sort by negative priority then fault_id."""
        run_pipeline("stable-order-tie")
        body = json.loads(ROSTER_JSON.read_text(encoding="utf-8"))
        ref = reference_assignments(FIXTURE_ROOT, "stable-order-tie")
        assert body["assignments"] == ref

    def test_calloutd_cancelled_fault_skip_assignment_export(self, fresh_callout_state) -> None:
        """cancelled-fault-skip scenario must not assign cancelled faults."""
        run_pipeline("cancelled-fault-skip")
        body = json.loads(ROSTER_JSON.read_text(encoding="utf-8"))
        ref = reference_assignments(FIXTURE_ROOT, "cancelled-fault-skip")
        assert body["assignments"] == ref


class TestCalloutUrgencyLadder:
    def test_calloutd_trapped_passenger_weight_in_urgency_scores(self, fresh_callout_state) -> None:
        """urgency ladder must add trapped_passengers weight per urgency-ladder-contract."""
        run_pipeline("trapped-escalation")
        ref_scores = reference_scores(FIXTURE_ROOT, "trapped-escalation")
        con = sqlite3.connect(DB_PATH)
        try:
            score = con.execute("SELECT priority_score FROM urgency_scores LIMIT 1").fetchone()[0]
        finally:
            con.close()
        assert score == ref_scores[0]["priority_score"]

    def test_calloutd_gold_sla_tier_urgency(self, fresh_callout_state) -> None:
        """rank-faults must compute sla_urgency from gold horizon tier."""
        run_pipeline("sla-tier-gold")
        ref_scores = reference_scores(FIXTURE_ROOT, "sla-tier-gold")
        con = sqlite3.connect(DB_PATH)
        try:
            urgency = con.execute("SELECT sla_urgency FROM urgency_scores LIMIT 1").fetchone()[0]
        finally:
            con.close()
        assert urgency == ref_scores[0]["sla_urgency"]


class TestCalloutPassGates:
    def test_calloutd_emit_callout_blocked_when_pass_zero(self, fresh_callout_state) -> None:
        """emit-callout must fail when callout_pass is zero."""
        invoke(["load-roster", "--scenario", "clean-dispatch", "--fixture-dir", str(FIXTURE_ROOT)])
        proc = invoke(["emit-callout", "--scenario", "clean-dispatch"])
        assert proc.returncode != 0

    def test_calloutd_bind_roster_increments_callout_pass(self, fresh_callout_state) -> None:
        """bind-roster must increment callout_pass in /app/state/callout-pass.json."""
        run_pipeline("clean-dispatch")
        body = json.loads(Path("/app/state/callout-pass.json").read_text(encoding="utf-8"))
        assert body["callout_pass"] == 1

    def test_calloutd_bind_audit_ledger_records_pass_num(self, fresh_callout_state) -> None:
        """bind-roster must append bind_audit_ledger rows with pass_num."""
        run_pipeline("clean-dispatch")
        con = sqlite3.connect(DB_PATH)
        try:
            row = con.execute("SELECT pass_num FROM bind_audit_ledger LIMIT 1").fetchone()
        finally:
            con.close()
        assert row is not None and row[0] == 1


class TestCalloutIdempotentBind:
    def test_calloutd_second_bind_roster_preserves_locked_rows(self, fresh_callout_state) -> None:
        """locked-rerun scenario must preserve locked assignments on repeat bind-roster."""
        invoke(["load-roster", "--scenario", "locked-rerun", "--fixture-dir", str(FIXTURE_ROOT)])
        invoke(["rank-faults", "--scenario", "locked-rerun"])
        invoke(["bind-roster", "--scenario", "locked-rerun"])
        con = sqlite3.connect(DB_PATH)
        try:
            first_rows = con.execute(
                "SELECT fault_id, tech_id FROM assignments ORDER BY fault_id"
            ).fetchall()
        finally:
            con.close()
        invoke(["bind-roster", "--scenario", "locked-rerun"])
        invoke(["emit-callout", "--scenario", "locked-rerun"])
        body = json.loads(ROSTER_JSON.read_text(encoding="utf-8"))
        ref = reference_roster(FIXTURE_ROOT, "locked-rerun")
        assert body["assignments"] == ref["assignments"]
        con = sqlite3.connect(DB_PATH)
        try:
            second_rows = con.execute(
                "SELECT fault_id, tech_id FROM assignments ORDER BY fault_id"
            ).fetchall()
            ledger_rows = con.execute("SELECT COUNT(*) FROM bind_audit_ledger").fetchone()[0]
        finally:
            con.close()
        assert first_rows == second_rows
        assert ledger_rows >= 1
