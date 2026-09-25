#!/usr/bin/env python3
"""Generate PostgreSQL WAL archive fixture trees."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path("/app/fixtures/archives")
ROOT.mkdir(parents=True, exist_ok=True)
CONFIG = Path("/app/config")
CONFIG.mkdir(parents=True, exist_ok=True)

(SEGMENT_CLOCK := {
    "seconds_per_segment": 60,
    "epoch_start": "2024-06-15 14:30:00 UTC",
})
(CONFIG / "segment-clock.json").write_text(json.dumps(SEGMENT_CLOCK, indent=2), encoding="utf-8")


def wal_name(timeline: int, segment: int) -> str:
    return f"{timeline:08X}{segment:016X}"


def write_label(
    archive: Path,
    timeline: int,
    start_segment: int,
    label: str,
    start_time: str = "2024-06-15 14:30:00 UTC",
) -> None:
    start_file = wal_name(timeline, start_segment)
    text = f"""START WAL LOCATION: 0/3000028 (file {start_file}, offset 40)
CHECKPOINT LOCATION: 0/3000060 (file {start_file}, offset 96)
BACKUP METHOD: streamed
BACKUP FROM: primary
START TIME: {start_time}
LABEL: {label}
START TIMELINE: {timeline}
"""
    (archive / "backup_label").write_text(text, encoding="utf-8")


def touch_segment(archive: Path, timeline: int, segment: int, partial: bool = False) -> None:
    name = wal_name(timeline, segment)
    if partial:
        name = f"{name}.partial"
    (archive / name).write_bytes(b"\x00" * 16)


def build_alpha() -> None:
    ar = ROOT / "alpha"
    ar.mkdir(parents=True, exist_ok=True)
    write_label(ar, 1, 1, "alpha-base")
    for seg in range(1, 6):
        touch_segment(ar, 1, seg)


def build_gap() -> None:
    ar = ROOT / "gap"
    ar.mkdir(parents=True, exist_ok=True)
    write_label(ar, 1, 1, "gap-base")
    for seg in (1, 2, 4, 5):
        touch_segment(ar, 1, seg)


def build_timeline_switch() -> None:
    ar = ROOT / "timeline-switch"
    ar.mkdir(parents=True, exist_ok=True)
    write_label(ar, 1, 1, "switch-base")
    touch_segment(ar, 1, 1)
    touch_segment(ar, 1, 2)
    (ar / "00000002.history").write_text(
        "1\t0/2000028\tno recovery target\n2\t0/3000000\tpromoted\n",
        encoding="utf-8",
    )
    for seg in range(1, 4):
        touch_segment(ar, 2, seg)


def build_partial() -> None:
    ar = ROOT / "partial-block"
    ar.mkdir(parents=True, exist_ok=True)
    write_label(ar, 1, 1, "partial-base")
    for seg in (1, 2, 3):
        touch_segment(ar, 1, seg)
    touch_segment(ar, 1, 4, partial=True)
    touch_segment(ar, 1, 5)


def build_shuffle_label() -> None:
    ar = ROOT / "shuffle-label"
    ar.mkdir(parents=True, exist_ok=True)
    start_file = wal_name(1, 1)
    text = f"""START WAL LOCATION: 0/3000028 (file {start_file}, offset 40)
CHECKPOINT LOCATION: 0/3000060 (file {start_file}, offset 96)
BACKUP METHOD: streamed
BACKUP FROM: primary
START TIME:   2024-06-15 14:30:00 UTC
LABEL: shuffle-base
START TIMELINE: 1
"""
    (ar / "backup_label").write_text(text, encoding="utf-8")
    for seg in range(1, 4):
        touch_segment(ar, 1, seg)


build_alpha()
build_gap()
build_timeline_switch()
build_partial()
build_shuffle_label()

TB3 = Path("/app/tb3-bundle")
TB3.mkdir(parents=True, exist_ok=True)
tb3_tl = 0x0000000A
tb3_ar = TB3 / "tb3-random-timeline"
tb3_ar.mkdir(parents=True, exist_ok=True)
write_label(tb3_ar, tb3_tl, 1, "tb3-hidden", start_time="2024-01-01 00:00:00 UTC")
for seg in range(1, 4):
    touch_segment(tb3_ar, tb3_tl, seg)
(TB3 / "tb3-clock.json").write_text(
    json.dumps({"seconds_per_segment": 45, "epoch_start": "2024-01-01 00:00:00 UTC"}, indent=2),
    encoding="utf-8",
)

catalog = {
    "archives": [
        {"stem": "alpha", "path": "/app/fixtures/archives/alpha"},
        {"stem": "gap", "path": "/app/fixtures/archives/gap"},
        {"stem": "timeline-switch", "path": "/app/fixtures/archives/timeline-switch"},
        {"stem": "partial-block", "path": "/app/fixtures/archives/partial-block"},
        {"stem": "shuffle-label", "path": "/app/fixtures/archives/shuffle-label"},
    ]
}
(ROOT / "catalog.json").write_text(json.dumps(catalog, indent=2), encoding="utf-8")
print(f"generated {len(catalog['archives'])} archive fixtures")
