"""Independent reference for the srtctl normalize temporal closure pipeline."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

RUBY_SHIFT_MS = 250
ROLLUP_GAP_MS = 120
EXPORT_FORMAT = "srt-normalized-v1"


def fnv1a64_bytes(data: bytes) -> int:
    hash_val = 0xCBF29CE484222325
    for byte in data:
        hash_val ^= byte
        hash_val = (hash_val * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return hash_val


def seed_offset_ms(seed: str) -> int:
    return 50 + (fnv1a64_bytes(seed.encode("utf-8")) % 450)


def input_digest(path: Path) -> str:
    return f"{fnv1a64_bytes(path.read_bytes()):016x}"


def snapshot_body_digest(path: Path) -> str:
    return f"{fnv1a64_bytes(path.read_bytes()):016x}"


@dataclass
class ParsedCue:
    source_index: int
    start_ms: int
    end_ms: int
    lines: list[str]
    has_an8: bool


@dataclass
class RubySegment:
    base: str
    reading: str
    start_ms: int
    end_ms: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "base": self.base,
            "reading": self.reading,
            "start_ms": self.start_ms,
            "end_ms": self.end_ms,
        }


@dataclass
class RubyCue:
    source_index: int
    start_ms: int
    end_ms: int
    text: str
    ruby_segments: list[RubySegment] = field(default_factory=list)
    rolled_up: bool = False


def parse_timestamp(raw: str) -> int | None:
    normalized = raw.strip().replace(",", ".")
    if "." not in normalized:
        return None
    hms, ms_part = normalized.split(".", 1)
    parts = hms.split(":")
    if len(parts) != 3:
        return None
    try:
        hours, minutes, seconds, millis = (int(parts[0]), int(parts[1]), int(parts[2]), int(ms_part))
    except ValueError:
        return None
    return hours * 3_600_000 + minutes * 60_000 + seconds * 1_000 + millis


def parse_file(path: Path) -> list[ParsedCue]:
    raw = path.read_text(encoding="utf-8")
    text = raw.lstrip("\ufeff")
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in text.split("\n"):
        trimmed = line.rstrip("\r").strip()
        if not trimmed:
            if current:
                blocks.append(current)
                current = []
            continue
        current.append(trimmed)
    if current:
        blocks.append(current)

    cues: list[ParsedCue] = []
    auto_index = 1
    for block in blocks:
        if len(block) < 2:
            continue
        timing_line = block[1]
        if "-->" not in timing_line:
            continue
        start_raw, end_raw = timing_line.split("-->", 1)
        start_ms = parse_timestamp(start_raw) or 0
        end_ms = parse_timestamp(end_raw) or 0
        lines = block[2:]
        has_an8 = any("{\\an8}" in line for line in lines)
        cues.append(
            ParsedCue(
                source_index=auto_index,
                start_ms=start_ms,
                end_ms=end_ms,
                lines=lines,
                has_an8=has_an8,
            )
        )
        auto_index += 1
    return cues


def resolve_overlaps(cues: list[ParsedCue]) -> tuple[list[ParsedCue], int]:
    sorted_cues = sorted(cues, key=lambda c: (c.start_ms, c.source_index))
    trims = 0
    for idx in range(len(sorted_cues) - 1):
        next_start = sorted_cues[idx + 1].start_ms
        if sorted_cues[idx].end_ms > next_start:
            sorted_cues[idx].end_ms = next_start
            trims += 1
    return sorted_cues, trims


def extract_ruby(raw: str, start_ms: int) -> tuple[str, list[RubySegment]]:
    display: list[str] = []
    ruby_base: list[str] = []
    segments: list[RubySegment] = []
    pos = 0
    while pos < len(raw):
        if raw.startswith("{\\an8}", pos):
            pos += len("{\\an8}")
            continue
        if raw.startswith("{rt}", pos):
            base = "".join(ruby_base)
            ruby_base.clear()
            pos += len("{rt}")
            read_start = pos
            while pos < len(raw) and not raw.startswith("{rt}", pos) and not raw.startswith("{\\an8}", pos):
                pos += 1
            reading = raw[read_start:pos]
            segments.append(RubySegment(base=base, reading=reading, start_ms=start_ms, end_ms=start_ms))
            continue
        ch = raw[pos]
        display.append(ch)
        ruby_base.append(ch)
        pos += 1
    return "".join(display).strip(), segments


def apply_ruby_shifts(cues: list[ParsedCue]) -> tuple[list[RubyCue], int]:
    out: list[RubyCue] = []
    shifts = 0
    for cue in cues:
        raw_text = "\n".join(cue.lines)
        display_text, segments = extract_ruby(raw_text, cue.start_ms)
        if cue.has_an8:
            for segment in segments:
                extended = min(segment.end_ms + RUBY_SHIFT_MS, cue.end_ms)
                if extended > segment.end_ms:
                    shifts += 1
                segment.end_ms = extended
        out.append(
            RubyCue(
                source_index=cue.source_index,
                start_ms=cue.start_ms,
                end_ms=cue.end_ms,
                text=display_text,
                ruby_segments=segments,
            )
        )
    return out, shifts


def ends_sentence(text: str) -> bool:
    stripped = text.rstrip()
    if not stripped:
        return False
    return stripped[-1] in ".!?"


def apply_rollup(cues: list[RubyCue]) -> tuple[list[RubyCue], int]:
    out: list[RubyCue] = []
    removals = 0
    for cue in cues:
        if out:
            prev = out[-1]
            gap = cue.start_ms - prev.end_ms if cue.start_ms >= prev.end_ms else 0
            if gap <= ROLLUP_GAP_MS and not ends_sentence(prev.text):
                prev.text = f"{prev.text} {cue.text}"
                prev.end_ms = cue.end_ms
                prev.ruby_segments.extend(cue.ruby_segments)
                prev.rolled_up = True
                removals += 1
                continue
        out.append(
            RubyCue(
                source_index=cue.source_index,
                start_ms=cue.start_ms,
                end_ms=cue.end_ms,
                text=cue.text,
                ruby_segments=list(cue.ruby_segments),
                rolled_up=cue.rolled_up,
            )
        )
    return out, removals


def normalize_export(path: Path, seed: str, fixture: str) -> dict[str, Any]:
    parsed = parse_file(path)
    parsed_count = len(parsed)
    offset = seed_offset_ms(seed)

    offset_cues: list[ParsedCue] = []
    for cue in parsed:
        offset_cues.append(
            ParsedCue(
                source_index=cue.source_index,
                start_ms=cue.start_ms + offset,
                end_ms=cue.end_ms + offset,
                lines=list(cue.lines),
                has_an8=cue.has_an8,
            )
        )

    overlap_resolved, overlap_trims = resolve_overlaps(offset_cues)
    ruby_applied, ruby_shifts = apply_ruby_shifts(overlap_resolved)
    rolled, rollup_removals = apply_rollup(ruby_applied)

    cues: list[dict[str, Any]] = []
    for idx, cue in enumerate(rolled):
        cues.append(
            {
                "index": idx + 1,
                "source_index": cue.source_index,
                "start_ms": cue.start_ms,
                "end_ms": cue.end_ms,
                "text": cue.text,
                "ruby_segments": [seg.as_dict() for seg in cue.ruby_segments],
                "rolled_up": cue.rolled_up,
            }
        )

    return {
        "fixture": fixture,
        "seed": seed,
        "seed_offset_ms": offset,
        "format": EXPORT_FORMAT,
        "cues": cues,
        "stats": {
            "parsed": parsed_count,
            "exported": len(cues),
            "overlap_trims": overlap_trims,
            "rollup_removals": rollup_removals,
            "ruby_shifts": ruby_shifts,
        },
    }


def snapshot_dir(fixture: str, seed: str) -> Path:
    return Path("/app/state/srtctl") / f"{fixture}-{seed}"


def procedural_combo_07_srt() -> str:
    return (
        "1\n"
        "00:00:01,000 --> 00:00:05,000\n"
        "{\\an8}Cap{rt}きゃ\n"
        "\n"
        "2\n"
        "00:00:03,500 --> 00:00:07,000\n"
        "Overlap trims first cue end.\n"
    )


def procedural_rollup_ruby_23_srt() -> str:
    return (
        "1\n"
        "00:00:01,000 --> 00:00:02,090\n"
        "{\\an8}Keep{rt}きー\n"
        "\n"
        "2\n"
        "00:00:02,150 --> 00:00:04,000\n"
        "also{rt}ある\n"
    )


def load_catalog(catalog_path: Path = Path("/app/fixtures/catalog.json")) -> list[str]:
    data = json.loads(catalog_path.read_text(encoding="utf-8"))
    return [entry["name"] for entry in data["fixtures"]]
