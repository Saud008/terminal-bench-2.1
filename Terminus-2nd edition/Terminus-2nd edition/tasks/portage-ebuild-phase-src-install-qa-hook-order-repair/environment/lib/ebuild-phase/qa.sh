#!/usr/bin/env bash

qa_check_normalized_dirs() {
  local bad
  bad="$(find "${D}" -type d ! -perm 0755 2>/dev/null | head -n 1 || true)"
  if [ -n "${bad}" ]; then
    echo "QA: directory not normalized to 0755: ${bad}" >&2
    return 1
  fi
  return 0
}

qa_check_symlinks_contained() {
  local link
  while IFS= read -r -d '' link; do
    local target resolved
    target="$(readlink "${link}")"
    if [[ "${target}" = /* ]]; then
      resolved="${target}"
    else
      resolved="$(cd "$(dirname "${link}")" && readlink -f "${target}")"
    fi
    case "${resolved}" in
      "${D}"/*) ;;
      *)
        echo "QA: symlink escapes DEST: ${link} -> ${resolved}" >&2
        return 1
        ;;
    esac
  done < <(find "${D}" -type l -print0 2>/dev/null)
  return 0
}

qa_check_setuid_preserved() {
  local tree="$1"
  local paths
  mapfile -t paths < <(jq -r '.fperms[]? // empty' "${tree}/manifest.json")
  local line
  for line in "${paths[@]}"; do
    [ -n "${line}" ] || continue
    local mode path
    mode="${line%% *}"
    path="${line#* }"
    case "${mode}" in
      4*) ;;
      *) continue ;;
    esac
    if [ ! -u "${D}/${path}" ]; then
      echo "QA: setuid bit missing on ${path}" >&2
      return 1
    fi
  done
  return 0
}

qa_run_preflight() {
  local tree="$1"
  qa_check_normalized_dirs
  qa_check_symlinks_contained
  qa_check_setuid_preserved "${tree}"
}

qa_run_postflight() {
  local tree="$1"
  qa_check_normalized_dirs
  qa_check_symlinks_contained
  qa_check_setuid_preserved "${tree}"
}
