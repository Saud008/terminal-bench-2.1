#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
patch -p0 -d /app < files/patches/pairing_gate.patch
patch -p0 -d /app < files/patches/resume_clear.patch
patch -p0 -d /app < files/patches/gatt_identity.patch
patch -p0 -d /app < files/patches/battery_debounce.patch
patch -p0 -d /app < files/patches/pipeline.patch
patch -p0 -d /app < files/patches/bundle_emit.patch
cd /app
make install-bondattest
bash /app/scripts/rebuild-bondattest.sh
bash /app/scripts/reset-state.sh
CFG=/app/config/bondattest.json
TRACE=/app/fixtures/traces/mixed-fleet-core.trace.jsonl
MID=/app/state/bondattest-midstate.json
OUT=/app/output/bond-reconnect-attestation.json
/usr/local/bin/bondattest absorb --trace "$TRACE" --config "$CFG" --seed oracle-seed --midstate "$MID"
/usr/local/bin/bondattest seal --midstate "$MID" --bundle "$OUT"
