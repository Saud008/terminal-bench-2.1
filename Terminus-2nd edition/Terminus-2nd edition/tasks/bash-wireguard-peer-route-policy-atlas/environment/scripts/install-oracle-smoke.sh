#!/usr/bin/env bash
set -euo pipefail
if [[ ! -d /solution/files ]]; then
  echo "mount /solution" >&2
  exit 1
fi
for rel in parse/parse_wg_conf.sh cidr/cidr_overlap.sh endpoint/endpoint_rank.sh routes/route_conflict.sh policy/disabled_peer.sh workspace/workspace_fingerprint.sh analyze/analyze_run.sh export/export_atlas.sh; do
  cp "/solution/files/${rel}" "/app/internal/wgpa91/${rel}"
  chmod +x "/app/internal/wgpa91/${rel}"
done
bash /app/scripts/rebuild-wgpatlas.sh
bash /app/scripts/reset-state.sh
/app/bin/wgpatlas ingest --site coastal-mesh --run-id oracle-smoke
/app/bin/wgpatlas analyze --run-id oracle-smoke
/app/bin/wgpatlas export --run-id oracle-smoke --output /app/output/oracle-smoke.json
test -s /app/output/oracle-smoke.json
echo ORACLE_OK
