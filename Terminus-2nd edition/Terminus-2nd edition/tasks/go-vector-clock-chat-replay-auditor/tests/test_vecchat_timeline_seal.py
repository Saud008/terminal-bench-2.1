"""Export timeline emit phase — sealed JSONL rows and generation gating."""

from __future__ import annotations

import json

import pytest

from vecchat_lamport_refmath import (
    load_events,
    reference_timeline_rows,
    stage_events,
)
from vecchat_session_probe import (
    VCREPLAY_BIN,
    VCREPLAY_BUNDLE,
    VCREPLAY_EARLY,
    VCREPLAY_GEN,
    VCREPLAY_ROOM,
    VCREPLAY_TIMELINE,
    read_timeline,
    vcreplay_cli,
    vcreplay_reset_workspace,
    vcreplay_run_pipeline,
)


class VecchatTimelineSeal:
    @pytest.mark.parametrize("scenario_id", ("clean-room", "mod-precedence", "dup-delivery"))
    def test_c4e91lam_timeline_rows_match_lamport_refmath(self, scenario_id: str) -> None:
        """audit-timeline.jsonl rows must match independent causal timeline reference."""
        vcreplay_reset_workspace()
        vcreplay_run_pipeline(scenario_id)
        rows = read_timeline(VCREPLAY_TIMELINE)
        events = stage_events(load_events(VCREPLAY_BUNDLE, scenario_id))
        ref = reference_timeline_rows(VCREPLAY_ROOM, scenario_id, events)
        assert rows == ref

    def test_c4e91lam_emit_blocked_before_reconcile_revision(self) -> None:
        """emit-timeline refuses when reconcile_revision is zero."""
        vcreplay_reset_workspace()
        vcreplay_cli(
            [
                VCREPLAY_BIN,
                "load",
                "--room",
                VCREPLAY_ROOM,
                "--scenario",
                "clean-room",
                "--fixture-dir",
                str(VCREPLAY_BUNDLE),
            ]
        )
        proc = vcreplay_cli(
            [
                VCREPLAY_BIN,
                "emit-timeline",
                "--room",
                VCREPLAY_ROOM,
                "--scenario",
                "clean-room",
                "--output",
                str(VCREPLAY_EARLY),
            ]
        )
        assert proc.returncode != 0

    def test_c4e91lam_mod_precedence_hides_m003(self) -> None:
        """Message event m003 is not visible when ban moderation applies."""
        vcreplay_reset_workspace()
        vcreplay_run_pipeline("mod-precedence")
        rows = read_timeline(VCREPLAY_TIMELINE)
        msg = next(r for r in rows if r["event_id"] == "m003")
        assert msg["visible"] is False

    def test_c4e91lam_dup_delivery_omits_d003(self) -> None:
        """Suppressed duplicate receipt d003 is omitted from audit-timeline.jsonl."""
        vcreplay_reset_workspace()
        vcreplay_run_pipeline("dup-delivery")
        ids = {r["event_id"] for r in read_timeline(VCREPLAY_TIMELINE)}
        assert "d003" not in ids
        assert "d002" in ids

    def test_c4e91lam_timeline_digest_final_row_only(self) -> None:
        """timeline_digest appears only on the final JSONL row per timeline-emit-contract.md."""
        vcreplay_reset_workspace()
        vcreplay_run_pipeline("clean-room")
        rows = read_timeline(VCREPLAY_TIMELINE)
        assert rows[-1].get("timeline_digest")
        assert all("timeline_digest" not in r for r in rows[:-1])

    def test_c4e91lam_default_output_audit_timeline_jsonl(self) -> None:
        """emit-timeline writes audit-timeline.jsonl under /app/output by default."""
        vcreplay_reset_workspace()
        vcreplay_run_pipeline("clean-room", output=VCREPLAY_TIMELINE)
        assert VCREPLAY_TIMELINE.is_file()
        assert str(VCREPLAY_TIMELINE) == "/app/output/audit-timeline.jsonl"


class VecchatSessionReset:
    def test_c4e91lam_reset_zeroes_reconcile_revision(self) -> None:
        """reset-state.sh zeroes reconcile_revision for cross-run tests."""
        vcreplay_reset_workspace()
        vcreplay_run_pipeline("clean-room")
        vcreplay_reset_workspace()
        gen = json.loads(VCREPLAY_GEN.read_text(encoding="utf-8"))
        assert gen["reconcile_revision"] == 0
