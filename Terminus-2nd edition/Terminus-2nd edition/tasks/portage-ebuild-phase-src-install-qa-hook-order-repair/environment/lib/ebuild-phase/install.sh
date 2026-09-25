#!/usr/bin/env bash

doins_tree() {
  local tree="$1"
  local count
  count="$(jq '.entries | length' "${tree}/manifest.json")"
  local i=0
  while [ "${i}" -lt "${count}" ]; do
    local etype dest src mode target
    etype="$(jq -r ".entries[${i}].type" "${tree}/manifest.json")"
    dest="$(jq -r ".entries[${i}].dest" "${tree}/manifest.json")"
    case "${etype}" in
      file)
        src="$(jq -r ".entries[${i}].src" "${tree}/manifest.json")"
        mode="$(jq -r ".entries[${i}].mode // \"0644\"" "${tree}/manifest.json")"
        mkdir -p "$(dirname "${D}/${dest}")"
        install -m "${mode}" "${tree}/${src}" "${D}/${dest}"
        ;;
      symlink)
        target="$(jq -r ".entries[${i}].target" "${tree}/manifest.json")"
        mkdir -p "$(dirname "${D}/${dest}")"
        doins_symlink "${dest}" "${target}" "${tree}"
        ;;
      *)
        echo "unknown entry type ${etype}" >&2
        return 1
        ;;
    esac
    i=$((i + 1))
  done
}

doins_symlink() {
  local dest="$1"
  local target="$2"
  local tree="$3"
  local link="${D}/${dest}"
  local abs_target
  abs_target="$(readlink -f "${tree}/${target}" 2>/dev/null || realpath "${tree}/${target}")"
  ln -sfn "${abs_target}" "${link}"
}

apply_fperms() {
  local tree="$1"
  local lines
  mapfile -t lines < <(jq -r '.fperms[]? // empty' "${tree}/manifest.json")
  local line
  for line in "${lines[@]}"; do
    [ -n "${line}" ] || continue
    local mode path
    mode="${line%% *}"
    path="${line#* }"
    chmod "${mode}" "${D}/${path}" 2>/dev/null || true
  done
}

dosbin_strip() {
  local tree="$1"
  local paths
  mapfile -t paths < <(jq -r '.dosbin_paths[]? // empty' "${tree}/manifest.json")
  local p
  for p in "${paths[@]}"; do
    [ -n "${p}" ] || continue
    if [ -f "${D}/${p}" ]; then
      chmod 0755 "${D}/${p}"
    fi
  done
}
