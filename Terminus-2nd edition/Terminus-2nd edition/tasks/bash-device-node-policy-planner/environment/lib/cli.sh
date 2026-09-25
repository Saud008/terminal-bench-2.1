#!/usr/bin/env bash
# CLI dispatch for udev-policy-planner verbs
set -euo pipefail

UDEV_LIB="${UDEV_LIB:-/app/lib}"
# shellcheck source=common.sh
source "${UDEV_LIB}/common.sh"
# shellcheck source=ruleio/rule_loader.sh
source "${UDEV_LIB}/ruleio/rule_loader.sh"
# shellcheck source=bindio/match_engine.sh
source "${UDEV_LIB}/bindio/match_engine.sh"
# shellcheck source=snapio/snap_writer.sh
source "${UDEV_LIB}/snapio/snap_writer.sh"
# shellcheck source=planio/device_rows.sh
source "${UDEV_LIB}/planio/device_rows.sh"
# shellcheck source=bindio/bind_tsv.sh
source "${UDEV_LIB}/bindio/bind_tsv.sh"

cmd_ingest() {
  local rules_dir="" devices="" modalias="" out="/app/state/rule_staging.json"
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --rules-dir) rules_dir="$2"; shift 2 ;;
      --devices) devices="$2"; shift 2 ;;
      --modalias) modalias="$2"; shift 2 ;;
      --out) out="$2"; shift 2 ;;
      *) echo "UDEVPLAN: unknown ingest arg $1" >&2; return 2 ;;
    esac
  done
  [[ -z "$rules_dir" || -z "$devices" || -z "$modalias" ]] && return 2
  local rules devices_json catalog edges
  rules="$(load_ordered_rules "$rules_dir")"
  devices_json="$(cat "$devices")"
  catalog="$(load_modalias_catalog "$modalias")"
  edges="$(build_match_edges "$rules" "$devices_json" "$catalog")"
  write_staging_snapshot "$out" "$rules" "$devices_json" "$edges"
}

cmd_export() {
  local staging="/app/state/rule_staging.json" policy="" out="/app/output/device_plan.json"
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --staging) staging="$2"; shift 2 ;;
      --policy) policy="$2"; shift 2 ;;
      --out) out="$2"; shift 2 ;;
      *) echo "UDEVPLAN: unknown export arg $1" >&2; return 2 ;;
    esac
  done
  [[ -z "$policy" || ! -f "$staging" ]] && return 2
  export_device_plan "$staging" "$policy" "$out"
}

main() {
  local cmd="${1:-}"
  shift || true
  case "$cmd" in
    ingest) cmd_ingest "$@" ;;
    export) cmd_export "$@" ;;
    *) echo "usage: udev-policy-planner ingest|export" >&2; return 2 ;;
  esac
}

main "$@"
