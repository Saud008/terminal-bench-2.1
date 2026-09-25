from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

AUDIT_BIN = "/app/bin/snapretctl"
AUDIT_ROOT = Path("/app")
RESET_SCRIPT = Path("/app/scripts/reset-state.sh")
FLEET_GRAPH_JSON = Path("/app/state/k8s-fleet-graph.json")
REVISION_JSON = Path("/app/state/audit-pass-counter.json")
FINDINGS_JSON = Path("/app/work/scoring-findings.json")
REPORT_JSON = Path("/app/output/volsnap-audit-report.json")
DANGLING_JSONL = Path("/app/output/orphan-snapshot-ledger.jsonl")
FIXTURE_ROOT = AUDIT_ROOT / "fixtures"
HIDDEN_FIXTURE_ROOT = Path("/opt/verifier-fixtures/snapretctl")

SCENARIO_CLEAN = "clean-retention"
SCENARIO_PVC = "pvc-join-chain"
SCENARIO_CLASS = "class-override"
SCENARIO_DANGLING = "dangling-snap"
SCENARIO_POLICY = "policy-precedence"
SCENARIO_QUOTA = "quota-cap"
SCENARIO_RETAIN = "retain-pin"
SCENARIO_STABLE_REPUBLISH = "stable-republish"


def invoke_audit(cmd: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        cmd,
        cwd=str(AUDIT_ROOT),
        capture_output=True,
        text=True,
        check=False,
        env=merged,
    )


def wipe_audit_state() -> None:
    proc = invoke_audit(["bash", str(RESET_SCRIPT)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def run_full_audit(
    scenario: str,
    fixture_root: Path | None = None,
    extra_env: dict | None = None,
) -> None:
    root = fixture_root or FIXTURE_ROOT
    env: dict[str, str] = {}
    if fixture_root:
        env["TB3_FIXTURE_DIR"] = str(root)
    if extra_env:
        env.update(extra_env)
    steps = (
        [AUDIT_BIN, "import-graph", "--scenario", scenario, "--fixture-dir", str(root)],
        [AUDIT_BIN, "score-retention", "--scenario", scenario],
        [AUDIT_BIN, "publish-audit", "--scenario", scenario],
    )
    for step in steps:
        proc = invoke_audit(step, env=env or None)
        assert proc.returncode == 0, proc.stderr + proc.stdout


def load_json_file(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl_file(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows
