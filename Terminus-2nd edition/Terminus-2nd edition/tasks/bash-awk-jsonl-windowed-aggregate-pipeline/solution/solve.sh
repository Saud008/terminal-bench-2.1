#!/usr/bin/env bash
set -euo pipefail

cp /solution/golden_ingest.awk /app/lib/ingest.awk
cp /solution/golden_bucket.awk /app/lib/bucket.awk
cp /solution/golden_export.awk /app/lib/export.awk
cp /solution/golden_agg_run.sh /app/bin/agg-run
sed -i 's/\r$//' /app/lib/ingest.awk /app/lib/bucket.awk /app/lib/export.awk /app/bin/agg-run
chmod +x /app/bin/agg-run
install -m 0755 /app/bin/agg-run /usr/local/bin/agg-run

bash /app/scripts/reset-state.sh
/app/bin/agg-run \
  --stream-dir /app/fixtures/streams \
  --config /app/config/window.json \
  --output /app/output/aggregate-report.json
