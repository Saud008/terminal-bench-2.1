#!/usr/bin/env bash
set -euo pipefail
STATE="/app/state"
OUTPUT="/app/output"
rm -f "${STATE}/staging-snapshot.json" "${STATE}/staging-manifest.json" "${STATE}/notify.done" "${STATE}/export-ready" "${STATE}/work-staging.json" "${STATE}/events.json" "${STATE}/event-lines.jsonl"
rm -f "${OUTPUT}/vrrp-state.json" "${OUTPUT}/config-report.json"
mkdir -p "${STATE}" "${OUTPUT}"
