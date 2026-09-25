"""Shard ingest load phase — chat-staging digest and numeric shard ordering."""

from __future__ import annotations

import json

import pytest

from vecchat_lamport_refmath import reference_staging
from vecchat_session_probe import (
    BUNDLED_SCENARIOS,
    VCREPLAY_BIN,
    VCREPLAY_BUNDLE,
    VCREPLAY_ROOM,
    VCREPLAY_STAGE,
    vcreplay_cli,
    vcreplay_reset_workspace,
)


class VecchatShardIngest:
    @pytest.mark.parametrize("scenario_id", BUNDLED_SCENARIOS)
    def test_c4e91lam_shard_digest_matches_lamport_refmath(self, scenario_id: str) -> None:
        """load writes chat-staging.json whose digest matches vecchat_lamport_refmath."""
        vcreplay_reset_workspace()
        proc = vcreplay_cli(
            [
                VCREPLAY_BIN,
                "load",
                "--room",
                VCREPLAY_ROOM,
                "--scenario",
                scenario_id,
                "--fixture-dir",
                str(VCREPLAY_BUNDLE),
            ]
        )
        assert proc.returncode == 0, proc.stderr + proc.stdout
        body = json.loads(VCREPLAY_STAGE.read_text(encoding="utf-8"))
        ref = reference_staging(VCREPLAY_ROOM, scenario_id, VCREPLAY_BUNDLE)
        assert body["staging_digest"] == ref["staging_digest"]
        assert body["event_count"] == ref["event_count"]
        assert body["events"] == ref["events"]

    def test_c4e91lam_numeric_shard_order_shard_010_after_002(self) -> None:
        """shard_010.jsonl is merged after shard_002.jsonl per vector-clock-contract.md."""
        vcreplay_reset_workspace()
        vcreplay_cli(
            [
                VCREPLAY_BIN,
                "load",
                "--room",
                VCREPLAY_ROOM,
                "--scenario",
                "shard-order",
                "--fixture-dir",
                str(VCREPLAY_BUNDLE),
            ]
        )
        body = json.loads(VCREPLAY_STAGE.read_text(encoding="utf-8"))
        ids = [ev["event_id"] for ev in body["events"]]
        assert ids == ["s001", "s002"]

    def test_c4e91lam_staging_path_under_app_state(self) -> None:
        """load materializes /app/state/chat-staging.json per chat-staging.md."""
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
        assert VCREPLAY_STAGE.is_file()
        assert str(VCREPLAY_STAGE) == "/app/state/chat-staging.json"
