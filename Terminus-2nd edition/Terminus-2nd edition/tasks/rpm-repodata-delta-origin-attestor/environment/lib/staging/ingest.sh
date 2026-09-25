#!/usr/bin/env bash

source /app/lib/repomd.sh
source /app/lib/primary.sh
source /app/lib/modules.sh
source /app/lib/mirror.sh
source /app/lib/lineage.sh

STAGE_PATH="/app/state/repo-stage.json"

read_stage_ingest_seq() {
  if [[ -f "$STAGE_PATH" ]]; then
    python3 - "$STAGE_PATH" <<'PY'
import json, sys
from pathlib import Path
p = Path(sys.argv[1])
if p.is_file():
    data = json.loads(p.read_text(encoding="utf-8"))
    print(int(data.get("ingest_seq", 0)))
else:
    print(0)
PY
  else
    echo 0
  fi
}

ingest_repository() {
  local repo_dir="$1"
  local mirror_manifest="$2"
  local repo_root
  repo_root="$(cd "$repo_dir" && pwd)"
  local repomd="${repo_root}/repodata/repomd.xml"
  local revision
  revision="$(parse_repomd_revision "$repomd")"
  local checksum_ok="false"
  if verify_repomd_checksums "$repo_root"; then
    checksum_ok="true"
  fi
  local packages_raw
  packages_raw="$(parse_primary_packages "${repo_root}/repodata/primary.xml")"
  local packages
  packages="$(assign_lineage_ranks "$packages_raw")"
  local module_defaults
  module_defaults="$(parse_module_defaults "${repo_root}/repodata/modules.yaml")"
  local mirror_valid
  mirror_valid="$(validate_mirror_snapshot "$mirror_manifest" "$revision")"
  local mirror_repo_revision=""
  mirror_repo_revision="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1],encoding="utf-8")).get("repo_revision",""))' "$mirror_manifest")"
  local seq
  seq="$(read_stage_ingest_seq)"
  seq=$((seq + 1))
  python3 - "$repo_root" "$mirror_manifest" "$revision" "$checksum_ok" "$packages" "$module_defaults" "$mirror_valid" "$mirror_repo_revision" "$seq" <<'PY'
import json, sys
repo_root, mirror_manifest, revision, checksum_ok, packages, module_defaults, mirror_valid, mirror_repo_revision, seq = sys.argv[1:10]
stage = {
    "repo_dir": repo_root,
    "repo_id": repo_root.rstrip("/").split("/")[-1],
    "mirror_manifest_path": mirror_manifest,
    "repomd_revision": revision,
    "checksum_ok": checksum_ok == "true",
    "packages": json.loads(packages),
    "module_defaults": json.loads(module_defaults),
    "mirror_snapshot_valid": mirror_valid == "true",
    "mirror_repo_revision": mirror_repo_revision,
    "ingest_seq": int(seq),
}
from pathlib import Path
Path("/app/state").mkdir(parents=True, exist_ok=True)
Path("/app/state/repo-stage.json").write_text(json.dumps(stage, sort_keys=True, indent=2) + "\n", encoding="utf-8")
PY
}
