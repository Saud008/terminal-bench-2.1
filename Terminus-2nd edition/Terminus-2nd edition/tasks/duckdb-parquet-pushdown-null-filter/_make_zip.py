import zipfile
from pathlib import Path

repo = Path(r"/mnt/d/Terminus-2nd edition/Terminus-2nd edition")
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
