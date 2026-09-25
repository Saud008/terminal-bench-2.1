#!/usr/bin/env bash
set -euo pipefail
cd /solution
cp files/scanstage/materialize_fleet.sh /app/internal/raidops/scanstage/materialize_fleet.sh
cp files/policies/bitmap_policy.sh /app/internal/raidops/policies/bitmap_policy.sh
cp files/policies/spare_hold_policy.sh /app/internal/raidops/policies/spare_hold_policy.sh
cp files/policies/degraded_floor_policy.sh /app/internal/raidops/policies/degraded_floor_policy.sh
cp files/policies/level_path_policy.sh /app/internal/raidops/policies/level_path_policy.sh
cp files/policies/window_fit_policy.sh /app/internal/raidops/policies/window_fit_policy.sh
cp files/ranking/criticality_rank.sh /app/internal/raidops/ranking/criticality_rank.sh
cp files/atlasstage/emit_eligibility_atlas.sh /app/internal/raidops/atlasstage/emit_eligibility_atlas.sh
bash /app/scripts/rebuild-mdreshape.sh
bash /app/scripts/reset-state.sh
/app/bin/mdreshape scan --scenario basic-reshape --run-id oracle-smoke >/dev/null
/app/bin/mdreshape compile --run-id oracle-smoke >/dev/null
test -s /app/state/reshape-ledger.json
/app/bin/mdreshape publish --run-id oracle-smoke --output /app/output/mdreshape_eligibility_atlas.json >/dev/null
test -s /app/output/mdreshape_eligibility_atlas.json
