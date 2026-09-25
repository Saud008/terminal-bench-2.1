"""Reconcile phase — moderation, mute windows, receipts, clock gaps."""

from __future__ import annotations

import json

from vecchat_lamport_refmath import reference_findings_report
from vecchat_session_probe import (
    VCREPLAY_BIN,
    VCREPLAY_BUNDLE,
    VCREPLAY_FINDINGS,
    VCREPLAY_GEN,
    VCREPLAY_ROOM,
    vcreplay_cli,
    vcreplay_reset_workspace,
    vcreplay_run_pipeline,
)


class VecchatModGates:
    def test_c4e91lam_clean_room_zero_findings(self) -> None:
        """reconcile-findings.json reports finding_count zero for clean-room."""
        vcreplay_reset_workspace()
        vcreplay_run_pipeline("clean-room")
        body = json.loads(VCREPLAY_FINDINGS.read_text(encoding="utf-8"))
        assert body["finding_count"] == 0

    def test_c4e91lam_mod_precedence_conflict_rows(self) -> None:
        """Concurrent moderation emits moderation_conflict per moderation-mute-contract.md."""
        vcreplay_reset_workspace()
        vcreplay_run_pipeline("mod-precedence")
        ref = reference_findings_report("mod-precedence", VCREPLAY_BUNDLE)
        body = json.loads(VCREPLAY_FINDINGS.read_text(encoding="utf-8"))
        assert body["findings"] == ref["findings"]
        assert any(f["code"] == "moderation_conflict" for f in body["findings"])

    def test_c4e91lam_mute_half_open_leak_u002_only(self) -> None:
        """mute_leak applies only inside half-open mute window for event u002."""
        vcreplay_reset_workspace()
        vcreplay_run_pipeline("mute-window")
        ref = reference_findings_report("mute-window", VCREPLAY_BUNDLE)
        body = json.loads(VCREPLAY_FINDINGS.read_text(encoding="utf-8"))
        assert body["findings"] == ref["findings"]
        leak_ids = {f["event_id"] for f in body["findings"] if f["code"] == "mute_leak"}
        assert leak_ids == {"u002"}

    def test_c4e91lam_dup_delivery_flags_d003(self) -> None:
        """dup-delivery flags duplicate_delivery on suppressed receipt event_id d003."""
        vcreplay_reset_workspace()
        vcreplay_run_pipeline("dup-delivery")
        body = json.loads(VCREPLAY_FINDINGS.read_text(encoding="utf-8"))
        dup = [f for f in body["findings"] if f["code"] == "duplicate_delivery"]
        assert len(dup) == 1
        assert dup[0]["event_id"] == "d003"

    def test_c4e91lam_clock_gap_on_large_component_jump(self) -> None:
        """Adjacent causal events with component delta above max_gap emit clock_gap."""
        vcreplay_reset_workspace()
        vcreplay_run_pipeline("clock-gap")
        body = json.loads(VCREPLAY_FINDINGS.read_text(encoding="utf-8"))
        assert any(f["code"] == "clock_gap" for f in body["findings"])

    def test_c4e91lam_reconcile_revision_increment(self) -> None:
        """reconcile advances reconcile_revision in reconcile-revision.json."""
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
        vcreplay_cli([VCREPLAY_BIN, "reconcile", "--room", VCREPLAY_ROOM, "--scenario", "clean-room"])
        gen = json.loads(VCREPLAY_GEN.read_text(encoding="utf-8"))
        assert gen["reconcile_revision"] >= 1

    def test_c4e91lam_clean_room_no_receipt_mismatch(self) -> None:
        """Valid delivery receipts produce no receipt_mismatch on clean-room."""
        vcreplay_reset_workspace()
        vcreplay_run_pipeline("clean-room")
        body = json.loads(VCREPLAY_FINDINGS.read_text(encoding="utf-8"))
        assert not any(f["code"] == "receipt_mismatch" for f in body["findings"])
