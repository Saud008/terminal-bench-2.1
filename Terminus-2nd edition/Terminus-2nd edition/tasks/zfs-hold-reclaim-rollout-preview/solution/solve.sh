#!/usr/bin/env bash
set -euo pipefail
cd /solution
cp files/load/load_inventory.sh /app/internal/zfsroll/load/load_inventory.sh
cp files/gates/hold_gate.sh /app/internal/zfsroll/gates/hold_gate.sh
cp files/gates/clone_gate.sh /app/internal/zfsroll/gates/clone_gate.sh
cp files/gates/bookmark_gate.sh /app/internal/zfsroll/gates/bookmark_gate.sh
cp files/gates/pool_floor.sh /app/internal/zfsroll/gates/pool_floor.sh
cp files/order/reclaim_sort.sh /app/internal/zfsroll/order/reclaim_sort.sh
cp files/publish/publish_atlas.sh /app/internal/zfsroll/publish/publish_atlas.sh
bash /app/scripts/rebuild-zfshold.sh
bash /app/scripts/reset-state.sh
/app/bin/zfshold load --scenario basic-hold --run-id oracle-smoke >/dev/null
/app/bin/zfshold compile --run-id oracle-smoke >/dev/null
test -s /app/state/reclaim-ledger.json
/app/bin/zfshold publish --run-id oracle-smoke --output /app/output/zfs_reclaim_rollout_atlas.json >/dev/null
test -s /app/output/zfs_reclaim_rollout_atlas.json
