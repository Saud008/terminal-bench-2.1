#!/usr/bin/env bash
set -euo pipefail
cd /app/environment
CARGO_TARGET_DIR=/app/environment/target cargo build --release
