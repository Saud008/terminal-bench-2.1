"""Independent inventory-stream reference for the verifier."""

from __future__ import annotations

import json
import random
import re
from pathlib import Path

APP = Path("/app")
FIXTURES = APP / "fixtures"
CONFIG = APP / "config/export.json"
GEN = APP / "scripts/gen_porcelain_fixture.sh"

PAIR_POOL = [
    ("R", 62, "src/new-name.c", "src/old name.c"),
    ("R", 50, "lib/renamed.sh", "lib/original.sh"),
    ("C", 88, "docs/copy.md", "docs/source.md"),
    ("C", 49, "tmp/low-copy.txt", "tmp/source.txt"),
    ("R", 37, "drop/rename.c", "drop/old.c"),
    ("C", 50, "edge/copy.sh", "edge/base.sh"),
]

UNMERGED_LINES = [
    "u UU N 100644 100644 100644 100644 abc def ghi conflict.txt",
    "u AA N 100644 100644 100644 100644 abc def ghi both-added.txt",
    "u DU N 100644 . 100644 100644 abc . ghi deleted-upstream.txt",
    "u UD N . 100644 100644 100644 . nop ghi deleted-by-us.txt",
]

ORDINARY_LINES = [
    "1 M. N 100644 100644 100644 abc def tracked.c",
    "1 .M N 100644 100644 100644 abc def dirty.py",
]

UNTRACKED_LINES = ["? orphan.txt"]


