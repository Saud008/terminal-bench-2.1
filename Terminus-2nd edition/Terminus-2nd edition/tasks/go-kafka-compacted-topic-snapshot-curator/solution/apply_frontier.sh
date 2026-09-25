#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

find /app/internal /app/cmd -name '*.go' -exec sed -i 's/\r$//' {} +

cp "${ROOT_DIR}/patches/patch_segpull_segment_pull.go" /app/internal/segpull/cold_pull.go
cp "${ROOT_DIR}/patches/patch_keysout_emit_rows.go" /app/internal/keysout/stream_mux.go
cp "${ROOT_DIR}/patches/patch_latestmap_build_rows.go" /app/internal/latestmap/snap_table.go
cp "${ROOT_DIR}/patches/patch_partitionorder_sort.go" /app/internal/partitionorder/sort.go
cp "${ROOT_DIR}/patches/patch_offsetdup_dedupe.go" /app/internal/offsetdup/dedupe.go
cp "${ROOT_DIR}/patches/patch_tombwin_retention.go" /app/internal/tombwin/floor_mux.go
cp "${ROOT_DIR}/patches/patch_keyfold_fold_codec.go" /app/internal/keyfold/fold_codec.go

# sealpass: bump curator_seal on audit (no full-file patch shipped)
python3 - <<'PY'
from pathlib import Path
path = Path("/app/internal/sealpass/gate_mux.go")
text = path.read_text(encoding="utf-8")
old = "gen.CuratorSeal = gen.CuratorSeal"
new = "gen.CuratorSeal = gen.CuratorSeal + 1"
if old not in text:
    raise SystemExit("seal bump assignment not found")
if new not in text:
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

# Post-apply sanity checks (non-boilerplate oracle material).
python3 - <<'PY'
from pathlib import Path

checks = {
    Path("/app/internal/segpull/cold_pull.go"): "NumericSegSort(segNames)",
    Path("/app/internal/keysout/stream_mux.go"): "CanonicalKey < rows[j].CanonicalKey",
    Path("/app/internal/latestmap/snap_table.go"): "deleted := rec.IsTombstone",
    Path("/app/internal/sealpass/gate_mux.go"): "CuratorSeal + 1",
    Path("/app/internal/keyfold/fold_codec.go"): "norm.NFC",
    Path("/app/internal/offsetdup/dedupe.go"): "TimestampMs",
    Path("/app/internal/tombwin/floor_mux.go"): "TB3_TOMB_RETENTION_MS",
    Path("/app/internal/partitionorder/sort.go"): "out[i].Offset < out[j].Offset",
}
extra_checks = {
    Path("/app/internal/keysout/stream_mux.go"): ["writeSnapshot", "writeLineage"],
    Path("/app/internal/sealpass/gate_mux.go"): ["analyze", "writeFindings"],
}
missing = []
for path, needle in checks.items():
    body = path.read_text(encoding="utf-8")
    if needle not in body:
        missing.append(f"{path}: {needle}")
for path, symbols in extra_checks.items():
    body = path.read_text(encoding="utf-8")
    for sym in symbols:
        if sym not in body:
            missing.append(f"{path}: {sym}")
if missing:
    raise SystemExit("frontier incomplete: " + "; ".join(missing))
PY
