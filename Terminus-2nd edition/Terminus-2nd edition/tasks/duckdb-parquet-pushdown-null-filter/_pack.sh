#!/usr/bin/env bash
set -euo pipefail
REPO="/mnt/d/Terminus-2nd edition/Terminus-2nd edition"
TASK="$REPO/tasks/duckdb-parquet-pushdown-null-filter"
python3 -c "
from pathlib import Path
root = Path('$TASK')
for p in root.rglob('*.sh'):
    p.write_bytes(p.read_bytes().replace(b'\r\n', b'\n').replace(b'\r', b'\n'))
"
STAGE=/tmp/duckdb-pack-test
rm -rf "$STAGE"
cp -a "$TASK" "$STAGE"
cd "$STAGE"
docker build -t duckdb-pack-test environment/
docker run --rm \
  -v "$STAGE/solution:/solution:ro" \
  -v "$STAGE/tests:/tests:ro" \
  duckdb-pack-test \
  bash -c 'bash /solution/solve.sh && bash /tests/test.sh; echo REWARD=$(cat /logs/verifier/reward.txt)'
mkdir -p "$REPO/tasksubmit"
rm -f "$REPO/tasksubmit/duckdb-parquet-pushdown-null-filter.zip"
cd "$TASK"
zip -r "$REPO/tasksubmit/duckdb-parquet-pushdown-null-filter.zip" instruction.md task.toml environment tests solution
ls -la "$REPO/tasksubmit/duckdb-parquet-pushdown-null-filter.zip"
