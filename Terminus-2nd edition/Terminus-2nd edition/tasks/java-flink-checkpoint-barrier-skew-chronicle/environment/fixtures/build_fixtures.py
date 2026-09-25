#!/usr/bin/env python3
"""Seed RNG fixture packs for flink-skew verifier."""
from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "config"


def write_config() -> None:
    CONFIG.mkdir(parents=True, exist_ok=True)
    graph = {
        "operators": [
            {"operator_id": "src-1", "parallelism": 2, "vertex_index": 0, "chain_head": True, "chain_tail": True},
            {"operator_id": "map-2", "parallelism": 4, "vertex_index": 1, "chain_head": True, "chain_tail": False},
            {"operator_id": "sink-3", "parallelism": 4, "vertex_index": 2, "chain_head": False, "chain_tail": True},
        ]
    }
    (CONFIG / "operator_graph.json").write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
    (CONFIG / "job_meta.json").write_text(
        json.dumps({"job_id": "job-f7c2a91e-flinkops", "alignment_timeout_ms": 60000}, indent=2) + "\n",
        encoding="utf-8",
    )


def emit_job(rng: random.Random, out_dir: Path, job_suffix: str, unaligned_cp: int | None, chain_stress: bool) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    events = []
    base_ts = 1_710_000_000_000 + rng.randint(0, 999_999)
    cp_ids = [rng.randint(10, 99) for _ in range(3)]
    if unaligned_cp is not None and unaligned_cp not in cp_ids:
        cp_ids[0] = unaligned_cp
    for cp in cp_ids:
        for attempt in (1, 2):
            is_unaligned = unaligned_cp is not None and cp == unaligned_cp
            timeout = 60000
            for op, par in (("src-1", 2), ("map-2", 4), ("sink-3", 4)):
                for st in range(par):
                    skew = rng.randint(0, 120) if not is_unaligned else rng.randint(200, 800)
                    ts = base_ts + skew + st * 5
                    events.append({
                        "event_kind": "CHECKPOINT_BARRIER",
                        "checkpoint_id": cp,
                        "attempt_id": attempt,
                        "operator_id": op,
                        "subtask_index": st,
                        "timestamp_ms": ts,
                        "is_unaligned": is_unaligned,
                        "aligned_checkpoint_timeout_ms": timeout,
                    })
                    if chain_stress and op == "map-2" and st == 0:
                        events.append({
                            "event_kind": "CHECKPOINT_BARRIER",
                            "checkpoint_id": cp,
                            "attempt_id": attempt,
                            "operator_id": "sink-3",
                            "subtask_index": 0,
                            "timestamp_ms": ts + 1,
                            "is_unaligned": is_unaligned,
                            "aligned_checkpoint_timeout_ms": timeout,
                        })
            for op, par in (("src-1", 2), ("map-2", 4)):
                for st in range(par):
                    events.append({
                        "event_kind": "WATERMARK",
                        "checkpoint_id": cp,
                        "attempt_id": attempt,
                        "operator_id": op,
                        "subtask_index": st,
                        "timestamp_ms": base_ts - 50 + st,
                        "is_unaligned": False,
                        "aligned_checkpoint_timeout_ms": timeout,
                    })
            events.append({
                "event_kind": "CHECKPOINT_COMPLETED",
                "checkpoint_id": cp,
                "attempt_id": attempt,
                "operator_id": "sink-3",
                "subtask_index": 0,
                "timestamp_ms": base_ts + 5000,
                "is_unaligned": is_unaligned,
                "aligned_checkpoint_timeout_ms": timeout,
            })
    path = out_dir / f"cp-events-{job_suffix}.jsonl"
    with path.open("w", encoding="utf-8") as fh:
        for row in sorted(events, key=lambda r: (r["timestamp_ms"], r["operator_id"], r["subtask_index"])):
            fh.write(json.dumps(row, separators=(",", ":")) + "\n")


def main() -> None:
    write_config()
    emit_job(random.Random(0xF7C2A91E), ROOT / "jm-events", "primary", unaligned_cp=None, chain_stress=True)
    emit_job(random.Random(0xA11CE), ROOT.parent / "hidden/unaligned_only/jm-events", "unaligned", unaligned_cp=42, chain_stress=False)
    emit_job(random.Random(0xC04100), ROOT.parent / "hidden/chained_only/jm-events", "chained", unaligned_cp=None, chain_stress=True)
    manifest = hashlib.sha256()
    for path in sorted(ROOT.rglob("*.jsonl")):
        manifest.update(path.read_bytes())
    (ROOT / "fixtures_manifest.sha256").write_text(manifest.hexdigest() + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
