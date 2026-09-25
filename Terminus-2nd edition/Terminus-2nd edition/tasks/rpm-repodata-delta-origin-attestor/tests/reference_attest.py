"""Independent reference for rpm-repo-attest attestation export."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def seg_key(token: str) -> list[tuple[int, str]]:
    parts: list[tuple[int, str]] = []
    for chunk in token.replace("-", "~").split("."):
        num = ""
        suffix = ""
        for ch in chunk:
            if ch.isdigit():
                num += ch
            else:
                suffix += ch
        parts.append((int(num or 0), suffix))
    return parts


def evra_key(pkg: dict[str, Any]) -> tuple[Any, ...]:
    return (pkg["epoch"], seg_key(pkg["version"]), seg_key(pkg["release"]))


def format_nevra(pkg: dict[str, Any]) -> str:
    return f"{pkg['epoch']}:{pkg['name']}-{pkg['version']}-{pkg['release']}.{pkg['arch']}"


def assign_lineage(packages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for pkg in packages:
        pkg = dict(pkg)
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    rows_in = [dict(p) for p in packages]
    for pkg in rows_in:
        pkg["nevra"] = format_nevra(pkg)
        groups.setdefault((pkg["name"], pkg["arch"]), []).append(pkg)
    out: list[dict[str, Any]] = []
    for key in sorted(groups):
        ordered = sorted(groups[key], key=evra_key, reverse=True)
        for rank, pkg in enumerate(ordered, start=1):
            row = dict(pkg)
            row["lineage_rank"] = rank
            out.append(row)
    return out


def build_origin_digest(stage: dict[str, Any]) -> str:
    packages = sorted(stage.get("packages", []), key=lambda p: p.get("nevra", ""))
    modules = sorted(stage.get("module_defaults", []), key=lambda m: m.get("module", ""))
    payload = {
        "module_defaults": modules,
        "mirror_repo_revision": stage.get("mirror_repo_revision", ""),
        "packages": sorted(p.get("nevra", "") for p in packages),
        "repomd_revision": stage.get("repomd_revision", ""),
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return f"sha256:{digest}"


def reference_export(stage_path: Path) -> dict[str, Any]:
    stage = json.loads(stage_path.read_text(encoding="utf-8"))
    packages = sorted(stage.get("packages", []), key=lambda p: p.get("nevra", ""))
    modules = sorted(stage.get("module_defaults", []), key=lambda m: m.get("module", ""))
    return {
        "repo_id": stage.get("repo_id", ""),
        "ingest_seq": stage.get("ingest_seq", 0),
        "repomd_revision": stage.get("repomd_revision", ""),
        "checksum_ok": stage.get("checksum_ok", False),
        "mirror_snapshot_valid": stage.get("mirror_snapshot_valid", False),
        "packages": packages,
        "module_defaults": modules,
        "origin_digest": build_origin_digest(stage),
    }


def tb3_salt() -> str:
    import os

    return os.environ.get("TB3_PACKAGE_SALT", "")
