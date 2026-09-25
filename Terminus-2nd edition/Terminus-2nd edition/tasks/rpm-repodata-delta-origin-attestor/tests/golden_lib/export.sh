#!/usr/bin/env bash

export_attestation() {
  local out="$1"
  python3 - "$out" <<'PY'
import hashlib, json, sys
from pathlib import Path
stage = json.loads(Path("/app/state/repo-stage.json").read_text(encoding="utf-8"))
packages = sorted(stage.get("packages", []), key=lambda p: p.get("nevra", ""))
modules = sorted(stage.get("module_defaults", []), key=lambda m: m.get("module", ""))
digest_payload = {
    "module_defaults": modules,
    "mirror_repo_revision": stage.get("mirror_repo_revision", ""),
    "packages": sorted(p.get("nevra", "") for p in packages),
    "repomd_revision": stage.get("repomd_revision", ""),
}
digest = hashlib.sha256(
    json.dumps(digest_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
).hexdigest()
export_doc = {
    "repo_id": stage.get("repo_id", ""),
    "ingest_seq": stage.get("ingest_seq", 0),
    "repomd_revision": stage.get("repomd_revision", ""),
    "checksum_ok": stage.get("checksum_ok", False),
    "mirror_snapshot_valid": stage.get("mirror_snapshot_valid", False),
    "packages": packages,
    "module_defaults": modules,
    "origin_digest": f"sha256:{digest}",
}
Path(sys.argv[1]).parent.mkdir(parents=True, exist_ok=True)
Path(sys.argv[1]).write_text(json.dumps(export_doc, sort_keys=True, indent=2) + "\n", encoding="utf-8")
PY
}
