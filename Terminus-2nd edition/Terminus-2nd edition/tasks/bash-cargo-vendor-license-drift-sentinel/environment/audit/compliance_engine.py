"""Baseline sentinel engine — audit against /app/docs/ contracts."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def workspace_id(workspace_root: Path) -> str:
    return workspace_root.name


def staging_path(app_root: Path, ws_id: str) -> Path:
    return app_root / "stage" / "license-compliance" / f"{ws_id}.json"


def parse_cargo_lock(text: str) -> list[dict[str, str]]:
    packages: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if line == "[[package]]":
            if current:
                packages.append(current)
            current = {}
            continue
        if not line or line.startswith("#"):
            continue
        m = re.match(r'^(\w+)\s*=\s*"(.*)"\s*$', line)
        if m and current is not None:
            current[m.group(1)] = m.group(2)
    if current:
        packages.append(current)
    # Baseline: name-only sort collapses duplicate versions
    seen: set[str] = set()
    deduped: list[dict[str, str]] = []
    for pkg in sorted(packages, key=lambda p: p.get("name", "")):
        name = pkg.get("name", "")
        if name in seen:
            continue
        seen.add(name)
        deduped.append(pkg)
    return deduped


def load_lock_metadata(workspace_root: Path) -> dict[str, str]:
    path = workspace_root / "lock-metadata.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, str] = {}
    for row in data.get("packages", []):
        key = f"{row['name']}@{row['version']}"
        out[key] = row["declared_license"]
    return out


def vendor_crate_dir(vendor_root: Path, name: str, version: str) -> Path:
    # Baseline: prefers nested vendor dir before name-version folder
    nested = vendor_root / name
    if nested.is_dir():
        return nested
    direct = vendor_root / f"{name}-{version}"
    if direct.is_dir():
        return direct
    return vendor_root / name


def list_crate_files(crate_dir: Path) -> list[Path]:
    if not crate_dir.is_dir():
        return []
    files: list[Path] = []
    for p in sorted(crate_dir.rglob("*")):
        if p.is_file() and p.name != ".cargo-checksum.json":
            rel = p.relative_to(crate_dir).as_posix()
            if rel.startswith(".git"):
                continue
            files.append(p)
    return files


def package_checksum(crate_dir: Path) -> str:
    lines: list[str] = []
    for p in list_crate_files(crate_dir):
        rel = p.relative_to(crate_dir).as_posix()
        digest = sha256_file(p)
        lines.append(f"{rel}:{digest}")
    lines.sort()
    # Baseline: checksum payload omits trailing newline
    return sha256_bytes("\n".join(lines).encode("utf-8"))


def read_checksum_json(crate_dir: Path) -> str | None:
    path = crate_dir / ".cargo-checksum.json"
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return str(data.get("package", ""))


def normalize_spdx(token: str) -> str:
    return token.strip()


def resolve_license(crate_dir: Path) -> str:
    cargo = crate_dir / "Cargo.toml"
    cargo_license: str | None = None
    license_file_field: str | None = None
    if cargo.is_file():
        for raw in cargo.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            m = re.match(r'^license-file\s*=\s*"(.*)"\s*$', line)
            if m:
                license_file_field = m.group(1)
            m2 = re.match(r'^license\s*=\s*"(.*)"\s*$', line)
            if m2:
                cargo_license = m2.group(1)

    license_paths = sorted(crate_dir.glob("LICENSE*")) + sorted(crate_dir.glob("COPYING*"))
    for lp in license_paths:
        if lp.is_file():
            body = lp.read_text(encoding="utf-8").strip()
            first = body.splitlines()[0].strip() if body else ""
            if first:
                return normalize_spdx(first)

    if license_file_field:
        lf = crate_dir / license_file_field
        if lf.is_file():
            body = lf.read_text(encoding="utf-8").strip()
            first = body.splitlines()[0].strip() if body else ""
            if first:
                return normalize_spdx(first)

    if cargo_license:
        return normalize_spdx(cargo_license)
    return "UNKNOWN"


def parse_patch_section(workspace_root: Path) -> dict[str, dict[str, str]]:
    cargo = workspace_root / "Cargo.toml"
    if not cargo.is_file():
        return {}
    text = cargo.read_text(encoding="utf-8")
    patches: dict[str, dict[str, str]] = {}
    in_patch = False
    for raw in text.splitlines():
        line = raw.strip()
        if line == "[patch.crates-io]":
            in_patch = True
            continue
        if in_patch and line.startswith("[") and line.endswith("]"):
            break
        if not in_patch or not line or line.startswith("#"):
            continue
        m = re.match(r'^(\S+)\s*=\s*\{\s*path\s*=\s*"(.*)"\s*\}\s*$', line)
        if m:
            patches[m.group(1)] = {"patch_path": m.group(2), "source": "path"}
    return patches


def workspace_fingerprint(workspace_root: Path) -> str:
    parts = [
        workspace_root / "Cargo.lock",
        workspace_root / "Cargo.toml",
        workspace_root / "lock-metadata.json",
    ]
    blob = b""
    for p in parts:
        if p.is_file():
            blob += p.read_bytes()
    return sha256_bytes(blob)


def ingest_workspace(workspace_root: Path) -> dict[str, Any]:
    ws_id = workspace_id(workspace_root)
    lock_path = workspace_root / "Cargo.lock"
    vendor_root = workspace_root / "vendor"
    packages = parse_cargo_lock(lock_path.read_text(encoding="utf-8"))
    declared = load_lock_metadata(workspace_root)
    patches = parse_patch_section(workspace_root)

    crate_rows: list[dict[str, Any]] = []
    for pkg in packages:
        name = pkg["name"]
        version = pkg["version"]
        key = f"{name}@{version}"
        crate_dir = vendor_crate_dir(vendor_root, name, version)
        resolved = resolve_license(crate_dir)
        expected = declared.get(key, "UNKNOWN")
        crate_rows.append(
            {
                "name": name,
                "version": version,
                "crate_dir": str(crate_dir.relative_to(workspace_root)),
                "declared_license": expected,
                "resolved_license": resolved,
                "license_drift": resolved != expected,
                "computed_checksum": package_checksum(crate_dir),
                "vendor_checksum": read_checksum_json(crate_dir),
                "checksum_mismatch": False,
                "patch_lineage": None,
            }
        )

    for row in crate_rows:
        vc = row["vendor_checksum"]
        cc = row["computed_checksum"]
        row["checksum_mismatch"] = bool(vc) and vc != cc

    name_groups: dict[str, list[str]] = {}
    for row in crate_rows:
        name_groups.setdefault(row["name"], []).append(row["version"])
    duplicate_names = sorted(
        n for n, vers in name_groups.items() if len(set(vers)) > 1
    )

    staging = {
        "workspace_id": ws_id,
        "workspace_root": str(workspace_root),
        "workspace_fingerprint": workspace_fingerprint(workspace_root),
        "packages": crate_rows,
        "duplicate_package_names": duplicate_names,
        "patch_map": patches,
        "ingest_complete": True,
        "audit_complete": False,
    }
    return staging


def audit_staging(staging: dict[str, Any]) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    for row in staging["packages"]:
        if row["license_drift"]:
            findings.append(
                {
                    "kind": "license_drift",
                    "package": row["name"],
                    "version": row["version"],
                    "declared": row["declared_license"],
                    "resolved": row["resolved_license"],
                }
            )
        if row["checksum_mismatch"]:
            findings.append(
                {
                    "kind": "checksum_mismatch",
                    "package": row["name"],
                    "version": row["version"],
                    "expected": row["vendor_checksum"],
                    "computed": row["computed_checksum"],
                }
            )

    for dup in staging["duplicate_package_names"]:
        vers = sorted(
            {r["version"] for r in staging["packages"] if r["name"] == dup}
        )
        findings.append(
            {
                "kind": "duplicate_versions",
                "package": dup,
                "versions": vers,
            }
        )

    # Baseline: patched findings omitted; digest uses unsorted JSON
    audited = dict(staging)
    audited["findings"] = findings
    audited["audit_complete"] = True
    audited["audit_digest"] = sha256_bytes(json.dumps(findings).encode("utf-8"))
    return audited


def export_report(staging: dict[str, Any], run_seq: int = 1) -> dict[str, Any]:
    if not staging.get("audit_complete"):
        raise ValueError("audit incomplete")
    summary = {
        "license_drift": sum(1 for f in staging["findings"] if f["kind"] == "license_drift"),
        "checksum_mismatch": sum(
            1 for f in staging["findings"] if f["kind"] == "checksum_mismatch"
        ),
        "patched_crate": sum(
            1 for f in staging["findings"] if f["kind"] == "patched_crate"
        ),
        "duplicate_versions": sum(
            1 for f in staging["findings"] if f["kind"] == "duplicate_versions"
        ),
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "workspace_id": staging["workspace_id"],
        "workspace_fingerprint": staging["workspace_fingerprint"],
        "run_seq": run_seq,
        "audit_digest": staging["audit_digest"],
        "summary": summary,
        "findings": staging["findings"],
        "packages": [
            {
                "name": r["name"],
                "version": r["version"],
                "declared_license": r["declared_license"],
                "resolved_license": r["resolved_license"],
                "checksum_mismatch": r["checksum_mismatch"],
                "patch_lineage": r["patch_lineage"],
            }
            for r in staging["packages"]
        ],
    }


def export_csv(report: dict[str, Any]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(
        [
            "kind",
            "package",
            "version",
            "declared_license",
            "resolved_license",
            "detail",
        ]
    )
    for f in report["findings"]:
        writer.writerow(
            [
                f.get("kind", ""),
                f.get("package", ""),
                f.get("version", ""),
                f.get("declared", f.get("declared_license", "")),
                f.get("resolved", f.get("resolved_license", "")),
                f.get("patch_path", f.get("computed", "")),
            ]
        )
    return buf.getvalue()


def canonical_json(report: dict[str, Any]) -> str:
    # Baseline: pretty JSON export
    return json.dumps(report, indent=2) + "\n"
