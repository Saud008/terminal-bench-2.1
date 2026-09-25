#!/usr/bin/env python3
"""Build bundled seed borg list fixture."""

from __future__ import annotations

from pathlib import Path

SEED = Path("/app/fixtures/seed/repo.list")

LINES = """# seed repository list for borg-prune-sim
host-2024-06-01	2024-06-01T06:00:00Z	12000000	8
host-2024-06-02	2024-06-02T06:00:00Z	12100000	8
host-2024-06-03	2024-06-03T06:00:00Z	12200000	9
host-2024-06-10	2024-06-10T06:00:00Z	13000000	10
host-2024-06-17	2024-06-17T06:00:00Z	14000000	11
host-2024-05-15	2024-05-15T06:00:00Z	9000000	6
host-2024-04-01	2024-04-01T06:00:00Z	8000000	5
host-2024-01-15	2024-01-15T06:00:00Z	7000000	4
host-2024-01-15	2024-01-15T18:00:00Z	7500000	5
host-2023-07-01	2023-07-01T06:00:00Z	6000000	3
host-2022-06-01	2022-06-01T06:00:00Z	5000000	2
host-skewed-future	2024-07-01T12:00:00Z	2000000	2
"""


def main() -> None:
    SEED.parent.mkdir(parents=True, exist_ok=True)
    SEED.write_text(LINES, encoding="utf-8")
    print(f"wrote {SEED}")


if __name__ == "__main__":
    main()
