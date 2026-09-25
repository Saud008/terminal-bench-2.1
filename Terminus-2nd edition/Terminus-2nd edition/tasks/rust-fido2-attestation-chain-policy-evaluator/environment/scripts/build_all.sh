#!/usr/bin/env bash
set -euo pipefail
cd /app
/usr/local/cargo/bin/cargo build --release --locked
install -m 0755 /app/target/release/fido2eval /app/bin/fido2eval
