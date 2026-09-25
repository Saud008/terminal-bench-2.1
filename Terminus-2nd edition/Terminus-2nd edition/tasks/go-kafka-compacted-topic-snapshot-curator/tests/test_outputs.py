"""G-026 smoke - kcompactctl staging path and digest."""

from __future__ import annotations

import json

from compact_segment_refmath import reference_staging
from kcompact_shell_ops import (
    BIN,
    BUNDLED_FIXTURES,
    PATHS,
    TOPIC_SLUG,
    exec_kcompact,
    wipe_workspace,
)


def test_t3c5e90_g026_smoke_compact_topic_staging_written() -> None:
    """G-026 smoke: pull-segments writes staging digest matching refmath."""
    wipe_workspace()
    proc = exec_kcompact(
        [
            BIN,
            "pull-segments",
            "--topic",
            TOPIC_SLUG,
            "--scenario",
            "clean-compact",
            "--fixture-dir",
            str(BUNDLED_FIXTURES),
        ]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert PATHS["staging"].is_file()
    body = json.loads(PATHS["staging"].read_text(encoding="utf-8"))
    ref = reference_staging(TOPIC_SLUG, "clean-compact", BUNDLED_FIXTURES)
    assert body["staging_digest"] == ref["staging_digest"]
