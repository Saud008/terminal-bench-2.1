#!/usr/bin/env bash
set -euo pipefail

TASK="/mnt/d/Terminus-2nd edition/Terminus-2nd edition/tasks/hitbox-hurtbox-frame-alignment-replay-repair"
ENV="$TASK/environment"
PATCH="$TASK/tests/patches"
SOL="$TASK/solution"
CORE="$ENV/crates/hitbox-core/src"

for m in frame interpolate hurtbox collision export ledger; do
  cp -f "$CORE/$m.rs" "$PATCH/broken_$m.rs"
  cp -f "$SOL/golden_$m.rs" "$PATCH/golden_$m.rs"
done

cd "$ENV"
cargo generate-lockfile
cargo build --release -p hitreplay
