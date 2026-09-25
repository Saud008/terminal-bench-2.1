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
  local inventory_chunk roles_chunk include_chunk playbook_chunk extra_chunk

  inventory_chunk="$(resolve_inventory_vars "$inventory_root" "$host")"
  merged="$(apply_var_layer "$merged" "$inventory_chunk" "$behaviour")"

  local -a roles=()
  mapfile -t roles < <(python3 - "$manifest" <<'PY'
import json, sys
data = json.loads(sys.argv[1])
for role in data.get("roles", []):
    print(role)
PY
)
  if [[ ${#roles[@]} -gt 0 ]]; then
    roles_chunk="$(resolve_role_vars "/app/roles" "${roles[@]}")"
    merged="$(apply_var_layer "$merged" "$roles_chunk" "$behaviour")"
  fi

  include_chunk="$(resolve_include_vars "$playbook_dir" "$manifest")"
  merged="$(apply_var_layer "$merged" "$include_chunk" "$behaviour")"

  if [[ -n "$extra_vars_file" && -f "$extra_vars_file" ]]; then
    extra_chunk="$(load_yaml_vars "$extra_vars_file")"
    merged="$(apply_var_layer "$merged" "$extra_chunk" "$behaviour")"
  fi

  playbook_chunk="$(python3 - "$manifest" <<'PY'
import json, sys
data = json.loads(sys.argv[1])
print(json.dumps(data.get("vars", {}), sort_keys=True))
PY
)"
  merged="$(apply_var_layer "$merged" "$playbook_chunk" "$behaviour")"

  python3 - "$host" "$seed" "$merged" <<'PY'
import json, sys
host, seed, merged = sys.argv[1], sys.argv[2], sys.argv[3]
print(json.dumps({"host": host, "seed": seed, "merged": json.loads(merged)}, sort_keys=True))
PY
}
