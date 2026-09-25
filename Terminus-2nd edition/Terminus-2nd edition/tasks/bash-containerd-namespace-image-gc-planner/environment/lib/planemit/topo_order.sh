#!/usr/bin/env bash
set -euo pipefail
CTGC_LIB="${CTGC_LIB:-/app/lib}"
source "${CTGC_LIB}/common.sh"
# shellcheck source=../imgref/manifest_index.sh
source "${CTGC_LIB}/imgref/manifest_index.sh"
# shellcheck source=../leaseio/lease_shield.sh
source "${CTGC_LIB}/leaseio/lease_shield.sh"
# shellcheck source=../snapgc/ancestor_keep.sh
source "${CTGC_LIB}/snapgc/ancestor_keep.sh"

resolve_gc_eligibility() {
  local snap_src="$1" now="$2" out="$3"
  local data ns images leases snaps
  data="$(cat "$snap_src")"
  ns="$(jq -c '.namespaces' <<< "$data")"
  images="$(jq -c '.images' <<< "$data")"
  leases="$(jq -c '.leases' <<< "$data")"
  snaps="$(jq -c '.snapshots' <<< "$data")"
  local protected
  protected="$(lease_protected_keys "$leases" "$now" "$snaps")"
  protected="$(expand_retained_snapshots "$protected" "$snaps")"
  local pins
  pins="$(jq -c '[.[] | .retention_pins[]?] | unique' <<< "$ns")"
  local dangling deletable_snaps deletable_imgs
  dangling='[]'
  deletable_snaps="$(jq -c --argjson prot "$protected" '[.[] | select(.key as $k | ($prot | index($k)) | not)] | map(.key)' <<< "$snaps")"
  deletable_imgs='[]'
  jq -n \
    --argjson protected "$protected" \
    --argjson dangling "$dangling" \
    --argjson deletable_snapshots "$deletable_snaps" \
    --argjson deletable_images "$deletable_imgs" \
    --arg now "$now" \
    '{schema_version:1,protected_snapshots:$protected,dangling_images:$dangling,deletable_snapshots:$deletable_snapshots,deletable_images:$deletable_images,resolve_now:$now,resolve_digest:"broken"}' \
    | jq -S '.' > "$out"
}

emit_gc_plan() {
  local buffer_src="$1" out="$2"
  local snaps imgs
  snaps="$(jq -c '.deletable_snapshots' "$buffer_src")"
  imgs="$(jq -c '.deletable_images' "$buffer_src")"
  local actions="[]"
  while IFS= read -r key; do
    [[ -z "$key" ]] && continue
    actions="$(jq -c --arg k "$key" --argjson a "$actions" '$a + [{action:"delete",kind:"snapshot",key:$k}]' <<< "$actions")"
  done < <(jq -r '.[]' <<< "$snaps")
  while IFS= read -r dig; do
    [[ -z "$dig" ]] && continue
    actions="$(jq -c --arg d "$dig" --argjson a "$actions" '$a + [{action:"delete",kind:"image",digest:$d}]' <<< "$actions")"
  done < <(jq -r '.[]' <<< "$imgs")
  local digest
  digest="$(sha256_lines "$(jq -c '.' <<< "$actions")")"
  jq -n \
    --argjson actions "$actions" \
    --arg digest "$digest" \
    '{schema_version:1,mode:"dry-run",actions:$actions,plan_digest:$digest}' \
    | jq -S '.' > "$out"
}
