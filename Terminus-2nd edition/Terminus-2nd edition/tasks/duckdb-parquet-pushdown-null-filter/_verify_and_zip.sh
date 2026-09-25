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
STAGE=/tmp/duckdb-pack-final
rm -rf "$STAGE"
cp -a "$TASK" "$STAGE"
cd "$STAGE"
docker build -t duckdb-pack-final environment/
docker run --rm \
  -v "$STAGE/solution:/solution:ro" \
  -v "$STAGE/tests:/tests:ro" \
  duckdb-pack-final \
  bash -c 'bash /solution/solve.sh && bash /tests/test.sh; echo REWARD=$(cat /logs/verifier/reward.txt)'
python3 - <<'PY'
import zipfile
from pathlib import Path
repo = Path("/mnt/d/Terminus-2nd edition/Terminus-2nd edition")
task = repo / "tasks/duckdb-parquet-pushdown-null-filter"
out = repo / "tasksubmit/duckdb-parquet-pushdown-null-filter.zip"
out.parent.mkdir(parents=True, exist_ok=True)

def add_dir(zf, base: Path, arc_prefix: str) -> None:
    for path in sorted(base.rglob("*")):
        if path.is_file():
            rel = path.relative_to(base).as_posix()
            zf.write(path, f"{arc_prefix}/{rel}")

with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
    zf.write(task / "instruction.md", "instruction.md")
    zf.write(task / "task.toml", "task.toml")
    add_dir(zf, task / "environment", "environment")
    add_dir(zf, task / "tests", "tests")
    add_dir(zf, task / "solution", "solution")
print(out)
print("entries", len(zipfile.ZipFile(out).namelist()))
PY
