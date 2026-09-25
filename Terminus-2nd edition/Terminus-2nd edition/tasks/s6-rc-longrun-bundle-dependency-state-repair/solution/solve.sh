#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
cp "${DIR}/patches/dag.sh" /app/lib/dag.sh
cp "${DIR}/patches/ready.sh" /app/lib/ready.sh
cp "${DIR}/patches/apply.sh" /app/lib/apply.sh
cp "${DIR}/patches/export.sh" /app/lib/export.sh
chmod +x /app/lib/dag.sh /app/lib/ready.sh /app/lib/apply.sh /app/lib/export.sh /app/bin/s6-bundle-resolver
