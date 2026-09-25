#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

patch -p1 -d /app < patches/parse__parse_wg_conf.sh.patch
patch -p1 -d /app < patches/cidr__cidr_overlap.sh.patch
patch -p1 -d /app < patches/endpoint__endpoint_rank.sh.patch
patch -p1 -d /app < patches/routes__route_conflict.sh.patch
patch -p1 -d /app < patches/policy__disabled_peer.sh.patch
patch -p1 -d /app < patches/workspace__workspace_fingerprint.sh.patch
patch -p1 -d /app < patches/analyze__analyze_run.sh.patch
patch -p1 -d /app < patches/export__export_atlas.sh.patch

bash /app/scripts/rebuild-wgpatlas.sh
bash /app/scripts/reset-state.sh

/app/bin/wgpatlas ingest --site coastal-mesh --run-id oracle-smoke >/dev/null
/app/bin/wgpatlas analyze --run-id oracle-smoke >/dev/null
test -s /app/state/wgpatlas-workspace.json
/app/bin/wgpatlas export --run-id oracle-smoke --output /app/output/oracle-smoke.json >/dev/null
test -s /app/output/oracle-smoke.json
