from __future__ import annotations

import os
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path


ARCHIVE_MEMBERS = {
    "golden_journal.rs": "/app/crates/archecore/src/migrate/journal.rs",
    "golden_runner.rs": "/app/crates/archecore/src/migrate/runner/mod.rs",
    "golden_ledger.rs": "/app/crates/archecore/src/migrate/ledger/mod.rs",
    "golden_archetype.rs": "/app/crates/archecore/src/storage/archetype.rs",
    "golden_component.rs": "/app/crates/archecore/src/storage/component.rs",
    "golden_sparse.rs": "/app/crates/archecore/src/storage/sparse.rs",
    "golden_world.rs": "/app/crates/archecore/src/storage/world.rs",
    "golden_cache.rs": "/app/crates/archecore/src/query/cache.rs",
    "golden_planner.rs": "/app/crates/archecore/src/query/planner.rs",
    "golden_staging.rs": "/app/crates/archecore/src/staging/snapshot.rs",
    "golden_publish.rs": "/app/crates/archecore/src/export/publish.rs",
    "golden_wrap.rs": "/app/crates/archecore/src/export/wrap.rs",
}


def locate_archive() -> Path | None:
    script_dir = Path(__file__).resolve().parent
    candidates = [
        script_dir / "archecore-oracle.tar",
        Path("/task/solution/oracle/archecore-oracle.tar"),
        Path("/solution/oracle/archecore-oracle.tar"),
        Path("/oracle/solution/oracle/archecore-oracle.tar"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def main() -> int:
    if len(sys.argv) > 2:
        print("usage: install_archecore_oracle.py [archive]", file=sys.stderr)
        return 2

    archive_path = Path(sys.argv[1]) if len(sys.argv) == 2 else locate_archive()
    if archive_path is None:
        print("oracle archive not found", file=sys.stderr)
        return 1
    if not archive_path.is_file():
        print(f"oracle archive not found: {archive_path}", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory(prefix="archecore-oracle-") as tmp:
        tmp_path = Path(tmp)
        with tarfile.open(archive_path) as tar:
            tar.extractall(tmp_path)

        for member, target in ARCHIVE_MEMBERS.items():
            src = tmp_path / member
            if not src.is_file():
                print(f"oracle member missing: {member}", file=sys.stderr)
                return 1
            Path(target).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    env = {
        **os.environ,
        "PATH": f"/usr/local/cargo/bin:/usr/local/bin:{os.environ.get('PATH', '')}",
        "CARGO_NET_OFFLINE": "true",
    }
    subprocess.run(
        ["cargo", "build", "--offline", "--release", "--locked", "-p", "archectl"],
        cwd="/app",
        env=env,
        check=True,
    )
    subprocess.run(
        ["install", "-m", "0755", "/app/target/release/archectl", "/usr/local/bin/archectl"],
        env=env,
        check=True,
    )
    subprocess.run(["bash", "/app/scripts/reset-state.sh"], env=env, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
