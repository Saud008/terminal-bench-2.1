#!/usr/bin/env bash
set -euo pipefail
CTGC_LIB="${CTGC_LIB:-/app/lib}"
source "${CTGC_LIB}/common.sh"

_load_namespace_meta() {
  local dir="$1"
  local arr="[]"
  if [[ -d "$dir" ]]; then
    while IFS= read -r f; do
      arr="$(jq -c --argjson cur "$arr" --slurpfile doc "$f" '$cur + [$doc[0]]' <<< "$arr")"
    done < <(find "$dir" -mindepth 2 -maxdepth 2 -type f -name '*.json' | sort)
  fi
  printf '%s' "$arr"
}

_load_json_dir() {
  local dir="$1"
  local arr="[]"
  if [[ -d "$dir" ]]; then
    while IFS= read -r f; do
      arr="$(jq -c --argjson cur "$arr" --slurpfile doc "$f" '$cur + [$doc[0]]' <<< "$arr")"
    done < <(find "$dir" -mindepth 1 -maxdepth 1 -type f -name '*.json' | sort)
  fi
  printf '%s' "$arr"
}

scan_meta_tree() {
  local root="$1" ns_filter="$2" out="$3"
  local ns_dir="${root}/namespaces"
  local img_dir="${root}/images"
  local lease_dir="${root}/leases"
  local snap_dir="${root}/snapshots"
  local namespaces images leases snapshots lines digest
  namespaces="$(_load_namespace_meta "$ns_dir")"
  images="$(_load_json_dir "$img_dir")"
  leases="$(_load_json_dir "$lease_dir")"
  snapshots="$(_load_json_dir "$snap_dir")"
  if [[ -n "$ns_filter" ]]; then
    namespaces="$(jq -c --arg ns "$ns_filter" '[.[] | select(.name == $ns)]' <<< "$namespaces")"
  fi
  lines=""
  lines+="namespaces=$(jq -c 'sort_by(.name)' <<< "$namespaces")"$'\n'
  lines+="images=$(jq -c 'sort_by(.digest)' <<< "$images")"$'\n'
  lines+="leases=$(jq -c 'sort_by(.id)' <<< "$leases")"$'\n'
  lines+="snapshots=$(jq -c 'sort_by(.key)' <<< "$snapshots")"$'\n'
  digest="$(sha256_lines "${lines%$'\n'}")"
  ensure_state_dir
  local prev=""
  if [[ -f "$out" ]]; then
    prev="$(jq -r '.meta_digest // ""' "$out" 2>/dev/null || true)"
  fi
  local seq
  seq="$(read_revision_seq)"
  if [[ "$digest" != "$prev" ]]; then
    seq=$((seq + 1))
    write_revision_seq "$seq"
  fi
  jq -n \
    --argjson namespaces "$namespaces" \
    --argjson images "$images" \
    --argjson leases "$leases" \
    --argjson snapshots "$snapshots" \
    --arg digest "$digest" \
    '{schema_version:1,namespaces:$namespaces,images:$images,leases:$leases,snapshots:$snapshots,meta_digest:$digest}' \
    | jq -S '.' > "$out"
}
