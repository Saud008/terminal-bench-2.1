"""TB3 hidden traps — gap bias and precedence fixtures under verifier-fixtures."""

from __future__ import annotations

import json

from vecchat_lamport_refmath import (
    load_events,
    reference_findings_report,
    reference_timeline_rows,
    stage_events,
)
from vecchat_session_probe import (
    VCREPLAY_BIN,
    VCREPLAY_FINDINGS,
    VCREPLAY_GEN,
    VCREPLAY_HIDDEN,
    VCREPLAY_ROOM,
    VCREPLAY_STAGE,
    VCREPLAY_TIMELINE,
    read_timeline,
    vcreplay_cli,
    vcreplay_reset_workspace,
    vcreplay_run_pipeline,
)


class VecchatArtifactContract:
    def test_c4e91lam_tb3_staging_path(self) -> None:
        """TB3 load writes chat-staging.json at /app/state/chat-staging.json."""
        vcreplay_reset_workspace()
        proc = vcreplay_cli(
            [
                VCREPLAY_BIN,
                "load",
                "--room",
                VCREPLAY_ROOM,
                "--scenario",
                "clean-room",
                "--fixture-dir",
                "/app/fixtures",
            ]
        )
        assert proc.returncode == 0
        assert str(VCREPLAY_STAGE) == "/app/state/chat-staging.json"
        assert VCREPLAY_STAGE.is_file()

    def test_c4e91lam_tb3_reconcile_generation_bump(self) -> None:
        """TB3 reconcile bumps reconcile_revision in /app/state/reconcile-revision.json."""
        vcreplay_reset_workspace()
        vcreplay_run_pipeline("clock-gap")
        assert VCREPLAY_FINDINGS.is_file()
        assert VCREPLAY_GEN.is_file()
        gen = json.loads(VCREPLAY_GEN.read_text(encoding="utf-8"))
        assert gen["reconcile_revision"] >= 1


class VecchatTb3Traps:
    def test_c4e91lam_hidden_gap_trap_tb3_gap_bias(self) -> None:
        """Hidden gap-trap with TB3_GAP_BIAS emits clock_gap per gap-findings-contract.md."""
        vcreplay_reset_workspace()
        hidden = str(VCREPLAY_HIDDEN)
        env = {"TB3_FIXTURE_DIR": hidden, "TB3_GAP_BIAS": "-1"}
        vcreplay_cli(
            [
                VCREPLAY_BIN,
                "load",
                "--room",
                VCREPLAY_ROOM,
                "--scenario",
                "gap-trap",
                "--fixture-dir",
                hidden,
            ],
            env=env,
        )
        vcreplay_cli(
            [VCREPLAY_BIN, "reconcile", "--room", VCREPLAY_ROOM, "--scenario", "gap-trap"],
            env=env,
        )
        ref = reference_findings_report("gap-trap", VCREPLAY_HIDDEN)
        body = json.loads(VCREPLAY_FINDINGS.read_text(encoding="utf-8"))
        assert body["findings"] == ref["findings"]
        assert any(f["code"] == "clock_gap" for f in body["findings"])

    def test_c4e91lam_hidden_precedence_timeline_refmath(self) -> None:
        """Hidden precedence-trap timeline rows match vecchat_lamport_refmath."""
        vcreplay_reset_workspace()
        hidden = str(VCREPLAY_HIDDEN)
        env = {"TB3_FIXTURE_DIR": hidden}
        out = VCREPLAY_TIMELINE
        vcreplay_run_pipeline("precedence-trap", fixture_root=VCREPLAY_HIDDEN, extra_env=env)
        events = stage_events(load_events(VCREPLAY_HIDDEN, "precedence-trap"))
        ref = reference_timeline_rows(VCREPLAY_ROOM, "precedence-trap", events)
        assert read_timeline(out) == ref

    def test_c4e91lam_hidden_precedence_warn_conflict(self) -> None:
        """Hidden precedence-trap flags moderation_conflict on concurrent warn event p001."""
        vcreplay_reset_workspace()
        hidden = str(VCREPLAY_HIDDEN)
        env = {"TB3_FIXTURE_DIR": hidden}
        vcreplay_run_pipeline("precedence-trap", fixture_root=VCREPLAY_HIDDEN, extra_env=env)
        body = json.loads(VCREPLAY_FINDINGS.read_text(encoding="utf-8"))
        assert any(
            f["code"] == "moderation_conflict" and f["event_id"] == "p001"
            for f in body["findings"]
        )
