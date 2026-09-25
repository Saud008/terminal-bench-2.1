"""G-026 bundled smoke for vecchat vcreplay (lamport contract entry)."""

from __future__ import annotations

import json
import subprocess

from vecchat_lamport_refmath import reference_staging
from vecchat_session_probe import (
    VCREPLAY_BIN,
    VCREPLAY_BUNDLE,
    VCREPLAY_GEN,
    VCREPLAY_ROOM,
    VCREPLAY_STAGE,
    VCREPLAY_TIMELINE,
    vcreplay_cli,
    vcreplay_reset_workspace,
)


def test_vclmp_bootstrap_load_materializes_lamport_snapshot() -> None:
    """load subcommand materializes /app/state/chat-staging.json for clean-room."""
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
            str(VCREPLAY_BUNDLE),
        ]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert isinstance(proc, subprocess.CompletedProcess)
    body = json.loads(VCREPLAY_STAGE.read_text(encoding="utf-8"))
    ref = reference_staging(VCREPLAY_ROOM, "clean-room", VCREPLAY_BUNDLE)
    assert body["staging_digest"] == ref["staging_digest"]
    assert str(VCREPLAY_STAGE) == "/app/state/chat-staging.json"
    assert str(VCREPLAY_GEN) == "/app/state/reconcile-revision.json"
    assert str(VCREPLAY_TIMELINE) == "/app/output/audit-timeline.jsonl"
