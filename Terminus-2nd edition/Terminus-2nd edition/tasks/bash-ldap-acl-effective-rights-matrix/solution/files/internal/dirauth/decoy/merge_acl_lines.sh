#!/usr/bin/env bash
# Historical ACL merge helper — not on ingest/export hot path
set -euo pipefail
sort -r "$@"
