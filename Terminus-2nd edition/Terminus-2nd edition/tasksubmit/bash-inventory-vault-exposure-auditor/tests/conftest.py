"""Shared pytest fixtures for hostsatlas verifier."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

APP = Path("/app")
CLI = Path("/usr/local/bin/hostsatlas")
TREES = APP / "fixtures/trees"
OUTPUT = APP / "output"
STATE = APP / "state"
RESET = APP / "scripts/reset-state.sh"
TB3 = Path("/opt/verifier-fixtures/tb3-trees")
PARTIAL_HOOKS = Path(__file__).resolve().parent / "traps" / "partial_hooks"
LIB = APP / "lib"

BUNDLED_TREES = [
    "clean-tree",
    "vault-leak",
    "precedence-trap",
    "ignored-leak",
    "inheritance-gap",
]

OUTPUT_REPORT_PATH = "/app/output/hosts-atlas-report.json"
STATE_SCAN_MANIFEST = "/app/state/scan-manifest.json"
STATE_HOST_ROWS = "/app/state/host-rows.ndjson"
STATE_EXPOSURE_ROWS = "/app/state/atlas-rows.ndjson"
STATE_RUN_SEQ = "/app/state/run-seq.json"


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False)


def tree_manifest(tree_id: str) -> Path:
    if tree_id == "tb3-nested-vault":
        return TB3 / "nested-vault" / "tree.json"
    if tree_id == "tb3-ignore-bypass":
        return TB3 / "ignore-bypass" / "tree.json"
    return TREES / tree_id / "tree.json"


def scan_cli(tree_id: str) -> subprocess.CompletedProcess[str]:
    manifest = tree_manifest(tree_id)
    return run([str(CLI), "scan", "--tree", str(manifest)])


def emit_cli(tree_id: str, out: Path) -> subprocess.CompletedProcess[str]:
    out.parent.mkdir(parents=True, exist_ok=True)
    return run([str(CLI), "emit", "--tree", tree_id, "--output", str(out)])


def load_scan_manifest() -> dict[str, Any]:
    return json.loads((STATE / "scan-manifest.json").read_text(encoding="utf-8"))


def load_host_rows() -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in (STATE / "host-rows.ndjson").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def load_exposure_rows() -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in (STATE / "atlas-rows.ndjson").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def load_staged_snapshot() -> dict[str, Any]:
    snapshot = load_scan_manifest()
    snapshot["hosts"] = load_host_rows()
    snapshot["findings"] = load_exposure_rows()
    return snapshot


def staging_digest_from_state_files() -> str:
    host_rows = (STATE / "host-rows.ndjson").read_bytes()
    exposure_rows = (STATE / "atlas-rows.ndjson").read_bytes()
    return hashlib.sha256(host_rows + exposure_rows).hexdigest()


def install_partial(name: str) -> None:
    src = PARTIAL_HOOKS / name
    if name == "emit_reopen.sh":
        dest = LIB / "emit_atlas.sh"
    elif name == "digest_trap.sh":
        dest = LIB / "scan_inventory.sh"
    else:
        dest = LIB / name
    data = src.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    dest.write_bytes(data)
    dest.chmod(0o755)


def snapshot_lib() -> dict[str, str]:
    saved: dict[str, str] = {}
    for path in sorted(LIB.glob("*.sh")):
        saved[str(path)] = path.read_text(encoding="utf-8")
    return saved


def restore_lib(saved: dict[str, str]) -> None:
    for path, content in saved.items():
        p = Path(path)
        p.write_text(content, encoding="utf-8")
        p.chmod(0o755)


@pytest.fixture(autouse=True)
def reset_state() -> None:
    proc = run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr
    yield
    run(["bash", str(RESET)])
