"""Build deterministic randomized partition/mutation fixtures."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SALT = "chmutled-fixture-v3"


def token(label: str) -> str:
    h = hashlib.sha256(f"{SALT}:{label}".encode()).hexdigest()[:8]
    return f"pt_{h}"


def write_config() -> None:
    cfg = ROOT / "config"
    cfg.mkdir(parents=True, exist_ok=True)
    (cfg / "lag_policy.json").write_text(json.dumps({"max_lag_sec": 120}, indent=2) + "\n", encoding="utf-8")
    (cfg / "catalog.json").write_text(
        json.dumps(
            {
                "tables": {
                    "events": {"partition_columns": ["month", "region"]},
                    "metrics": {"partition_columns": ["day", "shard"]},
                }
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (cfg / "anchor.txt").write_text("2024-06-15T12:00:00Z\n", encoding="utf-8")


def write_bundled() -> None:
    meta_dir = ROOT / "metadata"
    mut_dir = ROOT / "mutations"
    rep_dir = ROOT / "replicas"
    for d in (meta_dir, mut_dir, rep_dir):
        d.mkdir(parents=True, exist_ok=True)

    meta_rows = [
        {
            "part_id": token("part-a1"),
            "table_name": "events",
            "partition_key": {"month": "2024-01", "region": "eu"},
            "detached": False,
            "part_count": 2,
        },
        {
            "part_id": token("part-b1"),
            "table_name": "metrics",
            "partition_key": {"shard": "s2", "day": "2024-06-10"},
            "detached": False,
            "part_count": 1,
        },
        {
            "part_id": token("part-g1"),
            "table_name": "events",
            "partition_key": {"region": "us", "month": "2024-02"},
            "detached": True,
            "part_count": 1,
        },
    ]
    (meta_dir / "alpha.part-meta.jsonl").write_text(
        "\n".join(json.dumps(r) for r in meta_rows) + "\n", encoding="utf-8"
    )

    mut_rows = [
        {
            "mutation_id": token("mut-a1"),
            "partition_id": "events|month=2024-01|region=eu",
            "mutation_version": 9,
            "command": "DELETE WHERE obsolete=1",
            "issued_at": "2024-06-14T10:00:00Z",
        },
        {
            "mutation_id": token("mut-a2"),
            "partition_id": "events|month=2024-01|region=eu",
            "mutation_version": 10,
            "command": "UPDATE status='archived'",
            "issued_at": "2024-06-14T11:00:00Z",
        },
        {
            "mutation_id": token("mut-b1"),
            "partition_id": "metrics|day=2024-06-10|shard=s2",
            "mutation_version": 3,
            "command": "MATERIALIZE INDEX idx_latency",
            "issued_at": "2024-06-14T09:30:00Z",
        },
        {
            "mutation_id": token("mut-g1"),
            "partition_id": "events|month=2024-02|region=us",
            "mutation_version": 1,
            "command": "DROP PART",
            "issued_at": "2024-06-13T08:00:00Z",
        },
    ]
    (mut_dir / "alpha.mut-cmd.jsonl").write_text(
        "\n".join(json.dumps(r) for r in mut_rows) + "\n", encoding="utf-8"
    )

    rep_rows = [
        {
            "replica_name": token("rep-r1"),
            "partition_id": "events|month=2024-01|region=eu",
            "lag_sec": 45,
            "last_mutation_id": token("mut-a2"),
        },
        {
            "replica_name": token("rep-r2"),
            "partition_id": "events|month=2024-01|region=eu",
            "lag_sec": 130,
            "last_mutation_id": token("mut-a1"),
        },
        {
            "replica_name": token("rep-r3"),
            "partition_id": "metrics|day=2024-06-10|shard=s2",
            "lag_sec": 120,
            "last_mutation_id": token("mut-b1"),
        },
        {
            "replica_name": token("rep-r4"),
            "partition_id": "events|month=2024-02|region=us",
            "lag_sec": 10,
            "last_mutation_id": token("mut-g1"),
        },
    ]
    (rep_dir / "alpha.replica-log.jsonl").write_text(
        "\n".join(json.dumps(r) for r in rep_rows) + "\n", encoding="utf-8"
    )


def write_hidden() -> None:
    hidden = ROOT.parent / "hidden"
    meta = hidden / "metadata"
    mut = hidden / "mutations"
    rep = hidden / "replicas"
    for d in (meta, mut, rep):
        d.mkdir(parents=True, exist_ok=True)
    pid = "events|month=2024-03|region=ap"
    (meta / "hidden.part-meta.jsonl").write_text(
        json.dumps(
            {
                "part_id": token("hid-part"),
                "table_name": "events",
                "partition_key": {"month": "2024-03", "region": "ap"},
                "detached": False,
                "part_count": 1,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (mut / "hidden.mut-cmd.jsonl").write_text(
        json.dumps(
            {
                "mutation_id": token("hid-mut"),
                "partition_id": pid,
                "mutation_version": 11,
                "command": "UPDATE tier='cold'",
                "issued_at": "2024-06-14T12:00:00Z",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (rep / "hidden.replica-log.jsonl").write_text(
        json.dumps(
            {
                "replica_name": token("hid-rep"),
                "partition_id": pid,
                "lag_sec": 121,
                "last_mutation_id": token("hid-mut"),
            }
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_config()
    write_bundled()
    write_hidden()
    print("fixtures built")


if __name__ == "__main__":
    main()
