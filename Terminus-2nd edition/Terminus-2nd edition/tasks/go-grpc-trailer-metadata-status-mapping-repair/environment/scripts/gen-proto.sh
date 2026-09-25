#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"
protoc \
  --go_out=. --go_opt=module=faultserver \
  --go-grpc_out=. --go-grpc_opt=module=faultserver \
  proto/fault.proto
