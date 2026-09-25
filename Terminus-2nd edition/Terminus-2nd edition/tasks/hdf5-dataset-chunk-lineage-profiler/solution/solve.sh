#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export PATH="/usr/local/cargo/bin:/opt/verifier-scripts:/app/target/release:${PATH}"

bash "${ROOT_DIR}/apply.sh"

cd /app
/usr/local/cargo/bin/cargo build --release --locked
mkdir -p /app/state /app/output
