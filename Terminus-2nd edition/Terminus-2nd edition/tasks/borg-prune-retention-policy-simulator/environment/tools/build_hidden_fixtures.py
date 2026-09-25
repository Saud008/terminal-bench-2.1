#!/usr/bin/env python3
"""Build hidden verifier fixtures for borg retention simulator."""

from __future__ import annotations

import json
from pathlib import Path

HIDDEN_SKEW = Path("/opt/verifier-fixtures/borg/hidden-skew")
HIDDEN_HOLDS = Path("/opt/verifier-fixtures/borg/hidden-holds")


def write_skew() -> None:
    HIDDEN_SKEW.mkdir(parents=True, exist_ok=True)
    lines = """# skew + duplicate trap
edge-dup	2024-06-20T10:00:00Z	1000000	2
edge-dup	2024-06-25T10:00:00Z	2000000	3
edge-skew-a	2024-07-02T00:00:00Z	3000000	4
edge-skew-b	2024-06-28T08:00:00Z	4000000	5
edge-old	2024-01-01T00:00:00Z	500000	1
"""
    (HIDDEN_SKEW / "repo.list").write_text(lines, encoding="utf-8")
    policy = {
        "clock_skew_sec": 300,
        "keep_daily": 3,
        "keep_monthly": 2,
        "keep_weekly": 2,
        "keep_yearly": 1,
        "week_start": "monday",
    }
    (HIDDEN_SKEW / "policy.json").write_text(json.dumps(policy, indent=2) + "\n", encoding="utf-8")
    (HIDDEN_SKEW / "holds.json").write_text('{"exact":[],"prefix":[]}\n', encoding="utf-8")


def write_holds() -> None:
    HIDDEN_HOLDS.mkdir(parents=True, exist_ok=True)
    lines = """legal-q1-2024	2024-03-01T00:00:00Z	8000000	6
legal-q2-2024	2024-06-01T00:00:00Z	9000000	7
backup-not-legal	2024-06-15T00:00:00Z	1000000	1
weekly-a	2024-06-03T00:00:00Z	1100000	2
weekly-b	2024-06-10T00:00:00Z	1200000	2
stale-2023	2023-01-01T00:00:00Z	500000	1
"""
    (HIDDEN_HOLDS / "repo.list").write_text(lines, encoding="utf-8")
    policy = {
        "clock_skew_sec": 60,
        "keep_daily": 2,
        "keep_monthly": 1,
        "keep_weekly": 3,
        "keep_yearly": 1,
        "week_start": "monday",
    }
    (HIDDEN_HOLDS / "policy.json").write_text(json.dumps(policy, indent=2) + "\n", encoding="utf-8")
    holds = {"exact": [], "prefix": ["legal-"]}
    (HIDDEN_HOLDS / "holds.json").write_text(json.dumps(holds, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    write_skew()
    write_holds()
    print("hidden borg fixtures ready")


if __name__ == "__main__":
    main()
