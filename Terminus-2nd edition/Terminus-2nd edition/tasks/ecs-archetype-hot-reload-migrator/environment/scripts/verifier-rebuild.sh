#!/usr/bin/env bash
set -euo pipefail

cd /app
cargo build --locked -p ecs-migrate
install -m 0755 target/debug/ecs-migrate /usr/local/bin/ecs-migrate
