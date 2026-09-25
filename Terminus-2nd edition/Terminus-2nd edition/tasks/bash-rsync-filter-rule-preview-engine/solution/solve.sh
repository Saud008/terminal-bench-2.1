#!/usr/bin/env bash
set -euo pipefail
cd /solution
bash apply_frontier.sh
cd /app
bash /app/scripts/rebuild-rsyncprev.sh
bash /app/scripts/reset-state.sh

/app/bin/rsyncprev ingest --tree media-sync --run-id oracle-smoke >/dev/null
/app/bin/rsyncprev compile --run-id oracle-smoke >/dev/null
test -s /app/state/filter-compiled.json
/app/bin/rsyncprev export --run-id oracle-smoke --output /app/output/rsync_filter_preview_atlas.json >/dev/null
test -s /app/output/rsync_filter_preview_atlas.json
