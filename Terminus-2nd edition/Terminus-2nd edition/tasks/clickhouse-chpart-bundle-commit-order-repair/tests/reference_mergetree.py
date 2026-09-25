"""Independent reference decoder for chparts part bundles."""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path


def table_suffix() -> str:
    return os.environ.get("CHPARTS_TABLE_SUFFIX", "default")


def table_name() -> str:
    return f"TB3_{table_suffix()}_events"


def load_part(part_dir: Path) -> tuple[dict, list[dict]]:
    meta = json.loads((part_dir / "part.meta.json").read_text(encoding="utf-8"))
    rows: list[dict] = []
    lines = (part_dir / "data.tsv").read_text(encoding="utf-8").splitlines()
    header = lines[0].split("\t")
    idx = {name: i for i, name in enumerate(header)}
    for line in lines[1:]:
        if not line.strip():
            continue
        cols = line.split("\t")
        rows.append(
            {
                "id": cols[idx["id"]],
                "ver": int(cols[idx["ver"]]),
                "value": cols[idx["value"]],
                "expire_ts": int(cols[idx["expire_ts"]]),
                "part_id": meta["part_id"],
            }
        )
    return meta, rows


def checksum_file(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return f"sha256:{digest}"


def _part_dirs(parts_root: Path) -> list[Path]:
    out: list[Path] = []
    for meta in sorted(parts_root.rglob("part.meta.json")):
        out.append(meta.parent)
    return out


def write_part_bundle(
    root: Path,
    part_id: str,
    batch_id: str,
    rows: list[tuple[str, int, str, int]],
    *,
    max_block: int = 1,
) -> Path:
    """Write one part bundle directory and return its path."""
    part_dir = root / part_id
    part_dir.mkdir(parents=True, exist_ok=True)
    lines = ["id\tver\tvalue\texpire_ts"]
    for row_id, ver, value, expire_ts in rows:
        lines.append(f"{row_id}\t{ver}\t{value}\t{expire_ts}")
    data_path = part_dir / "data.tsv"
    data_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    digest = hashlib.sha256(data_path.read_bytes()).hexdigest()
    meta = {
        "part_id": part_id,
        "batch_id": batch_id,
        "checksum": f"sha256:{digest}",
        "min_block": 0,
        "max_block": max_block,
        "table": "events",
    }
    (part_dir / "part.meta.json").write_text(json.dumps(meta), encoding="utf-8")
    return part_dir


def reference_merge_parts(parts_root: Path, grace_ms: int = 86_400_000) -> dict:
    part_dirs = _part_dirs(parts_root)
    all_rows: list[dict] = []
    parts_stats: list[dict] = []
    max_block = 0
    seen_keys: set[str] = set()

    for part_dir in part_dirs:
        meta, rows = load_part(part_dir)
        key = f"{meta['batch_id']}:{meta['part_id']}"
        if key in seen_keys:
            continue
        seen_keys.add(key)

        ok = checksum_file(part_dir / "data.tsv") == meta["checksum"]
        parts_stats.append(
            {
                "part_id": meta["part_id"],
                "row_count": len(rows),
                "checksum_ok": ok,
                "committed": ok,
            }
        )
        if not ok:
            continue
        all_rows.extend(rows)
        max_block = max(max_block, int(meta["max_block"]))

    merged: dict[str, dict] = {}
    for row in all_rows:
        cur = merged.get(row["id"])
        if cur is None or row["ver"] > cur["ver"]:
            merged[row["id"]] = {
                "id": row["id"],
                "ver": row["ver"],
                "value": row["value"],
                "expire_ts": row["expire_ts"],
            }

    cutoff = int(time.time() * 1000) - grace_ms
    rows_out = [r for r in merged.values() if r["expire_ts"] >= cutoff]
    rows_out.sort(key=lambda r: r["id"])
    parts_stats.sort(key=lambda p: p["part_id"])

    return {
        "table_suffix": table_suffix(),
        "table_name": table_name(),
        "max_block_number": max_block,
        "fsynced": True,
        "parts": parts_stats,
        "rows": rows_out,
        "row_count": len(rows_out),
    }


def reference_export(parts_root: Path) -> dict:
    ref = reference_merge_parts(parts_root)
    return {
        "table_name": ref["table_name"],
        "max_block_number": ref["max_block_number"],
        "row_count": ref["row_count"],
        "rows": ref["rows"],
        "parts": ref["parts"],
    }


def build_hidden_parts_dir(root: Path) -> Path:
    """Create extra part bundle data generated at test time (not in the agent image)."""
    write_part_bundle(
        root,
        "part-h1",
        "hidden-x",
        [("9", 3, "hidden", 9_999_999_999_999), ("9", 7, "hidden-win", 9_999_999_999_999)],
        max_block=2,
    )
    return root
