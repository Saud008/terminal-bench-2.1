"""Contract path probes for bitswap session exports."""

from __future__ import annotations

import json
from pathlib import Path

from test_outputs import (
    CLI,
    FIXTURES,
    METRICS_FIXTURE,
    METRICS_REPORT,
    SESSION_REPORT,
    reset,
    run,
)

APP = Path("/app")
STAGING = Path("/app/state/want-snapshot.json")


def test_bitswap_pipeline_example_export_path() -> None:
    """Pipeline example writes /app/output/session-report.json and staging snapshot."""
    reset()
    out_path = Path(SESSION_REPORT)
    proc = run(
        [
            CLI,
            "pipeline",
            "--log",
            str(FIXTURES / "001-basic-wants.jsonl"),
            "--session",
            "demo",
            "--output",
            str(out_path),
        ]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert out_path.is_file()
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["session_id"] == "demo"
    assert STAGING.is_file()


def test_bitswap_metrics_example_export_path() -> None:
    """Metrics example writes /app/output/metrics-report.json."""
    reset()
    out_path = Path(METRICS_REPORT)
    proc = run(
        [
            CLI,
            "metrics",
            "--log",
            str(FIXTURES / METRICS_FIXTURE),
            "--session",
            "demo",
            "--output",
            str(out_path),
        ]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert out_path.is_file()
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["session_id"] == "demo"
    assert "queue_head_cid" in payload
