#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCHES="${ROOT_DIR}/patches"
find /app/internal /app/cmd -name '*.go' -exec sed -i 's/\r$//' {} +
cp -f "${PATCHES}/chronorder_rank.go" /app/internal/chronorder/sort.go
cp -f "${PATCHES}/retryledger_track.go" /app/internal/retryledger/retry.go
cp -f "${PATCHES}/eventcache_persist.go" /app/internal/eventcache/stage.go
cp -f "${PATCHES}/dbmirror_write.go" /app/internal/dbmirror/export.go
# Surgical firegate lane edits (avoid whole-file rewrite).
python3 - <<'PY'
from pathlib import Path
path = Path("/app/internal/firegate/pending.go")
text = path.read_text(encoding="utf-8")
text = text.replace(
    "func (l *Lane) Cancel(timerID string) {\n}",
    "func (l *Lane) Cancel(timerID string) {\n\tdelete(l.pending, timerID)\n}",
)
old_fire = (
    "func (l *Lane) Fire(timerID string, ts int64) {\n"
    "\t_ = ts\n"
    "\tl.fired[timerID] = true\n"
    "}"
)
new_fire = (
    "func (l *Lane) Fire(timerID string, ts int64) {\n"
    "\t_ = ts\n"
    "\tl.fired[timerID] = true\n"
    "\tdelete(l.pending, timerID)\n"
    "}"
)
if old_fire not in text:
    raise SystemExit("firegate Fire baseline not found")
text = text.replace(old_fire, new_fire, 1)
path.write_text(text, encoding="utf-8")
PY
sed -i 's/cur.CompactionSeal = cur.CompactionSeal/cur.CompactionSeal = 1 + canCount/' /app/internal/genfold/summarize.go
sed -i 's/return true/return seal.CompactionSeal > 0/' /app/internal/replayledger/inspect.go
python3 - <<'PY'
from pathlib import Path
need = {
    Path("/app/internal/chronorder/sort.go"): "EventID",
    Path("/app/internal/retryledger/retry.go"): "attempts = map[string]int{}",
    Path("/app/internal/firegate/pending.go"): "delete(l.pending",
    Path("/app/internal/genfold/summarize.go"): "1 + canCount",
    Path("/app/internal/eventcache/stage.go"): "max_run_generation",
    Path("/app/internal/dbmirror/export.go"): "RunGeneration",
    Path("/app/internal/replayledger/inspect.go"): "CompactionSeal > 0",
}
missing = [f"{p}: {n}" for p, n in need.items() if n not in p.read_text(encoding="utf-8")]
if missing:
    raise SystemExit("oracle incomplete: " + "; ".join(missing))
PY
