#!/usr/bin/env bash

source /app/lib/common.sh
source /app/lib/inventory.sh
source /app/lib/role.sh
source /app/lib/merge.sh
source /app/lib/include_vars.sh

resolve_playbook_manifest() {
  local playbook="$1"
  load_yaml_vars_quiet "$playbook"
}

resolve_stack() {
  local playbook="$1"
  local inventory_root="$2"
  local host="$3"
  local seed="$4"
  local extra_vars_file="${5:-}"

  local playbook_dir
  playbook_dir="$(dirname "$playbook")"
  local manifest
  manifest="$(resolve_playbook_manifest "$playbook")"
  local behaviour
  behaviour="$(json_get hash_behaviour "$manifest")"
  [[ -n "$behaviour" ]] || behaviour="replace"

  local merged='{}'
  local path chunk

  local -a roles=()
  mapfile -t roles < <(python3 - "$manifest" <<'PY'
import json, sys
data = json.loads(sys.argv[1])
for role in data.get("roles", []):
    print(role)
PY
)
  local role defaults role_vars
  for role in "${roles[@]}"; do
    defaults="/app/roles/${role}/defaults/main.yml"
    if [[ -f "$defaults" ]]; then
      chunk="$(load_yaml_vars "$defaults")"
      merged="$(apply_var_layer "$merged" "$chunk" "$behaviour")"
    fi
  done

  while read -r path; do
    [[ -n "$path" ]] || continue
    chunk="$(load_yaml_vars "$path")"
    merged="$(apply_var_layer "$merged" "$chunk" "$behaviour")"
  done < <(collect_group_var_files "$inventory_root" "$host")

  while read -r path; do
    [[ -n "$path" ]] || continue
    chunk="$(load_yaml_vars "$path")"
    merged="$(apply_var_layer "$merged" "$chunk" "$behaviour")"
  done < <(collect_host_var_file "$inventory_root" "$host")

  for role in "${roles[@]}"; do
    role_vars="/app/roles/${role}/vars/main.yml"
    if [[ -f "$role_vars" ]]; then
      chunk="$(load_yaml_vars "$role_vars")"
      merged="$(apply_var_layer "$merged" "$chunk" "$behaviour")"
    fi
  done

  chunk="$(resolve_include_vars "$playbook_dir" "$manifest")"
  merged="$(apply_var_layer "$merged" "$chunk" "$behaviour")"

  playbook_chunk="$(python3 - "$manifest" <<'PY'
import json, sys
data = json.loads(sys.argv[1])
print(json.dumps(data.get("vars", {}), sort_keys=True))
PY
)"
  merged="$(apply_var_layer "$merged" "$playbook_chunk" "$behaviour")"

  if [[ -n "$extra_vars_file" && -f "$extra_vars_file" ]]; then
    chunk="$(load_yaml_vars "$extra_vars_file")"
    merged="$(apply_var_layer "$merged" "$chunk" "$behaviour")"
  fi

  python3 - "$host" "$seed" "$merged" <<'PY'
import json, sys
host, seed, merged = sys.argv[1], sys.argv[2], sys.argv[3]
print(json.dumps({"host": host, "seed": seed, "merged": json.loads(merged)}, sort_keys=True))
PY
}
