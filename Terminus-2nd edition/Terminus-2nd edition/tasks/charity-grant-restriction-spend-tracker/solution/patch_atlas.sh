#!/usr/bin/env bash
set -euo pipefail
cp "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/files/oracle_atlas_publish.go" /app/internal/atlaswriter/atlas_publish.go
