#!/usr/bin/env bash
set -euo pipefail

SCENARIO=""
SEED=""
OUTPUT=""

usage() {
  echo "usage: gen_porcelain_fixture.sh --scenario NAME --seed SEED --output PATH" >&2
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --scenario) SCENARIO="$2"; shift 2 ;;
    --seed) SEED="$2"; shift 2 ;;
    --output) OUTPUT="$2"; shift 2 ;;
    *) usage ;;
  esac
done

[[ -z "${SCENARIO}" || -z "${SEED}" || -z "${OUTPUT}" ]] && usage

python3 - "${SCENARIO}" "${SEED}" "${OUTPUT}" <<'PY'
import random
import sys
from pathlib import Path

scenario, seed, output = sys.argv[1:4]


def fnv1a64(s: str) -> int:
    h = 0xCBF29CE484222325
    for b in s.encode("utf-8"):
        h ^= b
        h = (h * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return h


rng = random.Random(fnv1a64(f"{scenario}:{seed}"))

PAIR_POOL = [
    ("R", 62, "src/new-name.c", "src/old name.c"),
    ("R", 50, "lib/renamed.sh", "lib/original.sh"),
    ("C", 88, "docs/copy.md", "docs/source.md"),
    ("C", 49, "tmp/low-copy.txt", "tmp/source.txt"),
    ("R", 37, "drop/rename.c", "drop/old.c"),
    ("C", 50, "edge/copy.sh", "edge/base.sh"),
]

UNMERGED = [
    "u UU N 100644 100644 100644 100644 abc def ghi conflict.txt",
    "u AA N 100644 100644 100644 100644 abc def ghi both-added.txt",
    "u DU N 100644 . 100644 100644 abc . ghi deleted-upstream.txt",
    "u UD N . 100644 100644 100644 . nop ghi deleted-by-us.txt",
]

ORDINARY = [
    "1 M. N 100644 100644 100644 abc def tracked.c",
    "1 .M N 100644 100644 100644 abc def dirty.py",
]

UNTRACKED = [
    "? orphan.txt",
]


def emit(records: list[str]) -> bytes:
    rng.shuffle(records)
    return ("\0".join(records) + "\0").encode("utf-8")


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
    records.extend(UNMERGED)
    records.extend(ORDINARY[:1])
elif scenario == "mixed-worktree":
    picks = rng.sample(PAIR_POOL, 2)
    for letter, score, new_path, old_path in picks:
        xy = "R." if letter == "R" else "C."
        records.append(
            f"2 {xy} N 100644 100644 100644 abc def {letter}{score} {new_path}\t{old_path}"
        )
    records.extend(ORDINARY)
    records.extend(UNMERGED[:2])
    records.extend(UNTRACKED)
else:
    raise SystemExit(f"unknown generated scenario: {scenario}")

Path(output).parent.mkdir(parents=True, exist_ok=True)
Path(output).write_bytes(emit(records))
PY
