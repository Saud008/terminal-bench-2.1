"""Build avsccompat and run ingest/export after patches are applied."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

APP = Path("/app")
ENV = APP / "environment"
BIN = ENV / "tools" / "avsccompat" / "avsccompat"


def run(cmd: list[str], *, cwd: Path | None = None) -> None:
    subprocess.run(cmd, check=True, cwd=cwd)


def main() -> int:
    target = ENV / "target"
    if target.exists():
        import shutil

        shutil.rmtree(target)
    run(["cargo", "build", "--release", "-p", "avsccompat"], cwd=ENV)
    built = ENV / "target" / "release" / "avsccompat"
    BIN.parent.mkdir(parents=True, exist_ok=True)
    BIN.write_bytes(built.read_bytes())
    BIN.chmod(0o755)
    schema = Path(__import__("os").environ.get("TB3_SCHEMA_DIR", str(ENV / "fixtures" / "schemas")))
    pairs = Path(__import__("os").environ.get("TB3_PAIRS_FILE", str(ENV / "fixtures" / "schema_pairs.jsonl")))
    staging = APP / "state" / "schema_pair_ledger.jsonl"
    report = APP / "output" / "avro_migration_report.json"
    staging.parent.mkdir(parents=True, exist_ok=True)
    report.parent.mkdir(parents=True, exist_ok=True)
    if staging.exists():
        staging.unlink()
    if report.exists():
        report.unlink()
    run([str(BIN), "ingest", "--schema-dir", str(schema), "--pairs", str(pairs), "--staging", str(staging)])
    run([str(BIN), "export", "--staging", str(staging), "--out", str(report)])
    return 0


if __name__ == "__main__":
    sys.exit(main())
