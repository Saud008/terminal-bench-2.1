#!/usr/bin/env bash

S2_META_SEED=""
S2_META_ROOTFS=""
S2_META_CODENAME=""
S2_META_MERGED_USR=0
S2_META_SUITE_RETRY=0
S2_ROOTFS_DIR=""
S2_TREE_DIR=""

s2_load_meta() {
  local rootfs="$1"
  S2_ROOTFS_DIR="$rootfs"
  S2_TREE_DIR="${rootfs}/tree"
  local meta="${rootfs}/meta.json"
  S2_META_SEED="$(python3 - "$meta" <<'PY'
import json, sys
print(json.load(open(sys.argv[1], encoding="utf-8"))["seed"])
PY
)"
  S2_META_ROOTFS="$(python3 - "$meta" <<'PY'
import json, sys
print(json.load(open(sys.argv[1], encoding="utf-8"))["name"])
PY
)"
  S2_META_CODENAME="$(python3 - "$meta" <<'PY'
import json, sys
print(json.load(open(sys.argv[1], encoding="utf-8"))["codename"])
PY
)"
  S2_META_MERGED_USR="$(python3 - "$meta" <<'PY'
import json, sys
print(1 if json.load(open(sys.argv[1], encoding="utf-8")).get("merged_usr") else 0)
PY
)"
  S2_META_SUITE_RETRY="$(python3 - "$meta" <<'PY'
import json, sys
print(int(json.load(open(sys.argv[1], encoding="utf-8")).get("suite_retry") or 0))
PY
)"
}

s2_load_mounts() {
  local rootfs="$1"
  S2_MOUNTS_JSON="${rootfs}/mounts.json"
}
