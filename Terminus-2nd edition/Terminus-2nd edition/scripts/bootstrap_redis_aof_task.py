#!/usr/bin/env python3
"""Bootstrap redis-aof-rewrite-barrier-export task tree."""
from __future__ import annotations

import json
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "tasks" / "redis-aof-rewrite-barrier-export"
ENV = ROOT / "environment"
TESTS = ROOT / "tests"
SOL = ROOT / "solution" / "patches"
GOLDEN = TESTS / "verifier-golden"
HIDDEN = TESTS / "verifier-fixtures" / "suites"


def w(rel: str, content: str) -> None:
    p = ROOT / rel if not str(rel).startswith("environment") else ENV / rel.removeprefix("environment/")
    if rel.startswith("tests/"):
        p = ROOT / rel
    elif rel.startswith("solution/"):
        p = ROOT / rel
    else:
        p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(content).lstrip("\n"), encoding="utf-8")


# --- metadata ---
w("task.toml", """
version = "2.0"

[metadata]
author_name = "anonymous"
author_email = "anonymous"
difficulty = "hard"
category = "data-processing"
subcategories = []
number_of_milestones = 0
codebase_size = "small"
languages = ["go", "bash"]
tags = ["redis", "aof", "multi-exec", "checkpoint", "manifest", "go-cli"]
expert_time_estimate_min = 180
junior_time_estimate_min = 360

[agent]
timeout_sec = 1800

[verifier]
timeout_sec = 900

[environment]
allow_internet = false
workdir = "/app"
build_timeout_sec = 900.0
cpus = 2
memory_mb = 4096
storage_mb = 10240
""")

w("instruction.md", """
The aofreplay CLI under /app/cmd/aofreplay simulates Redis AOF rewrite replay with preamble keyspace, MULTI and EXEC batching, and checkpoint barriers. Each replay run writes /app/state/aof-staging.json and publish emits /app/output/aof-export-report.json.

Implement the modules listed in /app/docs/module-api.md so replay loads preamble keys, applies ops through txn batching per /app/docs/aof-ops-format.md and /app/docs/multi-exec-semantics.md, enforces checkpoint max_seq per /app/docs/checkpoint-barrier.md, writes staging per /app/docs/staging-schema.md, and publish reads staging only per /app/docs/export-schema.md.

Example:

aofreplay replay --suite /app/fixtures/suites/001-preamble-set --staging /app/state/aof-staging.json

aofreplay publish --staging /app/state/aof-staging.json --output /app/output/aof-export-report.json

After Go changes rebuild aofreplay before grading. Do not edit /app/docs/, /app/fixtures/, or files under /tests/.
""")

print("bootstrap: wrote metadata")
