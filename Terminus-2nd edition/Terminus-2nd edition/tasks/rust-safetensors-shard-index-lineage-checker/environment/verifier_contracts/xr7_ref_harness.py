"""CLI harness helpers for safetensors shard index lineage checker."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

APP = Path("/app")
ENV = APP / "environment"
BIN = APP / "bin" / "xr7"
BUILD = ENV / "scripts" / "build_all.sh"
STATE = APP / "var" / "xr7_journal.ndjson"
OUT = APP / "lineage" / "weight_lineage_atlas.json"
DEFAULT_CATALOGS = ENV / "registry" / "catalogs"
DEFAULT_WEIGHTS = ENV / "registry" / "weights"


def catalog_dir() -> Path:
    root = os.environ.get("XR7_CATALOG_ROOT")
    if root:
        return Path(root)
    return DEFAULT_CATALOGS


def weight_root() -> Path:
    root = os.environ.get("XR7_WEIGHT_ROOT")
    if root:
        return Path(root)
    return DEFAULT_WEIGHTS


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)


def rebuild() -> None:
    run(["bash", str(BUILD)])


def pipeline(catalogs: Path | None = None, weights: Path | None = None) -> None:
    catalogs = catalogs or catalog_dir()
    weights = weights or weight_root()
    STATE.parent.mkdir(parents=True, exist_ok=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if STATE.exists():
        STATE.unlink()
    if OUT.exists():
        OUT.unlink()
    run(
        [
            str(BIN),
            "catalog-scan",
            "--catalog-dir",
            str(catalogs),
            "--weight-root",
            str(weights),
            "--journal",
            str(STATE),
        ]
    )
    run(
        [
            str(BIN),
            "atlas-publish",
            "--journal",
            str(STATE),
            "--catalog-dir",
            str(catalogs),
            "--weight-root",
            str(weights),
            "--atlas",
            str(OUT),
        ]
    )


def catalog_scan_only(catalogs: Path | None = None, weights: Path | None = None) -> None:
    """Run catalog-scan only and leave the on-disk journal snapshot."""
    catalogs = catalogs or catalog_dir()
    weights = weights or weight_root()
    STATE.parent.mkdir(parents=True, exist_ok=True)
    if STATE.exists():
        STATE.unlink()
    run(
        [
            str(BIN),
            "catalog-scan",
            "--catalog-dir",
            str(catalogs),
            "--weight-root",
            str(weights),
            "--journal",
            str(STATE),
        ]
    )


def atlas_publish_only(catalogs: Path | None = None, weights: Path | None = None) -> None:
    """Run atlas-publish using the existing on-disk journal snapshot."""
    catalogs = catalogs or catalog_dir()
    weights = weights or weight_root()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if OUT.exists():
        OUT.unlink()
    run(
        [
            str(BIN),
            "atlas-publish",
            "--journal",
            str(STATE),
            "--catalog-dir",
            str(catalogs),
            "--weight-root",
            str(weights),
            "--atlas",
            str(OUT),
        ]
    )


def load_report() -> list:
    return json.loads(OUT.read_text(encoding="utf-8"))


def load_journal_rows() -> list[dict]:
    rows = []
    for ln in STATE.read_text(encoding="utf-8").splitlines():
        if ln.strip():
            rows.append(json.loads(ln))
    return rows
