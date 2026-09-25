#!/usr/bin/env bash
set -euo pipefail

export PATH="/usr/local/cargo/bin:/usr/local/bin:${PATH}"
cd /app

SOL="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cp "${SOL}/files/scheduler.rs" /app/src/merge/scheduler.rs
cp "${SOL}/files/finalize.rs" /app/src/merge/finalize.rs
cp "${SOL}/files/norm.rs" /app/src/schema/norm.rs
cp "${SOL}/files/wal.rs" /app/src/commit/wal.rs
cp "${SOL}/files/search.rs" /app/src/export/search.rs

bash /app/scripts/verifier-rebuild.sh
bash /app/scripts/reset-state.sh

test -x /usr/local/bin/tantool
