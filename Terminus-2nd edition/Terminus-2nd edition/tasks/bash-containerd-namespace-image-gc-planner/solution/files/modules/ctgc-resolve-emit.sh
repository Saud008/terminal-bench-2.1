#!/usr/bin/env bash
set -euo pipefail
CTGC_LIB="${CTGC_LIB:-/app/lib}"
source "${CTGC_LIB}/common.sh"
source "${CTGC_LIB}/imgref/manifest_index.sh"
source "${CTGC_LIB}/leaseio/lease_shield.sh"
source "${CTGC_LIB}/snapgc/ancestor_keep.sh"

resolve_gc_eligibility() {
  local snap_src="$1" now="$2" out="$3"
  local data ns images leases snaps
  data="$(cat "$snap_src")"
  ns="$(jq -c '.namespaces' <<< "$data")"
  images="$(jq -c '.images' <<< "$data")"
  leases="$(jq -c '.leases' <<< "$data")"
  snaps="$(jq -c '.snapshots' <<< "$data")"
  local protected pins pin_snaps
  protected="$(lease_protected_keys "$leases" "$now" "$snaps")"
  pins="$(jq -c '[.[] | .retention_pins[]?] | unique' <<< "$ns")"
  local pin_roots
  pin_roots="$(jq -nc --argjson pins "$pins" --argjson snaps "$snaps" '
    [$pins[] as $d | $snaps[] | select(.refs[]? == $d) | .key] | unique
  ')"
  protected="$(jq -nc --argjson add "$pin_roots" --argjson cur "$protected" '$cur + $add | unique')"
  protected="$(expand_retained_snapshots "$protected" "$snaps")"
  local dangling deletable_snaps deletable_imgs depth_map
  dangling="$(find_dangling_images "$images" "$snaps")"
  depth_map="$(snapshot_depth_map "$snaps")"
  deletable_snaps="$(jq -nc --argjson prot "$protected" --argjson depths "$depth_map" --argjson snaps "$snaps" '
    [$snaps[] | .key as $k | select(($prot | index($k)) | not) | $k] |
    sort_by(-($depths[.] // 0))
  ')"
  deletable_imgs="$(jq -nc --argjson dangling "$dangling" --argjson pins "$pins" '
    [$dangling[] | select(. as $d | ($pins | index($d)) | not)] | sort
  ')"
  local rdigest
  rdigest="$(sha256_lines "prot=$(jq -c '.' <<< "$protected")|del_s=$(jq -c '.' <<< "$deletable_snaps")|del_i=$(jq -c '.' <<< "$deletable_imgs")")"
  jq -n \
    --argjson protected "$protected" \
    --argjson dangling "$dangling" \
    --argjson deletable_snapshots "$deletable_snaps" \
    --argjson deletable_images "$deletable_imgs" \
    --arg now "$now" \
    --arg digest "$rdigest" \
    '{schema_version:1,protected_snapshots:$protected,dangling_images:$dangling,deletable_snapshots:$deletable_snapshots,deletable_images:$deletable_images,resolve_now:$now,resolve_digest:$digest}' \
    | jq -S '.' > "$out"
}

emit_gc_plan() {
  local buffer_src="$1" out="$2"
  local snaps imgs actions
  snaps="$(jq -c '.deletable_snapshots' "$buffer_src")"
  imgs="$(jq -c '.deletable_images' "$buffer_src")"
  actions='[]'
  while IFS= read -r key; do
    [[ -z "$key" ]] && continue
    actions="$(jq -c --arg k "$key" --argjson a "$actions" '$a + [{action:"delete",kind:"snapshot",key:$k}]' <<< "$actions")"
  done < <(jq -r '.[]' <<< "$snaps")
  while IFS= read -r dig; do
    [[ -z "$dig" ]] && continue
    actions="$(jq -c --arg d "$dig" --argjson a "$actions" '$a + [{action:"delete",kind:"image",digest:$d}]' <<< "$actions")"
  done < <(jq -r '.[]' <<< "$imgs")
  local digest lines
  lines="$(jq -r '.[] | if .kind == "snapshot" then "s:\(.key)" else "i:\(.digest)" end' <<< "$actions" | tr -d '\n')"
  digest="$(sha256_lines "$lines")"
  jq -n \
    --argjson actions "$actions" \
    --arg digest "$digest" \
    '{schema_version:1,mode:"dry-run",actions:$actions,plan_digest:$digest}' \
    | jq -S '.' > "$out"
}
