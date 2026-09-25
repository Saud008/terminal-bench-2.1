#!/usr/bin/env bash

inventory_groups_for_host() {
  local inventory="$1"
  local host="$2"
  python3 - "$inventory" "$host" <<'PY'
import sys
from pathlib import Path

inventory = Path(sys.argv[1])
host = sys.argv[2]
groups = []
current = None
for raw in inventory.read_text(encoding="utf-8").splitlines():
    line = raw.strip()
    if not line or line.startswith("#") or line.startswith(";"):
        continue
    if line.startswith("[") and line.endswith("]"):
        header = line[1:-1]
        if ":children" in header or ":vars" in header:
            current = None
            continue
        current = header
        continue
    if current and line.split()[0] == host:
        groups.append(current)
print(" ".join(groups))
PY
}

collect_group_var_files() {
  local inventory_root="$1"
  local host="$2"
  local -a files=()
  local group
  if [[ -f "${inventory_root}/group_vars/all.yml" ]]; then
    files+=("${inventory_root}/group_vars/all.yml")
  fi
  while read -r group; do
    [[ -n "$group" ]] || continue
    if [[ -f "${inventory_root}/group_vars/${group}.yml" ]]; then
      files+=("${inventory_root}/group_vars/${group}.yml")
    fi
  done < <(inventory_groups_for_host "${inventory_root}/hosts.ini" "$host" | tr ' ' '\n' | sort -r)
  printf '%s\n' "${files[@]}"
}

collect_host_var_file() {
  local inventory_root="$1"
  local host="$2"
  local path="${inventory_root}/host_vars/${host}.yml"
  [[ -f "$path" ]] && printf '%s\n' "$path"
}

resolve_inventory_vars() {
  local inventory_root="$1"
  local host="$2"
  local merged='{}'
  local path
  while read -r path; do
    [[ -n "$path" ]] || continue
    local chunk
    chunk="$(load_yaml_vars "$path")"
    merged="$(merge_shallow "$merged" "$chunk")"
  done < <(collect_host_var_file "$inventory_root" "$host")
  while read -r path; do
    [[ -n "$path" ]] || continue
    local chunk
    chunk="$(load_yaml_vars "$path")"
    merged="$(merge_shallow "$merged" "$chunk")"
  done < <(collect_group_var_files "$inventory_root" "$host")
  printf '%s' "$merged"
}
