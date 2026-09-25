#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCHES="${ROOT_DIR}/patches"
find /app/internal /app/cmd -name '*.go' -exec sed -i 's/\r$//' {} +
cp -f "${PATCHES}/mqttsess_wildcard_topic.go" /app/internal/topicmatch/wildcard.go
cp -f "${PATCHES}/mqttsess_retained_store.go" /app/internal/retainstore/retained.go
cp -f "${PATCHES}/mqttsess_qos_inflight.go" /app/internal/qosledger/inflight.go
cp -f "${PATCHES}/mqttsess_session_expiry.go" /app/internal/sessionexp/expiry.go
cp -f "${PATCHES}/mqttsess_atlas_emit.go" /app/internal/atlasemit/export.go
sed -i 's/cur.CuratorSeal = cur.CuratorSeal$/cur.CuratorSeal = cur.CuratorSeal + 1/' /app/internal/curatormux/reconcile.go
python3 - <<'PY'
from pathlib import Path
need = {
    Path("/app/internal/topicmatch/wildcard.go"): "fi == len(fParts)-1",
    Path("/app/internal/retainstore/retained.go"): 'ev.Payload == ""',
    Path("/app/internal/qosledger/inflight.go"): "return false",
    Path("/app/internal/sessionexp/expiry.go"): "TB3_SESSION_EXPIRY_MS",
    Path("/app/internal/curatormux/reconcile.go"): "CuratorSeal + 1",
    Path("/app/internal/atlasemit/export.go"): "stableReplayDigest",
}
missing = [f"{p}: {n}" for p, n in need.items() if n not in p.read_text(encoding="utf-8")]
if missing:
    raise SystemExit("oracle incomplete: " + "; ".join(missing))
PY
