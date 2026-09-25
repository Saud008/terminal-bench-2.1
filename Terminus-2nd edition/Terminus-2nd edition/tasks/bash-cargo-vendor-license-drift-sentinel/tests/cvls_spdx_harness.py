"""Shared contract helpers for cargo vendor sentinel verifier."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

APP = Path("/app")
CLI = Path("/usr/local/bin/cvls-governor")
WORKSPACES = APP / "fixtures/workspaces"
OUTPUT = APP / "output"
STAGE = APP / "stage/license-compliance"
STATE = APP / "state"
RESET = APP / "scripts/reset-state.sh"
TB3_ROOT = Path("/opt/verifier-fixtures/tb3-workspaces")

BUNDLED_WORKSPACE_IDS = (
    "baseline",
    "license-drift",
    "checksum-mismatch",
    "patched-lineage",
    "duplicate-versions",
)


def invoke(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False)


def workspace_root(ws_id: str) -> Path:
    if ws_id.startswith("tb3-"):
        return TB3_ROOT / ws_id
    return WORKSPACES / ws_id


def staging_manifest(ws_id: str) -> Path:
    return STAGE / f"{ws_id}.json"


def run_inventory(ws_id: str) -> subprocess.CompletedProcess[str]:
    return invoke([str(CLI), "inventory", "--workspace", str(workspace_root(ws_id))])


def run_attest(ws_id: str) -> subprocess.CompletedProcess[str]:
    return invoke([str(CLI), "attest", "--workspace", str(workspace_root(ws_id))])


def run_publish(ws_id: str, json_out: Path, csv_out: Path) -> subprocess.CompletedProcess[str]:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    return invoke(
        [
            str(CLI),
            "publish",
            "--workspace",
            str(workspace_root(ws_id)),
            "--json",
            str(json_out),
            "--csv",
            str(csv_out),
        ]
    )


def run_full_chain(ws_id: str, json_out: Path, csv_out: Path) -> None:
    assert run_inventory(ws_id).returncode == 0
    assert run_attest(ws_id).returncode == 0
    proc = run_publish(ws_id, json_out, csv_out)
    assert proc.returncode == 0, proc.stderr or proc.stdout


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
