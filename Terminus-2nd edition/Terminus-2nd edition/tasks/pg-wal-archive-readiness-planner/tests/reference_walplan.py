"""Independent reference for PostgreSQL WAL archive restore planner."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

STAGING_VERSION = 1
SCHEMA = "pg-wal-restore-plan/1"
SEGMENT_RE = re.compile(r"^([0-9A-Fa-f]{24})(?:\.partial)?$")
HISTORY_LINE = re.compile(r"^([0-9A-Fa-f]+)\t")


def parse_utc(text: str) -> datetime:
    cleaned = text.strip().replace(" UTC", "").replace("T", " ")
    return datetime.strptime(cleaned, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)


def format_utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def load_segment_clock(config_root: Path | None = None) -> dict[str, Any]:
    root = config_root or Path("/app/config")
    data = json.loads((root / "segment-clock.json").read_text(encoding="utf-8"))
    return {
        "seconds_per_segment": int(data["seconds_per_segment"]),
        "epoch_start": data["epoch_start"],
    }


def split_wal_name(name: str) -> tuple[int, int] | None:
    base = name
    if base.endswith(".partial"):
        base = base[: -len(".partial")]
    if not SEGMENT_RE.match(base):
        return None
    timeline = int(base[0:8], 16)
    segment = int(base[8:24], 16)
    return timeline, segment


def list_archive_files(archive_root: Path) -> tuple[list[str], list[str], list[dict[str, Any]]]:
    segments: list[str] = []
    partials: list[str] = []
    timelines: list[dict[str, Any]] = []
    for path in sorted(archive_root.iterdir()):
        if not path.is_file():
            continue
        name = path.name
        if name.endswith(".history"):
            tl = int(path.stem, 16)
            parents: list[int] = []
            for line in path.read_text(encoding="utf-8").splitlines():
                m = HISTORY_LINE.match(line.strip())
                if m:
                    parents.append(int(m.group(1), 16))
            timelines.append({"timeline": tl, "parents": parents})
            continue
        if name.endswith(".partial"):
            partials.append(name)
            continue
        if SEGMENT_RE.match(name):
            segments.append(name.upper())
    segments.sort()
    partials.sort()
    timelines.sort(key=lambda row: row["timeline"])
    return segments, partials, timelines


def parse_backup_label(archive_root: Path) -> dict[str, Any]:
    text = (archive_root / "backup_label").read_text(encoding="utf-8")
    start_time = None
    start_timeline = None
    start_file = None
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("START TIME:"):
            start_time = parse_utc(line.split(":", 1)[1].strip())
        elif line.startswith("START TIMELINE:"):
            start_timeline = int(line.split(":", 1)[1].strip(), 10)
        elif line.startswith("START WAL LOCATION:") and "file" in line:
            m = re.search(r"file\s+([0-9A-Fa-f]{24})", line)
            if m:
                start_file = m.group(1).upper()
    if start_time is None or start_timeline is None or start_file is None:
        raise ValueError("backup_label incomplete")
    return {
        "start_time": format_utc(start_time),
        "start_timeline": start_timeline,
        "start_segment_file": start_file,
    }


def continuity_gaps(segments: list[str]) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    by_timeline: dict[int, list[int]] = {}
    for name in segments:
        parsed = split_wal_name(name)
        if parsed is None:
            continue
        tl, seg = parsed
        by_timeline.setdefault(tl, []).append(seg)
    for tl in sorted(by_timeline):
        nums = sorted(by_timeline[tl])
        for prev, cur in zip(nums, nums[1:]):
            if cur != prev + 1:
                gaps.append(
                    {
                        "timeline": tl,
                        "from_segment": f"{tl:08X}{prev:016X}",
                        "to_segment": f"{tl:08X}{cur:016X}",
                    }
                )
    return gaps


def staging_digest(segments: list[str], timelines: list[dict[str, Any]], label: dict[str, Any]) -> str:
    payload = json.dumps(
        {
            "segments": segments,
            "timelines": timelines,
            "start_timeline": label["start_timeline"],
            "start_segment_file": label["start_segment_file"],
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def expected_stage(
    archive_root: Path,
    config_root: Path | None = None,
) -> dict[str, Any]:
    label = parse_backup_label(archive_root)
    segments, partials, timelines = list_archive_files(archive_root)
    digest = staging_digest(segments, timelines, label)
    return {
        "staging_version": STAGING_VERSION,
        "archive_root": str(archive_root),
        "start_time": label["start_time"],
        "start_timeline": label["start_timeline"],
        "start_segment_file": label["start_segment_file"],
        "segments_present": segments,
        "partial_files": partials,
        "timelines": timelines,
        "digest": digest,
    }


def segment_end_time(start_time: str, segment_file: str, clock: dict[str, Any]) -> datetime:
    parsed = split_wal_name(segment_file)
    assert parsed is not None
    _, seg_num = parsed
    base = parse_utc(start_time)
    return base + timedelta(seconds=seg_num * int(clock["seconds_per_segment"]))


def select_restore_target(
    segments: list[str],
    start_time: str,
    restore_target: str,
    clock: dict[str, Any],
) -> str | None:
    target = parse_utc(restore_target)
    selected: str | None = None
    selected_end: datetime | None = None
    for name in segments:
        end = segment_end_time(start_time, name, clock)
        if end <= target and (selected_end is None or end > selected_end):
            selected = name
            selected_end = end
    return selected


def expected_plan(
    archive_root: Path,
    restore_target: str,
    config_root: Path | None = None,
) -> dict[str, Any]:
    stage = expected_stage(archive_root, config_root)
    clock = load_segment_clock(config_root)
    gaps = continuity_gaps(stage["segments_present"])
    partial_in_range = [
        p
        for p in stage["partial_files"]
        if split_wal_name(p) is not None
    ]
    selected = select_restore_target(
        stage["segments_present"],
        stage["start_time"],
        restore_target,
        clock,
    )
    continuity_ok = len(gaps) == 0
    partial_rejected: list[str] = []
    if selected:
        sel_tl, sel_seg = split_wal_name(selected)  # type: ignore[misc]
        for p in partial_in_range:
            parsed = split_wal_name(p)
            if parsed and parsed[0] == sel_tl and parsed[1] <= sel_seg:
                partial_rejected.append(p)
    restore_ready = continuity_ok and selected is not None and len(partial_rejected) == 0
    parsed = split_wal_name(selected) if selected else (stage["start_timeline"], 0)
    return {
        "schema": SCHEMA,
        "archive_root": stage["archive_root"],
        "staging_version": STAGING_VERSION,
        "restore_ready": restore_ready,
        "restore_target_time": format_utc(parse_utc(restore_target)),
        "target_timeline": parsed[0] if selected else stage["start_timeline"],
        "selected_segment": selected,
        "continuity_ok": continuity_ok,
        "gaps": gaps,
        "partial_rejected": partial_rejected,
        "digest": stage["digest"],
    }


def load_catalog(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
