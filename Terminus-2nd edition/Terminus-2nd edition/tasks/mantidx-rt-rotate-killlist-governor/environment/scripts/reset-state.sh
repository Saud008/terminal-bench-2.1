#!/usr/bin/env bash
set -euo pipefail
rm -f /app/data/mantidx.db
rm -f /app/state/rotate-meta.json /app/state/ram-segments.json /app/state/killlist.json
rm -f /app/state/binlog-checkpoint.json /app/state/rotate-audit.json
rm -f /app/state/merge-ram-audit.json /app/state/attribute-audit.json
rm -f /app/state/killlist-merge-audit.json
rm -f /app/state/search-report.json
mkdir -p /app/data /app/state /app/output
