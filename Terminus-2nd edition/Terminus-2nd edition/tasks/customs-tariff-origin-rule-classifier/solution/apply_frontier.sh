#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FILES_DIR="${ROOT_DIR}/files"

cp "${FILES_DIR}/oracle_normalize.go" /app/internal/codify/digits.go
cp "${FILES_DIR}/oracle_rvc.go" /app/internal/concession/sharemath.go
cp "${FILES_DIR}/oracle_cert.go" /app/internal/concession/credential.go
cp "${FILES_DIR}/oracle_precedence.go" /app/internal/concession/ranker.go
cp "${FILES_DIR}/oracle_emit.go" /app/internal/classout/publish.go

find /app/internal /app/cmd -name '*.go' -exec sed -i 's/\r$//' {} +
