"""Bundled mpiqctl inspection queue contract tests."""

from __future__ import annotations

import json
import sqlite3
import subprocess
from pathlib import Path

from permit_ref_math import reference_entries, reference_queue, reference_scores
from permit_queue_driver import DB_PATH, FIXTURE_ROOT, MPIQ_BIN, MANIFEST_JSON, invoke, run_pipeline


class TestPermitQueueManifestContracts:
    def test_t751ee9_mpq_snapshot_load_populates_permit_sqlite(self, fresh_insp_state) -> None:
        """snapshot-load must persist permits and inspectors into /app/state/permit.db"""
        proc = invoke(["snapshot-load", "--scenario", "clean-queue", "--fixture-dir", str(FIXTURE_ROOT)])
        assert proc.returncode == 0, proc.stderr + proc.stdout
        con = sqlite3.connect(DB_PATH)
        try:
            assert con.execute("SELECT COUNT(*) FROM permits").fetchone()[0] == 2
            assert con.execute("SELECT COUNT(*) FROM inspectors").fetchone()[0] == 2
        finally:
            con.close()

    def test_t751ee9_mpq_publish_manifest_matches_independent_ref(self, fresh_insp_state) -> None:
        """publish-queue manifest must match independent reference math for clean-queue."""
        run_pipeline("clean-queue")
        body = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
        ref = reference_queue(FIXTURE_ROOT, "clean-queue")
        assert body["queue_entries"] == ref["queue_entries"]
        assert body["hold_summary"] == ref["hold_summary"]
        assert body["queue_digest"] == ref["queue_digest"]

    def test_t751ee9_mpq_cli_subprocess_snapshot_load_ok(self, fresh_insp_state) -> None:
        """Ingest stage must run mpiqctl via subprocess before export."""
        proc = subprocess.run(
            [MPIQ_BIN, "snapshot-load", "--scenario", "clean-queue", "--fixture-dir", str(FIXTURE_ROOT)],
            cwd="/app",
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0, proc.stderr + proc.stdout

    def test_t751ee9_mpq_partial_pipeline_blocks_publish(self, fresh_insp_state) -> None:
        """Ingest-only snapshot-load must block publish-queue export stage."""
        subprocess.run(
            [MPIQ_BIN, "snapshot-load", "--scenario", "clean-queue", "--fixture-dir", str(FIXTURE_ROOT)],
            cwd="/app",
            check=True,
        )
        proc = subprocess.run(
            [MPIQ_BIN, "publish-queue", "--scenario", "clean-queue"],
            cwd="/app",
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode != 0

    def test_t751ee9_mpq_manifest_carries_queue_digest(self, fresh_insp_state) -> None:
        """Export stage publish-queue must publish queue_digest."""
        run_pipeline("clean-queue")
        body = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
        ref = reference_queue(FIXTURE_ROOT, "clean-queue")
        assert body["queue_digest"] == ref["queue_digest"]

    def test_t751ee9_mpq_violation_priority_rank_order(self, fresh_insp_state) -> None:
        """violation-priority scenario queue entries must match reference scoring."""
        run_pipeline("violation-priority")
        body = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
        ref = reference_entries(FIXTURE_ROOT, "violation-priority")
        assert body["queue_entries"] == ref

    def test_t751ee9_mpq_cert_floor_inclusive_match(self, fresh_insp_state) -> None:
        """cert-floor-edge scenario must honor inclusive certification floor matching."""
        run_pipeline("cert-floor-edge")
        body = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
        ref = reference_entries(FIXTURE_ROOT, "cert-floor-edge")
        assert body["queue_entries"] == ref

    def test_t751ee9_mpq_blackout_end_day_inclusive(self, fresh_insp_state) -> None:
        """blackout-inclusive-end scenario must allow requested_day on inclusive end_day."""
        run_pipeline("blackout-inclusive-end")
        body = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
        ref = reference_entries(FIXTURE_ROOT, "blackout-inclusive-end")
        assert body["queue_entries"] == ref

    def test_t751ee9_mpq_moratorium_hold_suppresses_queue(self, fresh_insp_state) -> None:
        """zoning-hold-block scenario must emit empty queue when hold active."""
        run_pipeline("zoning-hold-block")
        body = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
        ref = reference_queue(FIXTURE_ROOT, "zoning-hold-block")
        assert body["queue_entries"] == ref["queue_entries"]
        assert body["hold_summary"] == ref["hold_summary"]

    def test_t751ee9_mpq_electrical_lane_routing(self, fresh_insp_state) -> None:
        """electrical-lane-route scenario must bind lane-electrical from permit route table."""
        run_pipeline("electrical-lane-route")
        body = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
        ref = reference_entries(FIXTURE_ROOT, "electrical-lane-route")
        assert body["queue_entries"] == ref

    def test_t751ee9_mpq_stable_rank_permit_id_tiebreak(self, fresh_insp_state) -> None:
        """stable-order-tie scenario must sort by composite score then permit_id."""
        run_pipeline("stable-order-tie")
        body = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
        ref = reference_entries(FIXTURE_ROOT, "stable-order-tie")
        assert body["queue_entries"] == ref

    def test_t751ee9_mpq_score_stage_writes_rank_json(self, fresh_insp_state) -> None:
        """score-queue must write /app/work/violation-ranks.json with composite scores."""
        run_pipeline("violation-priority")
        ranks = json.loads(Path("/app/work/violation-ranks.json").read_text(encoding="utf-8"))
        ref = reference_scores(FIXTURE_ROOT, "violation-priority")
        for row in ref:
            assert ranks[row["permit_id"]] == row["composite_score"]

    def test_t751ee9_mpq_policy_compile_emits_graph(self, fresh_insp_state) -> None:
        """compile-policy must emit /app/work/policy-graph.json with lane edges."""
        invoke(["snapshot-load", "--scenario", "clean-queue", "--fixture-dir", str(FIXTURE_ROOT)])
        proc = invoke(["compile-policy", "--scenario", "clean-queue"])
        assert proc.returncode == 0
        graph = json.loads(Path("/app/work/policy-graph.json").read_text(encoding="utf-8"))
        assert "lanes" in graph and "edges" in graph

    def test_t751ee9_mpq_hold_apply_writes_mask_json(self, fresh_insp_state) -> None:
        """apply-holds must write hold-mask.json keyed by district."""
        invoke(["snapshot-load", "--scenario", "zoning-hold-block", "--fixture-dir", str(FIXTURE_ROOT)])
        proc = invoke(["apply-holds", "--scenario", "zoning-hold-block"])
        assert proc.returncode == 0
        mask = json.loads(Path("/app/work/hold-mask.json").read_text(encoding="utf-8"))
        assert mask

    def test_t751ee9_mpq_blackout_filter_eligible_json(self, fresh_insp_state) -> None:
        """filter-blackouts must write eligible-dates.json for non-blocked permits."""
        invoke(["snapshot-load", "--scenario", "blackout-inclusive-end", "--fixture-dir", str(FIXTURE_ROOT)])
        invoke(["apply-holds", "--scenario", "blackout-inclusive-end"])
        proc = invoke(["filter-blackouts", "--scenario", "blackout-inclusive-end"])
        assert proc.returncode == 0
        eligible = json.loads(Path("/app/work/eligible-dates.json").read_text(encoding="utf-8"))
        assert eligible

    def test_t751ee9_mpq_score_increments_queue_pass_counter(self, fresh_insp_state) -> None:
        """score-queue must increment queue_pass in /app/state/queue-pass.json"""
        invoke(["snapshot-load", "--scenario", "clean-queue", "--fixture-dir", str(FIXTURE_ROOT)])
        invoke(["compile-policy", "--scenario", "clean-queue"])
        invoke(["apply-holds", "--scenario", "clean-queue"])
        invoke(["filter-blackouts", "--scenario", "clean-queue"])
        invoke(["score-queue", "--scenario", "clean-queue"])
        body = json.loads(Path("/app/state/queue-pass.json").read_text(encoding="utf-8"))
        assert body["queue_pass"] >= 1

    def test_t751ee9_mpq_bind_persists_queue_entry_rows(self, fresh_insp_state) -> None:
        """bind-inspectors must persist queue_entries rows before publish."""
        run_pipeline("clean-queue")
        con = sqlite3.connect(DB_PATH)
        try:
            assert con.execute("SELECT COUNT(*) FROM queue_entries").fetchone()[0] >= 1
        finally:
            con.close()

    def test_t751ee9_mpq_violation_weight_monotonic_in_ref(self, fresh_insp_state) -> None:
        """Higher violation weight must rank before lower when base_priority ties."""
        scores = reference_scores(FIXTURE_ROOT, "violation-priority")
        assert scores[0]["violation_weight"] >= scores[-1]["violation_weight"]

    def test_t751ee9_mpq_manifest_includes_planning_epoch(self, fresh_insp_state) -> None:
        """Published manifest must include planning_epoch_day from bundle."""
        run_pipeline("clean-queue")
        body = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
        ref = reference_queue(FIXTURE_ROOT, "clean-queue")
        assert body["planning_epoch_day"] == ref["planning_epoch_day"]

    def test_t751ee9_mpq_instruction_output_paths_exist(self, fresh_insp_state) -> None:
        """Instruction paths /app/state/permit.db, queue-pass.json, and manifest must exist after pipeline."""
        run_pipeline("clean-queue")
        assert Path("/app/state/permit.db").is_file()
        assert Path("/app/state/queue-pass.json").is_file()
        assert Path("/app/output/permit-queue-manifest.json").is_file()

