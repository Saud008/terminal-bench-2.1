#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
cp "${DIR}/patches/parse.sh" /app/lib/parse.sh
cp "${DIR}/patches/dag.sh" /app/lib/dag.sh
chmod +x /app/lib/*.sh /app/bin/quadlet-resolver
