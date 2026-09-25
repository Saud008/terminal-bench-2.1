#!/usr/bin/env bash
# Build remount lineage with remap and stacking.

remount_apply_path_prefix() {
  local path="$1"
  local letter="${path:0:1}"
  letter="${letter^^}"
  if [[ ${#path} -ge 2 && "${path:1:1}" == ":" ]]; then
    if [[ -n "${REMAP_TABLE[$letter]:-}" ]]; then
      printf '%s%s' "${REMAP_TABLE[$letter]}" "${path:1}"
      return 0
    fi
  fi
  printf '%s' "$path"
}

remount_render_plan() {
  local ordered_file="$1"
  REMOUNT_LINEAGE=()
  REMOUNT_REMAPS=()
  REMOUNT_WARNINGS=()
  REMOUNT_ERRORS=()
  declare -gA REMAP_TABLE=()
  declare -A drive_stack_count=()

  local sec src cmd
  while IFS='|' read -r sec src cmd; do
    [[ "$sec" != "config" ]] && continue
    if conf_parse_remap_tokens "$cmd"; then
      REMAP_TABLE["${CONF_REMAP_FROM}"]="${CONF_REMAP_TO}"
      REMOUNT_REMAPS+=("${CONF_REMAP_FROM}|${CONF_REMAP_TO}")
    fi
  done < "${ordered_file}"

  local seq=0
  while IFS='|' read -r sec src cmd; do
    [[ "$sec" != "autoexec" ]] && continue
    conf_parse_mount_tokens "$cmd" || continue

    if ! validate_drive_letter "${CONF_PARSE_DRIVE}"; then
      REMOUNT_ERRORS+=("invalid drive letter: ${CONF_PARSE_DRIVE}")
      REMOUNT_RC=2
      return 1
    fi

    local effective_drive="${REMAP_TABLE[${CONF_PARSE_DRIVE}]:-${CONF_PARSE_DRIVE}}"
    local effective_path
    effective_path="$(remount_apply_path_prefix "${CONF_PARSE_PATH}")"

    seq=$((seq + 1))
    REMOUNT_LINEAGE+=("${seq}|${CONF_PARSE_OP}|${effective_drive}|${effective_path}|${src}")

    local stack_key="${effective_drive}"
    drive_stack_count["${stack_key}"]=$(( ${drive_stack_count[${stack_key}]:-0} + 1 ))
  done < "${ordered_file}"

  REMOUNT_STACK_DEPTH=0
  local k
  for k in "${!drive_stack_count[@]}"; do
    if ((${drive_stack_count[$k]} > REMOUNT_STACK_DEPTH)); then
      REMOUNT_STACK_DEPTH=${drive_stack_count[$k]}
    fi
  done
  REMOUNT_RC=0
  return 0
}
