#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/bin:${PATH}"
/app/bin/lt-canonicalize /app/projects/demo --out /app/output/libtool-manifest.json
