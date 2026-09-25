#!/usr/bin/env bash
set -euo pipefail
cd /solution
patch -p1 -d /app < patches/w0__wrap_stage.sh.patch
patch -p1 -d /app < patches/w1__gate_pin.sh.patch
patch -p1 -d /app < patches/w2__gate_rect.sh.patch
patch -p1 -d /app < patches/w3__gate_lag.sh.patch
patch -p1 -d /app < patches/w5__rank_mix.sh.patch
patch -p1 -d /app < patches/w6__tally_stage.sh.patch
patch -p1 -d /app < patches/w7__emit_stage.sh.patch
bash /app/scripts/rebuild-geoboxplay.sh
bash /app/scripts/reset-state.sh
/app/bin/geoboxplay load-level --level paris-core --run-id oracle-smoke >/dev/null
/app/bin/geoboxplay score-round --run-id oracle-smoke >/dev/null
test -s /app/state/round-score.json
/app/bin/geoboxplay seal-atlas --run-id oracle-smoke --output /app/output/geo-filter-playtest-atlas.json >/dev/null
test -s /app/output/geo-filter-playtest-atlas.json