def fnv1a64(seed: str) -> int:
    h = 0xCBF29CE484222325
    for b in seed.encode("utf-8"):
        h ^= b
        h = (h * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return h


def parse_record(text: str) -> dict:
    if not text:
        raise ValueError("empty record")
    tag = text[0]
    if tag == "1":
        parts = text.split(" ", 8)
        if len(parts) < 9:
            raise ValueError(text)
        return {
            "tag": "1",
            "xy": parts[1],
            "sub": parts[2],
            "mH": parts[3],
            "mI": parts[4],
            "mW": parts[5],
            "hH": parts[6],
            "hI": parts[7],
            "path": parts[8],
        }
    if tag == "2":
        parts = text.split(" ", 8)
        if len(parts) < 9:
            raise ValueError(text)
        tail = parts[8]
        m = re.match(r"^([RC])(\d+) (.+)$", tail)
        if not m:
            raise ValueError(tail)
        letter, score_s, paths = m.group(1), m.group(2), m.group(3)
        if "\t" not in paths:
            raise ValueError(paths)
        new_path, old_path = paths.split("\t", 1)
        return {
            "tag": "2",
            "xy": parts[1],
            "sub": parts[2],
            "mH": parts[3],
            "mI": parts[4],
            "mW": parts[5],
            "hH": parts[6],
            "hI": parts[7],
            "letter": letter,
            "score": int(score_s),
            "path": new_path,
            "old_path": old_path,
        }
    if tag == "u":
        parts = text.split(" ", 10)
        if len(parts) < 11:
            raise ValueError(text)
        return {
            "tag": "u",
            "xy": parts[1],
            "sub": parts[2],
            "m1": parts[3],
            "m2": parts[4],
            "m3": parts[5],
            "mW": parts[6],
            "h1": parts[7],
            "h2": parts[8],
            "h3": parts[9],
            "path": parts[10],
        }
    if tag == "?":
        return {"tag": "?", "path": text[2:]}
    if tag == "!":
        return {"tag": "!", "path": text[2:]}
    raise ValueError(text)


def parse_porcelain_bytes(data: bytes) -> list[dict]:
    records: list[dict] = []
    for chunk in data.split(b"\0"):
        if not chunk:
            continue
        records.append(parse_record(chunk.decode("utf-8")))
    return records


def is_submodule(record: dict) -> bool:
    if record["tag"] == "u":
        keys = ("m1", "m2", "m3", "mW")
    else:
        keys = ("mH", "mI", "mW")
    return any(record.get(k) == "160000" for k in keys)


def classify_records(raw: list[dict], config_path: Path | None = None) -> list[dict]:
    cfg_path = config_path or CONFIG
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    threshold = int(cfg["rename_score_min"])
    entries: list[dict] = []

    for rec in raw:
        tag = rec["tag"]
        if tag == "1":
            entries.append(
                {
                    "kind": "ordinary",
                    "xy": rec["xy"],
                    "path": rec["path"],
                    "submodule": is_submodule(rec),
                    "index_mode": rec["mI"],
                    "worktree_mode": rec["mW"],
                }
            )
        elif tag == "2":
            if rec["score"] < threshold:
                continue
            kind = "rename" if rec["letter"] == "R" else "copy"
            entries.append(
                {
                    "kind": kind,
                    "xy": rec["xy"],
                    "path": rec["path"],
                    "old_path": rec["old_path"],
                    "score": rec["score"],
                    "submodule": is_submodule(rec),
                    "index_mode": rec["mI"],
                    "worktree_mode": rec["mW"],
                }
            )
        elif tag == "u":
            entries.append(
                {
                    "kind": "unmerged",
                    "xy": rec["xy"],
                    "path": rec["path"],
                    "submodule": is_submodule(rec),
                    "worktree_mode": rec["mW"],
                    "unmerged_xy": rec["xy"],
                }
            )
        elif tag == "?":
            entries.append(
                {
                    "kind": "untracked",
                    "xy": "..",
                    "path": rec["path"],
                    "submodule": False,
                }
            )
        elif tag == "!":
            entries.append(
                {
                    "kind": "ignored",
                    "xy": "..",
                    "path": rec["path"],
                    "submodule": False,
                }
            )

    entries.sort(key=lambda e: e["path"].encode("utf-8"))
    return entries


def build_export(porcelain_path: str, config_path: str, entries: list[dict]) -> dict:
    cfg = json.loads(Path(config_path).read_text(encoding="utf-8"))
    summary = {
        "ordinary": 0,
        "rename": 0,
        "copy": 0,
        "unmerged": 0,
        "untracked": 0,
        "ignored": 0,
    }
    for entry in entries:
        summary[entry["kind"]] += 1
    return {
        "porcelain": porcelain_path,
        "config": config_path,
        "rename_score_min": int(cfg["rename_score_min"]),
        "entries": entries,
        "summary": summary,
    }


def reference_export(porcelain_path: str, config_path: str | None = None) -> dict:
    data = Path(porcelain_path).read_bytes()
    raw = parse_porcelain_bytes(data)
    cfg = config_path or str(CONFIG)
    entries = classify_records(raw, Path(cfg))
    return build_export(porcelain_path, cfg, entries)


def generate_fixture_bytes(scenario: str, seed: str) -> bytes:
    rng = random.Random(fnv1a64(f"{scenario}:{seed}"))
    records: list[str] = []

    if scenario == "rename-threshold":
        count = 3 + rng.randint(0, len(PAIR_POOL) - 3)
        picks = rng.sample(PAIR_POOL, count)
        for letter, score, new_path, old_path in picks:
            xy = "R." if letter == "R" else "C."
            records.append(
                f"2 {xy} N 100644 100644 100644 abc def {letter}{score} {new_path}\t{old_path}"
            )
    elif scenario == "unmerged-matrix":
        records.extend(UNMERGED_LINES)
        records.extend(ORDINARY_LINES[:1])
    elif scenario == "mixed-worktree":
        picks = rng.sample(PAIR_POOL, 2)
        for letter, score, new_path, old_path in picks:
            xy = "R." if letter == "R" else "C."
            records.append(
                f"2 {xy} N 100644 100644 100644 abc def {letter}{score} {new_path}\t{old_path}"
            )
        records.extend(ORDINARY_LINES)
        records.extend(UNMERGED_LINES[:2])
        records.extend(UNTRACKED_LINES)
    else:
        raise ValueError(scenario)

    rng.shuffle(records)
    return ("\0".join(records) + "\0").encode("utf-8")


def scenario_porcelain_path(name: str, seed: str, tmp_dir: Path) -> Path:
    catalog = json.loads((FIXTURES / "catalog.json").read_text(encoding="utf-8"))
    entry = next(s for s in catalog["scenarios"] if s["name"] == name)
    if entry.get("mode") == "static":
        return FIXTURES / entry["porcelain"]
    out = tmp_dir / f"{name}-{seed}.bin"
    out.write_bytes(generate_fixture_bytes(name, seed))
    return out
