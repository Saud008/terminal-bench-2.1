#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

make -f /dev/null pamtrace-offline 2>/dev/null || true

patch -p1 -d /app < files/patches/pamtrace-expand-includes.patch
patch -p1 -d /app < files/patches/pamtrace-stack-walker.patch
patch -p1 -d /app < files/patches/pamtrace-group-gate.patch
patch -p1 -d /app < files/patches/pamtrace-ledger-build.patch
patch -p1 -d /app < files/patches/pamtrace-emit-trace.patch

bash /app/scripts/rebuild-pamtrace.sh
bash /app/scripts/reset-state.sh

/app/bin/pamtrace load --scenario sshd-basic --run-id oracle-smoke >/dev/null
/app/bin/pamtrace compile --run-id oracle-smoke >/dev/null
test -s /app/state/pamtrace-ledger.json
/app/bin/pamtrace emit --run-id oracle-smoke --service sshd --subject alice --output /app/output/oracle-smoke.json >/dev/null
test -s /app/output/oracle-smoke.json
