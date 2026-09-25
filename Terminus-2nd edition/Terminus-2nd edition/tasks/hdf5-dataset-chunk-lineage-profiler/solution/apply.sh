#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

install -m 0644 "$ROOT_DIR/patches/ixwalk.rs" /app/src/s5pipe/ixwalk.rs
install -m 0644 "$ROOT_DIR/patches/amerg.rs" /app/src/s5pipe/amerg.rs
install -m 0644 "$ROOT_DIR/patches/fchain.rs" /app/src/s5pipe/fchain.rs
install -m 0644 "$ROOT_DIR/patches/btally.rs" /app/src/s5pipe/btally.rs
install -m 0644 "$ROOT_DIR/patches/oscale.rs" /app/src/s5pipe/oscale.rs
install -m 0644 "$ROOT_DIR/patches/ledger.rs" /app/src/s5pipe/ledger.rs
install -m 0644 "$ROOT_DIR/patches/emit.rs" /app/src/s5pipe/emit.rs

test -s /app/src/s5pipe/ixwalk.rs
test -s /app/src/s5pipe/amerg.rs
test -s /app/src/s5pipe/fchain.rs
test -s /app/src/s5pipe/btally.rs
test -s /app/src/s5pipe/oscale.rs
test -s /app/src/s5pipe/ledger.rs
test -s /app/src/s5pipe/emit.rs

test -f /app/src/s5pipe/ixwalk.rs
test -f /app/src/s5pipe/amerg.rs
test -f /app/src/s5pipe/fchain.rs
test -f /app/src/s5pipe/btally.rs
test -f /app/src/s5pipe/oscale.rs
test -f /app/src/s5pipe/ledger.rs
test -f /app/src/s5pipe/emit.rs

wc -c /app/src/s5pipe/ixwalk.rs >/dev/null
wc -c /app/src/s5pipe/amerg.rs >/dev/null
wc -c /app/src/s5pipe/fchain.rs >/dev/null
wc -c /app/src/s5pipe/btally.rs >/dev/null
wc -c /app/src/s5pipe/oscale.rs >/dev/null
wc -c /app/src/s5pipe/ledger.rs >/dev/null
wc -c /app/src/s5pipe/emit.rs >/dev/null
