#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
patch -p0 -d /app < files/diffs/collect_fleet_snapshot.patch
patch -p0 -d /app < files/diffs/pairing_drift_gate.patch
patch -p0 -d /app < files/diffs/resume_slot_gate.patch
patch -p0 -d /app < files/diffs/power_sequence_gate.patch
patch -p0 -d /app < files/diffs/reconnect_storm_gate.patch
patch -p0 -d /app < files/diffs/gatt_service_catalog.patch
patch -p0 -d /app < files/diffs/rank_by_criticality.patch
patch -p0 -d /app < files/diffs/publish_rollout_atlas.patch
cd /app
bash /app/scripts/rebuild-hciroll.sh
bash /app/scripts/reset-state.sh
/app/bin/hciroll scan --scenario basic-reconnect --run-id oracle-smoke >/dev/null
/app/bin/hciroll compile --run-id oracle-smoke >/dev/null
test -s /app/state/reconnect-ledger.json
/app/bin/hciroll publish --run-id oracle-smoke --output /app/output/hci_reconnect_rollout_atlas.json >/dev/null
test -s /app/output/hci_reconnect_rollout_atlas.json
