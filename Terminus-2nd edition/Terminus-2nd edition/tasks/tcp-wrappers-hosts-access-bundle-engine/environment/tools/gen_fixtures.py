#!/usr/bin/env python3
"""Build-time seed-derived except bundle (not in static catalog)."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUNDLES = ROOT / "fixtures" / "bundles"
BUILD_SEED = os.environ.get("VERIFIER_SEED", "tcp-wrappers-hosts-access-bundle-engine")


def tag(seed: str) -> int:
    h = hashlib.sha256(f"{BUILD_SEED}:{seed}".encode()).digest()
    return (h[0] % 200) + 10


def bundle_name() -> str:
    digest = hashlib.sha256(BUILD_SEED.encode()).hexdigest()[:8]
    return f"dynamic-except-{digest}"


def write_bundle() -> None:
    name = bundle_name()
    bdir = BUNDLES / name
    if bdir.exists():
        import shutil

        shutil.rmtree(bdir)
    bdir.mkdir(parents=True)

    a = tag("except-a")
    b = tag("except-b")
    probe = tag("probe")

    (bdir / "manifest.json").write_text(
        json.dumps(
            {
                "name": name,
                "allow_files": ["allow/10-wide.allow"],
                "deny_files": [],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    allow_dir = bdir / "allow"
    allow_dir.mkdir()
    (allow_dir / "10-wide.allow").write_text(
        f"sshd: ALL EXCEPT 192.0.2.{a} 192.0.2.{b}\n",
        encoding="utf-8",
    )

    manifest = {
        "dynamic_bundle": name,
        "build_seed": BUILD_SEED,
        "except_hosts": [f"192.0.2.{a}", f"192.0.2.{b}"],
        "probe_allow": f"192.0.2.{probe}",
    }
    (ROOT / "fixtures" / "_dynamic_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Generated dynamic bundle {name}")


if __name__ == "__main__":
    write_bundle()
