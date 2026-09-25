#!/usr/bin/env bash
# ctrgc CLI dispatch
set -euo pipefail

CTGC_LIB="${CTGC_LIB:-/app/lib}"
# shellcheck source=common.sh
source "${CTGC_LIB}/common.sh"
# shellcheck source=nsio/meta_loader.sh
source "${CTGC_LIB}/nsio/meta_loader.sh"
# shellcheck source=imgref/manifest_index.sh
source "${CTGC_LIB}/imgref/manifest_index.sh"
# shellcheck source=leaseio/lease_shield.sh
source "${CTGC_LIB}/leaseio/lease_shield.sh"
# shellcheck source=snapgc/ancestor_keep.sh
source "${CTGC_LIB}/snapgc/ancestor_keep.sh"
# shellcheck source=planemit/topo_order.sh
source "${CTGC_LIB}/planemit/topo_order.sh"

cmd_scan_meta() {
  local meta_root="" ns_filter="" out="/app/state/gc_snapshot.json"
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --meta-root) meta_root="$2"; shift 2 ;;
      --namespace) ns_filter="$2"; shift 2 ;;
      --out) out="$2"; shift 2 ;;
      *) echo "CTGC: unknown scan-meta arg $1" >&2; return 2 ;;
    esac
  done
  [[ -z "$meta_root" ]] && return 2
  scan_meta_tree "$meta_root" "$ns_filter" "$out"
}

cmd_resolve() {
  local snap_path="/app/state/gc_snapshot.json" now="" out="/app/state/eligibility.buffer"
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --gc-snapshot) snap_path="$2"; shift 2 ;;
      --now) now="$2"; shift 2 ;;
      --out) out="$2"; shift 2 ;;
      *) echo "CTGC: unknown resolve arg $1" >&2; return 2 ;;
    esac
  done
  [[ -z "$now" || ! -f "$snap_path" ]] && return 2
  resolve_gc_eligibility "$snap_path" "$now" "$out"
}

cmd_emit_plan() {
  local buffer_path="/app/state/eligibility.buffer" out="/app/output/namespace_gc_plan.json"
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --eligibility-buffer) buffer_path="$2"; shift 2 ;;
      --out) out="$2"; shift 2 ;;
      *) echo "CTGC: unknown emit-plan arg $1" >&2; return 2 ;;
    esac
  done
  [[ ! -f "$buffer_path" ]] && return 2
  emit_gc_plan "$buffer_path" "$out"
}

main() {
  local cmd="${1:-}"
  shift || true
  case "$cmd" in
    scan-meta) cmd_scan_meta "$@" ;;
    resolve) cmd_resolve "$@" ;;
    emit-plan) cmd_emit_plan "$@" ;;
    *) echo "usage: ctrgc scan-meta|resolve|emit-plan" >&2; return 2 ;;
  esac
}

main "$@"
