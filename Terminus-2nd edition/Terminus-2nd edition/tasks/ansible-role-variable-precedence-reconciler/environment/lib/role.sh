#!/usr/bin/env bash

resolve_role_vars() {
  local roles_root="$1"
  shift
  local merged='{}'
  local role
  for role in "$@"; do
    local defaults="${roles_root}/${role}/defaults/main.yml"
    local role_vars="${roles_root}/${role}/vars/main.yml"
    if [[ -f "$role_vars" ]]; then
      local chunk
      chunk="$(load_yaml_vars "$role_vars")"
      merged="$(merge_shallow "$merged" "$chunk")"
    fi
    if [[ -f "$defaults" ]]; then
      local chunk
      chunk="$(load_yaml_vars "$defaults")"
      merged="$(merge_shallow "$merged" "$chunk")"
    fi
  done
  printf '%s' "$merged"
}
