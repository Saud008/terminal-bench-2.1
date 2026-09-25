#!/usr/bin/env bash
set -euo pipefail
cd /app
cargo build --release --locked
cp /app/target/release/fsplatlas /app/bin/fsplatlas
