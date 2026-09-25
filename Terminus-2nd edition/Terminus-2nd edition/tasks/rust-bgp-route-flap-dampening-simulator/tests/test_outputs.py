"""G-026 entrypoint — fleet host dampening rollout verifier for rdampctl.

Subprocess tests use independent bgp_refmath reference_pipeline / reference_reuse_forecast.
"""

from __future__ import annotations

from bgp_refmath import reference_reuse_forecast
from rdamp_helpers import FIXTURES, forecast_pipeline, read_jsonl, reset
from test_rdamp_advance import TestDriveFeed
from test_rdamp_normalize import TestCompileScenario, TestOutputPathContracts
from test_rdamp_report import (
    TestDecoyModule,
    TestEmitAtlas,
    TestHiddenTraps,
    TestReuseForecast,
)

# Keep suite classes bound in this module so pytest - test_outputs.py collects them.
_SUITE_CLASSES = (
    TestDriveFeed,
    TestCompileScenario,
    TestOutputPathContracts,
    TestDecoyModule,
    TestEmitAtlas,
    TestHiddenTraps,
    TestReuseForecast,
)


def test_fleet_host_manifest_compile_locks_scenario() -> None:
    """Fleet host rollout: compile-scenario must seal scenario-lock.json from the scenario manifest."""
    reset()
    from rdamp_helpers import LOCK, RDAMP, run

    proc = run(
        [str(RDAMP), "compile-scenario", "--scenario", "stable-prefix", "--root", str(FIXTURES)]
    )
    assert proc.returncode == 0
    assert LOCK.is_file()
    import json

    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    assert lock.get("scenario_id") == "stable-prefix"
    assert "feed_fingerprint" in lock


def test_topology_rollout_reuse_forecast_matches_reference() -> None:
    """Topology rollout: emit-reuse-forecast JSONL must match independent reference_reuse_forecast."""
    reset()
    out = forecast_pipeline("decay-reuse")
    rows = read_jsonl(out)
    ref = reference_reuse_forecast(FIXTURES, "decay-reuse")
    assert rows == ref
