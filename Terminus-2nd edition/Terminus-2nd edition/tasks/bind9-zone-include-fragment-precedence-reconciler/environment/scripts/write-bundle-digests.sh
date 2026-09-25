#!/usr/bin/env bash
# Record sha256 digests for every bundle input file (build-time; anti-tamper baseline).
set -euo pipefail
python3 - <<'PY'
import hashlib
import json
from pathlib import Path

manifest: dict[str, dict[str, str]] = {}


def digest_tree(root: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            rel = path.relative_to(root).as_posix()
            entries[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return entries


for bundles_root, prefix in (
    (Path("/app/fixtures/bundles"), "bundles"),
    (Path("/opt/verifier-fixtures"), "hidden"),
):
    if not bundles_root.is_dir():
        continue
    for bundle in sorted(bundles_root.iterdir()):
        if bundle.is_dir():
            manifest[f"{prefix}/{bundle.name}"] = digest_tree(bundle)

out = Path("/app/fixtures/bundle-digests.json")
out.write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")
print(f"wrote {out} ({len(manifest)} bundles)")

import subprocess

subprocess.run(
    [
        "find",
        "/app/fixtures/bundles",
        "/opt/verifier-fixtures",
        "/opt/verifier-golden",
        "-exec",
        "chmod",
        "a-w",
        "{}",
        "+",
    ],
    check=True,
)
PY
