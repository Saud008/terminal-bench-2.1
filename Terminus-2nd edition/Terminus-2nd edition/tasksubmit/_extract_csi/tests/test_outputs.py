"""G-026 smoke — snapretctl import-graph fleet graph digest and paths."""

from __future__ import annotations

import json
import subprocess

from csi_audit_runner import (
    AUDIT_BIN,
    FIXTURE_ROOT,
    SCENARIO_CLEAN,
    FLEET_GRAPH_JSON,
    invoke_audit,
    wipe_audit_state,
)
from k8s_volume_refmath import reference_fleet_graph

PATH_K8S_FLEET_GRAPH = "/app/state/k8s-fleet-graph.json"


def test_gsra_smoke_import_graph_writes_staging_path() -> None:
    """import-graph must write /app/state/k8s-fleet-graph.json with contract fleet_graph_digest."""
    wipe_audit_state()
    proc = invoke_audit(
        [AUDIT_BIN, "import-graph", "--scenario", SCENARIO_CLEAN, "--fixture-dir", str(FIXTURE_ROOT)]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert isinstance(proc, subprocess.CompletedProcess)
    assert str(FLEET_GRAPH_JSON) == PATH_K8S_FLEET_GRAPH
    assert FLEET_GRAPH_JSON.is_file()
    body = json.loads(FLEET_GRAPH_JSON.read_text(encoding="utf-8"))
    ref = reference_fleet_graph(SCENARIO_CLEAN, FIXTURE_ROOT)
    assert body["fleet_graph_digest"] == ref["fleet_graph_digest"]


def test_gsra_smoke_staging_engine_is_snapretctl() -> None:
    """Fleet graph staging JSON must record engine snapretctl per k8s-fleet-graph-contract."""
    wipe_audit_state()
    invoke_audit(
        [AUDIT_BIN, "import-graph", "--scenario", SCENARIO_CLEAN, "--fixture-dir", str(FIXTURE_ROOT)]
    )
    body = json.loads(FLEET_GRAPH_JSON.read_text(encoding="utf-8"))
    assert body["engine"] == "snapretctl"
