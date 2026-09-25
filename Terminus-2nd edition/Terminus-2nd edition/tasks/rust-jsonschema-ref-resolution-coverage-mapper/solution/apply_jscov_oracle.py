#!/usr/bin/env python3
"""Build jscovmap after patches and run trace/publish once."""
from __future__ import annotations

import subprocess
from pathlib import Path

ENV = Path("/app/environment")
BIN = ENV / "tools" / "jscovmap" / "jscovmap"


def main() -> None:
    built = ENV / "target" / "release" / "jscovmap"
    BIN.parent.mkdir(parents=True, exist_ok=True)
    BIN.write_bytes(built.read_bytes())
    BIN.chmod(0o755)

    schema = ENV / "fixtures" / "schemas"
    examples = ENV / "fixtures" / "validation_examples.jsonl"
    ref_edges = Path("/app/state/ref_edges.jsonl")
    coverage = Path("/app/state/example_coverage.jsonl")
    report = Path("/app/output/schema_coverage_report.json")
    graph = Path("/app/output/ref_graph.json")
    ref_edges.parent.mkdir(parents=True, exist_ok=True)
    report.parent.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [
            str(BIN),
            "trace",
            "--schema-dir",
            str(schema),
            "--examples",
            str(examples),
            "--ref-edges",
            str(ref_edges),
            "--coverage",
            str(coverage),
        ],
        check=True,
    )
    subprocess.run(
        [
            str(BIN),
            "publish",
            "--ref-edges",
            str(ref_edges),
            "--coverage",
            str(coverage),
            "--report",
            str(report),
            "--graph",
            str(graph),
        ],
        check=True,
    )


if __name__ == "__main__":
    main()
