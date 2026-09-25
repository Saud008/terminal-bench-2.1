#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
cp "${DIR}/patches/parse.sh" /app/lib/parse.sh
chmod +x /app/lib/parse.sh /app/bin/quadlet-resolver
