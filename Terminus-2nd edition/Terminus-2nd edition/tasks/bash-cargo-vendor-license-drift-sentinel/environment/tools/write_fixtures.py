#!/usr/bin/env python3
"""Generate fixture workspaces with correct vendor checksums."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures" / "workspaces"
if Path("/opt/verifier-fixtures").exists():
    TB3 = Path("/opt/verifier-fixtures/tb3-workspaces")
else:
    TB3 = ROOT / "opt-verifier-fixtures" / "tb3-workspaces"


def write_crate(crate_dir: Path, name: str, version: str, license_field: str, license_lines: list[str], extra_license_files: dict[str, str] | None = None, license_file_field: str | None = None) -> None:
    crate_dir.mkdir(parents=True, exist_ok=True)
    (crate_dir / "src").mkdir(exist_ok=True)
    (crate_dir / "src" / "lib.rs").write_text(
        f"// {name} {version}\npub fn ping() -> &'static str {{ \"{name}\" }}\n",
        encoding="utf-8",
    )
    cargo_lines = [
        "[package]",
        f'name = "{name}"',
        f'version = "{version}"',
        f'license = "{license_field}"',
    ]
    if license_file_field:
        cargo_lines.append(f'license-file = "{license_file_field}"')
    (crate_dir / "Cargo.toml").write_text("\n".join(cargo_lines) + "\n", encoding="utf-8")
    if extra_license_files:
        for fname, body in extra_license_files.items():
            (crate_dir / fname).write_text(body, encoding="utf-8")
    else:
        (crate_dir / "LICENSE-MIT").write_text("\n".join(license_lines) + "\n", encoding="utf-8")


def package_checksum(crate_dir: Path) -> str:
    import hashlib

    lines: list[str] = []
    for p in sorted(crate_dir.rglob("*")):
        if not p.is_file() or p.name == ".cargo-checksum.json":
            continue
        rel = p.relative_to(crate_dir).as_posix()
        if rel.startswith(".git"):
            continue
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        lines.append(f"{rel}:{digest}")
    payload = "\n".join(lines)
    if payload:
        payload += "\n"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def write_checksum(crate_dir: Path, override: str | None = None) -> str:
    digest = override or package_checksum(crate_dir)
    data = {"files": {}, "package": digest}
    (crate_dir / ".cargo-checksum.json").write_text(json.dumps(data, sort_keys=True) + "\n", encoding="utf-8")
    return digest


def write_lock(ws: Path, packages: list[tuple[str, str]]) -> None:
    lines = ['version = 3', ""]
    for name, version in packages:
        lines.append("[[package]]")
        lines.append(f'name = "{name}"')
        lines.append(f'version = "{version}"')
        lines.append(
            f'source = "registry+https://github.com/rust-lang/crates.io-index#{name}@{version}"'
        )
        lines.append("")
    (ws / "Cargo.lock").write_text("\n".join(lines), encoding="utf-8")


def write_metadata(ws: Path, rows: list[dict[str, str]]) -> None:
    (ws / "lock-metadata.json").write_text(
        json.dumps({"packages": rows}, indent=2) + "\n", encoding="utf-8"
    )


def write_workspace(ws_id: str, base: Path, packages: list[tuple[str, str]], metadata: list[dict[str, str]], cargo_toml_extra: str = "", checksum_overrides: dict[str, str] | None = None) -> None:
    ws = base / ws_id
    ws.mkdir(parents=True, exist_ok=True)
    vendor = ws / "vendor"
    vendor.mkdir(exist_ok=True)
    write_lock(ws, packages)
    write_metadata(ws, metadata)
    cargo = '[package]\nname = "fixture-root"\nversion = "0.1.0"\nedition = "2021"\n\n'
    if cargo_toml_extra:
        cargo += cargo_toml_extra + "\n"
    (ws / "Cargo.toml").write_text(cargo, encoding="utf-8")


def build_all() -> None:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    TB3.mkdir(parents=True, exist_ok=True)

    # baseline
    ws = FIXTURES / "baseline"
    ws.mkdir(parents=True, exist_ok=True)
    write_lock(ws, [("serde", "1.0.195"), ("libc", "0.2.150")])
    write_metadata(
        ws,
        [
            {"name": "serde", "version": "1.0.195", "declared_license": "MIT"},
            {"name": "libc", "version": "0.2.150", "declared_license": "MIT"},
        ],
    )
    (ws / "Cargo.toml").write_text(
        '[package]\nname = "fixture-root"\nversion = "0.1.0"\nedition = "2021"\n',
        encoding="utf-8",
    )
    write_crate(ws / "vendor" / "serde-1.0.195", "serde", "1.0.195", "MIT", ["MIT"])
    write_crate(ws / "vendor" / "libc-0.2.150", "libc", "0.2.150", "MIT", ["MIT"])
    write_checksum(ws / "vendor" / "serde-1.0.195")
    write_checksum(ws / "vendor" / "libc-0.2.150")

    # license-drift
    ws = FIXTURES / "license-drift"
    ws.mkdir(parents=True, exist_ok=True)
    write_lock(ws, [("serde", "1.0.195")])
    write_metadata(ws, [{"name": "serde", "version": "1.0.195", "declared_license": "Apache-2.0"}])
    (ws / "Cargo.toml").write_text('[package]\nname = "fixture-root"\nversion = "0.1.0"\n', encoding="utf-8")
    write_crate(ws / "vendor" / "serde-1.0.195", "serde", "1.0.195", "Apache-2.0", ["MIT"])
    write_checksum(ws / "vendor" / "serde-1.0.195")

    # checksum-mismatch
    ws = FIXTURES / "checksum-mismatch"
    ws.mkdir(parents=True, exist_ok=True)
    write_lock(ws, [("tinyvec", "1.6.0")])
    write_metadata(ws, [{"name": "tinyvec", "version": "1.6.0", "declared_license": "MIT"}])
    (ws / "Cargo.toml").write_text('[package]\nname = "fixture-root"\nversion = "0.1.0"\n', encoding="utf-8")
    write_crate(ws / "vendor" / "tinyvec-1.6.0", "tinyvec", "1.6.0", "MIT", ["MIT"])
    write_checksum(ws / "vendor" / "tinyvec-1.6.0", override="0" * 64)

    # patched-lineage
    ws = FIXTURES / "patched-lineage"
    ws.mkdir(parents=True, exist_ok=True)
    write_lock(ws, [("serde", "1.0.195")])
    write_metadata(ws, [{"name": "serde", "version": "1.0.195", "declared_license": "MIT"}])
    (ws / "Cargo.toml").write_text(
        '[package]\nname = "fixture-root"\nversion = "0.1.0"\n\n[patch.crates-io]\nserde = { path = "patches/serde-fork" }\n',
        encoding="utf-8",
    )
    write_crate(ws / "vendor" / "serde-1.0.195", "serde", "1.0.195", "MIT", ["MIT"])
    write_checksum(ws / "vendor" / "serde-1.0.195")
    (ws / "patches" / "serde-fork").mkdir(parents=True, exist_ok=True)
    (ws / "patches" / "serde-fork" / "README.md").write_text("fork\n", encoding="utf-8")

    # duplicate-versions
    ws = FIXTURES / "duplicate-versions"
    ws.mkdir(parents=True, exist_ok=True)
    write_lock(ws, [("bitflags", "1.3.2"), ("bitflags", "0.3.2")])
    write_metadata(
        ws,
        [
            {"name": "bitflags", "version": "1.3.2", "declared_license": "MIT"},
            {"name": "bitflags", "version": "0.3.2", "declared_license": "MIT"},
        ],
    )
    (ws / "Cargo.toml").write_text('[package]\nname = "fixture-root"\nversion = "0.1.0"\n', encoding="utf-8")
    write_crate(ws / "vendor" / "bitflags-1.3.2", "bitflags", "1.3.2", "MIT", ["MIT"])
    write_crate(ws / "vendor" / "bitflags-0.3.2", "bitflags", "0.3.2", "MIT", ["MIT"])
    write_checksum(ws / "vendor" / "bitflags-1.3.2")
    write_checksum(ws / "vendor" / "bitflags-0.3.2")

    # tb3 precedence trap
    ws = TB3 / "tb3-precedence-trap"
    ws.mkdir(parents=True, exist_ok=True)
    write_lock(ws, [("ring", "0.17.8")])
    write_metadata(ws, [{"name": "ring", "version": "0.17.8", "declared_license": "ISC"}])
    (ws / "Cargo.toml").write_text('[package]\nname = "fixture-root"\nversion = "0.1.0"\n', encoding="utf-8")
    crate = ws / "vendor" / "ring-0.17.8"
    write_crate(
        crate,
        "ring",
        "0.17.8",
        "MIT",
        ["MIT"],
        extra_license_files={"LICENSE-MIT": "MIT\n", "COPYING": "ISC\n"},
        license_file_field="COPYING",
    )
    write_checksum(crate)

    # tb3 staging poison uses baseline layout
    ws = TB3 / "tb3-staging-poison"
    ws.mkdir(parents=True, exist_ok=True)
    write_lock(ws, [("serde", "1.0.195")])
    write_metadata(ws, [{"name": "serde", "version": "1.0.195", "declared_license": "MIT"}])
    (ws / "Cargo.toml").write_text('[package]\nname = "fixture-root"\nversion = "0.1.0"\n', encoding="utf-8")
    write_crate(ws / "vendor" / "serde-1.0.195", "serde", "1.0.195", "MIT", ["MIT"])
    write_checksum(ws / "vendor" / "serde-1.0.195")

    catalog = {
        "bundled": [
            "baseline",
            "license-drift",
            "checksum-mismatch",
            "patched-lineage",
            "duplicate-versions",
        ],
        "hidden": ["tb3-precedence-trap", "tb3-staging-poison"],
    }
    (ROOT / "fixtures" / "catalog.json").write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    print("fixtures written", file=sys.stderr)


if __name__ == "__main__":
    build_all()
