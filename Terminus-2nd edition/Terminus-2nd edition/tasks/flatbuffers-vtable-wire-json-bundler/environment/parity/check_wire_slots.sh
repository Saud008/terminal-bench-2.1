#!/usr/bin/env bash
# Verifier-only wire slot sanity check (not on fbdecode hot path).
set -euo pipefail
test -f /app/schema/scene.fbs
test -d /app/fixtures/buffers
