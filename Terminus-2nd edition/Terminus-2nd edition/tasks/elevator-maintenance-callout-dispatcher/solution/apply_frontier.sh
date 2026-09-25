#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FILES_DIR="${ROOT_DIR}/files"

sed -i 's/f.SeverityBase\*100 + urgency/f.SeverityBase*100 + f.TrappedPassengers*50 + urgency/' /app/internal/faultpriority/score.go
sed -i 's/ORDER BY tier/ORDER BY tier_rank DESC/' /app/internal/slahorizon/tier.go
cp "${FILES_DIR}/frontier_bind_skillgate.go" /app/internal/skillgate/match.go
cp "${FILES_DIR}/frontier_bind_windowfit.go" /app/internal/windowfit/window.go
cp "${FILES_DIR}/frontier_bind_rosterbind.go" /app/internal/rosterbind/plan.go
cp "${FILES_DIR}/frontier_emit_calloutpublish.go" /app/internal/calloutpublish/publish.go

find /app/internal /app/cmd -name '*.go' -exec sed -i 's/\r$//' {} +
