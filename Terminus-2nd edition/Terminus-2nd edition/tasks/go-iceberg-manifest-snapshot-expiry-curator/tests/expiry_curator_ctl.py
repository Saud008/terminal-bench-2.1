"""Subprocess driver for iceexpctl lakehouse expiry curator verifier runs."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

AGENT_USER = "agent"
CTL_BIN = "/app/bin/iceexpctl"
CTL_APP = Path("/app")
CTL_RESET = Path("/app/scripts/reset-state.sh")
CTL_CURSOR = Path("/app/state/table-cursor.json")
CTL_AUDIT_PASS = Path("/app/state/analyze-revision.json")
CTL_AUDIT_WITNESS = Path("/app/work/analyze-findings.json")
CTL_PLAN = Path("/app/output/expiry-plan.json")
CTL_ORPHAN = Path("/app/output/orphan-ledger.jsonl")
CTL_BUNDLE = CTL_APP / "fixtures"
CTL_OVERLAY = Path("/opt/verifier-fixtures/iceexpctl")

SCENARIO_TABLE = {
    "clean-lineage": "lake_clean-lineage",
    "branch-protect": "lake_branch-protect",
    "tag-pin": "lake_tag-pin",
    "delete-retain": "lake_delete-retain",
    "manifest-nested": "lake_manifest-nested",
    "meta-order": "lake_meta-order",
    "orphan-trap": "lake_orphan-trap",
    "stable-republish": "lake_stable-republish",
    "tag-branch-trap": "lake_tag-branch-trap",
    "delete-boundary-trap": "lake_delete-boundary-trap",
}


def catalog_for(scenario: str) -> str:
    return SCENARIO_TABLE[scenario]


def _as_agent(cmd: list[str]) -> list[str]:
    """Drop to the unprivileged agent UID for rebuild artifacts and CLI runs."""
    return ["runuser", "-u", AGENT_USER, "--", *cmd]


def invoke_iceexpctl(cmd: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        _as_agent(cmd),
        cwd=str(CTL_APP),
        capture_output=True,
        text=True,
        check=False,
        env=merged,
    )


def reset_curator_workspace() -> None:
    proc = invoke_iceexpctl(["bash", str(CTL_RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def run_curator_chain(
    scenario: str,
    fixture_root: Path | None = None,
    extra_env: dict | None = None,
) -> None:
    root = fixture_root or CTL_BUNDLE
    catalog = catalog_for(scenario)
    env: dict[str, str] = {}
    if fixture_root:
        env["TB3_FIXTURE_DIR"] = str(root)
    if extra_env:
        env.update(extra_env)
    steps = (
        [CTL_BIN, "capture-catalog", "--catalog", catalog, "--scenario", scenario, "--fixture-dir", str(root)],
        [CTL_BIN, "audit-retention", "--catalog", catalog, "--scenario", scenario],
        [CTL_BIN, "publish-expiry", "--catalog", catalog, "--scenario", scenario],
    )
    for step in steps:
        proc = invoke_iceexpctl(step, env=env or None)
        assert proc.returncode == 0, proc.stderr + proc.stdout


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows
