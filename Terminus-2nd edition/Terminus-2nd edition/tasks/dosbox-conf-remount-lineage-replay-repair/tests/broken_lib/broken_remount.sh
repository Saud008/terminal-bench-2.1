#!/usr/bin/env bash
# Apply remaps and build mount/imgmount lineage entries.

remount_apply_path_prefix() {
  local path="$1"
  local op="${2:-mount}"
  if [[ "$op" == "imgmount" ]]; then
    printf '%s' "$path"
    return 0
  fi
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
  declare -A last_seq_for_drive=()

  local sec src cmd
  while IFS='|' read -r sec src cmd; do
    if [[ "$sec" == "config" ]]; then
      if conf_parse_remap_tokens "$cmd"; then
        REMAP_TABLE["${CONF_REMAP_FROM}"]="${CONF_REMAP_TO}"
        REMOUNT_REMAPS+=("${CONF_REMAP_FROM}|${CONF_REMAP_TO}")
      fi
      continue
    fi
    [[ "$sec" != "autoexec" ]] && continue
    conf_parse_mount_tokens "$cmd" || continue

    validate_drive_letter "${CONF_PARSE_DRIVE}" || true

    local effective_drive="${CONF_PARSE_DRIVE}"
    if [[ "$sec" == "autoexec" && -z "${REMAP_TABLE[${CONF_PARSE_DRIVE}]:-}" ]]; then
      effective_drive="${CONF_PARSE_DRIVE}"
    else
      effective_drive="${REMAP_TABLE[${CONF_PARSE_DRIVE}]:-${CONF_PARSE_DRIVE}}"
    fi

    local effective_path
    effective_path="$(remount_apply_path_prefix "${CONF_PARSE_PATH}" "${CONF_PARSE_OP}")"

    local seq
    if [[ -n "${last_seq_for_drive[${effective_drive}]:-}" ]]; then
      seq="${last_seq_for_drive[${effective_drive}]}"
      local idx=$((seq - 1))
      REMOUNT_LINEAGE[$idx]="${seq}|${CONF_PARSE_OP}|${effective_drive}|${effective_path}|${src}"
    else
      seq=$((${#REMOUNT_LINEAGE[@]} + 1))
      REMOUNT_LINEAGE+=("${seq}|${CONF_PARSE_OP}|${effective_drive}|${effective_path}|${src}")
      last_seq_for_drive["${effective_drive}"]="$seq"
    fi

    drive_stack_count["${effective_drive}"]=1
  done < "${ordered_file}"

  REMOUNT_STACK_DEPTH=1
  if ((${#drive_stack_count[@]} > 0)); then
    REMOUNT_STACK_DEPTH=1
  fi
  REMOUNT_RC=0
  return 0
}
