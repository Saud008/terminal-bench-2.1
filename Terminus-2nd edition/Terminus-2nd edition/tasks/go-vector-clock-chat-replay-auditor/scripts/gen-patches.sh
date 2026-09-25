#!/usr/bin/env bash
set -euo pipefail
TASK_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$TASK_ROOT"

for f in solution/patches/*.patch solution/solve.sh solution/files/*.go; do
  [[ -f "$f" ]] && sed -i 's/\r$//' "$f"
done

python3 <<'PY'
import difflib
from pathlib import Path

TASK = Path('.')
pairs = [
    ('environment/internal/lamportmesh/merge.go', 'solution/files/lamportmesh_merge.go', 'vcreplay_lamportmesh_merge.patch'),
    ('environment/internal/modgate/precedence.go', 'solution/files/modgate_precedence.go', 'vcreplay_modgate_precedence.patch'),
    ('environment/internal/silencewin/window.go', 'solution/files/silencewin_window.go', 'vcreplay_silencewin_window.patch'),
    ('environment/internal/receiptcollapse/suppress.go', 'solution/files/receiptcollapse_suppress.go', 'vcreplay_receiptcollapse_suppress.patch'),
    ('environment/internal/deliveryproof/validate.go', 'solution/files/deliveryproof_validate.go', 'vcreplay_deliveryproof_validate.patch'),
    ('environment/internal/roombind/shard_pull.go', 'solution/files/roombind_shard_pull.go', 'vcreplay_roombind_shard_pull.patch'),
    ('environment/internal/chronicle/timeline_seal.go', 'solution/files/chronicle_timeline_seal.go', 'vcreplay_chronicle_timeline_seal.patch'),
]
out_dir = TASK / 'solution/patches'
for env_rel, sol_rel, name in pairs:
    env = (TASK / env_rel).read_text(encoding='utf-8').replace('\r\n', '\n').splitlines(keepends=True)
    sol = (TASK / sol_rel).read_text(encoding='utf-8').replace('\r\n', '\n').splitlines(keepends=True)
    app_rel = env_rel.replace('environment/', '')
    diff = difflib.unified_diff(env, sol, fromfile=f'a/{app_rel}', tofile=f'b/{app_rel}', n=3)
    (out_dir / name).write_text(''.join(diff), encoding='utf-8', newline='\n')
    print('wrote', name, (out_dir / name).stat().st_size)
PY

sed -i 's/\r$//' solution/patches/vcreplay_clockjump_detect.patch solution/patches/vcreplay_casaudit_reconcile_core.patch
