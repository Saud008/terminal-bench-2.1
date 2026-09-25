#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_ROOT="/app"
cp -f "${SCRIPT_DIR}/golden_flags.go" "${APP_ROOT}/internal/maildir/flags.go"
cp -f "${SCRIPT_DIR}/golden_precedence.go" "${APP_ROOT}/internal/tags/precedence.go"
cp -f "${SCRIPT_DIR}/golden_dedupe.go" "${APP_ROOT}/internal/thread/dedupe.go"
cp -f "${SCRIPT_DIR}/golden_snapshot.go" "${APP_ROOT}/internal/staging/snapshot.go"
cp -f "${SCRIPT_DIR}/golden_writer.go" "${APP_ROOT}/internal/staging/writer.go"
cp -f "${SCRIPT_DIR}/golden_publish.go" "${APP_ROOT}/internal/export/publish.go"
cp -f "${SCRIPT_DIR}/golden_engine.go" "${APP_ROOT}/internal/syncengine/engine.go"
bash /app/scripts/verifier-rebuild.sh
bash /app/scripts/reset-state.sh
mailsync sync --maildir /app/fixtures/maildir --db /app/data/mailsync.db --report /app/output/mail-sync-report.json
