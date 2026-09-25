#!/usr/bin/env bash
set -euo pipefail
# Catalog helpers — not on ingest hot path
APP_ROOT="${APP_ROOT:-/app}"
cat "${APP_ROOT}/fixtures/catalog.json"
