#!/usr/bin/env bash
set -euo pipefail

export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

for src in \
  files/c41f64e930_oracle_tz_resolver.go \
  files/c41f64e930_oracle_croncalc_compute.go \
  files/c41f64e930_oracle_staging_snapshot.go \
  files/c41f64e930_oracle_lock_singleton.go \
  files/c41f64e930_oracle_lock_lease.go \
  files/c41f64e930_oracle_runtracker.go \
  files/c41f64e930_oracle_replay_runner.go \
  files/c41f64e930_oracle_replay_export.go \
  files/c41f64e930_oracle_clock.go \
  files/c41f64e930_oracle_main.go \
  files/c41f64e930_oracle_ledger_sqlite.go
do
  test -f "${ROOT_DIR}/${src}"
done

cp -f "${ROOT_DIR}/files/c41f64e930_oracle_tz_resolver.go" /app/internal/tz/resolver.go
cp -f "${ROOT_DIR}/files/c41f64e930_oracle_croncalc_compute.go" /app/internal/croncalc/compute.go
cp -f "${ROOT_DIR}/files/c41f64e930_oracle_staging_snapshot.go" /app/internal/staging/snapshot.go
cp -f "${ROOT_DIR}/files/c41f64e930_oracle_lock_singleton.go" /app/internal/lock/singleton.go
cp -f "${ROOT_DIR}/files/c41f64e930_oracle_lock_lease.go" /app/internal/lock/lease.go
cp -f "${ROOT_DIR}/files/c41f64e930_oracle_runtracker.go" /app/internal/runtracker/tracker.go
cp -f "${ROOT_DIR}/files/c41f64e930_oracle_replay_runner.go" /app/internal/replay/runner.go
cp -f "${ROOT_DIR}/files/c41f64e930_oracle_replay_export.go" /app/internal/replay/export.go
cp -f "${ROOT_DIR}/files/c41f64e930_oracle_clock.go" /app/internal/clock/clock.go
cp -f "${ROOT_DIR}/files/c41f64e930_oracle_main.go" /app/cmd/cronctl/main.go
cp -f "${ROOT_DIR}/files/c41f64e930_oracle_ledger_sqlite.go" /app/internal/ledger/sqlite.go

for dst in \
  /app/internal/tz/resolver.go \
  /app/internal/croncalc/compute.go \
  /app/internal/staging/snapshot.go \
  /app/internal/lock/singleton.go \
  /app/internal/lock/lease.go \
  /app/internal/runtracker/tracker.go \
  /app/internal/replay/runner.go \
  /app/internal/replay/export.go \
  /app/internal/clock/clock.go \
  /app/cmd/cronctl/main.go \
  /app/internal/ledger/sqlite.go
do
  test -f "${dst}"
  test -s "${dst}"
done

cd /app
go build -mod=readonly -trimpath -ldflags="-s -w" -o /usr/local/bin/cronctl ./cmd/cronctl
bash /app/scripts/reset-state.sh

test -x /usr/local/bin/cronctl
echo "gocron-cronctl-staging-replay-ledger oracle ready"
