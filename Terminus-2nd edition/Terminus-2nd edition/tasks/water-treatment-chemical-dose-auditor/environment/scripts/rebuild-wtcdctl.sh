#!/usr/bin/env bash
set -euo pipefail
cd /app
python3 /app/fixtures/build_fixtures.py --seed 4821 --out-dir /app/fixtures/plant_shifts
/usr/local/cargo/bin/cargo build --release
install -m 0755 /app/target/release/wtcdctl /app/bin/wtcdctl
