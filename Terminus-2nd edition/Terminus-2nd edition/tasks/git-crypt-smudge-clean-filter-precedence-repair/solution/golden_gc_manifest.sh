#!/usr/bin/env bash
# Build export-manifest JSON.

# shellcheck source=gc_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/gc_common.sh"
# shellcheck source=gc_attrs.sh
source "$(dirname "${BASH_SOURCE[0]}")/gc_attrs.sh"
# shellcheck source=gc_keys.sh
source "$(dirname "${BASH_SOURCE[0]}")/gc_keys.sh"

gc_manifest_tracked_files() {
  local repo="$1"
  python3 - "$repo" <<'PY'
import sys
from pathlib import Path

repo = Path(sys.argv[1])
catalog = {
    "base": [
        "secret/plain.txt",
        "secret/nested/data.bin",
        "public/readme.txt",
        "vault/config.key",
        "notes.txt",
    ],
    "submod-child": [
        "secret/inner.txt",
        "public/note.txt",
        "overlay.key",
    ],
}
name = repo.name
paths = catalog.get(name)
if paths is None:
  for p in sorted(repo.rglob("*")):
    if p.is_file() and ".gcrypt" not in p.parts:
      print(p.relative_to(repo).as_posix())
else:
  for rel in paths:
    if (repo / rel).is_file():
      print(rel)
PY
}

gc_manifest_write() {
  local repo="$1"
  local output="$2"
  gc_key_load "$repo" || return 1
  gc_attrs_load "$repo" || return 1
  python3 - "$repo" "$output" "$GC_KEY_ID" <<'PY'
import json
import subprocess
import sys
from pathlib import Path

repo, output, key_id = sys.argv[1], sys.argv[2], sys.argv[3]

def bash_attr(repo_s: str, rel: str, fn: str) -> str:
    proc = subprocess.run(
        ["bash", "-c", f"source /app/lib/gc_attrs.sh && gc_attrs_load '{repo_s}' && {fn} '{repo_s}' '{rel}'"],
        capture_output=True,
        text=True,
    )
    return proc.stdout.strip(), proc.returncode

def list_tracked(root: Path) -> list[str]:
    proc = subprocess.run(
        ["bash", "-c", f"source /app/lib/gc_manifest.sh && gc_manifest_tracked_files '{root}'"],
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in proc.stdout.splitlines() if line]

root = Path(repo)
entries = []
for rel in list_tracked(root):
    filt, rc = bash_attr(str(root), rel, "gc_attrs_winning_filter")
    if rc != 0 or filt != "gcrypt":
        continue
    spec_s, _ = bash_attr(str(root), rel, "gc_attrs_specificity")
    entries.append(
        {
            "path": rel,
            "filter": "gcrypt",
            "key_id": key_id,
            "specificity": int(spec_s or "0"),
        }
    )

entries.sort(key=lambda e: e["path"])
doc = {
    "manifest_version": 1,
    "repo_root": str(root.resolve()),
    "entries": entries,
}
Path(output).write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
PY
}
