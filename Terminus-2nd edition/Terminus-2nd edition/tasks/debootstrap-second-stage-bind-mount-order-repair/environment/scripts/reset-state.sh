#!/usr/bin/env bash
set -euo pipefail
rm -rf /app/output/* /app/state/mount-snapshots/* /app/state/mount-gate/* /app/state/stage2-staging/*
rm -f /app/state/stage2-ledger.json
mkdir -p /app/output /app/state/mount-snapshots /app/state/mount-gate /app/state/stage2-staging
unset S2_COMMITTED 2>/dev/null || true
if [ -d /opt/fixture-seed/rootfs ]; then
  rm -rf /app/fixtures/rootfs
  mkdir -p /app/fixtures
  cp -a /opt/fixture-seed/rootfs /app/fixtures/rootfs
fi
