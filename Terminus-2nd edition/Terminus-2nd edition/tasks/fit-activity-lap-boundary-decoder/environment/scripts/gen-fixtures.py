"""Generate deterministic FIT-like fixtures and catalog."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path("/app/fixtures/fit")
ROOT.mkdir(parents=True, exist_ok=True)


def crc16(data: bytes) -> int:
    return sum(data) & 0xFFFF


def encode_lap(start: int, end: int, distance: int, trigger: int, note: str) -> bytes:
    note_bytes = note.encode("utf-8")
    if len(note_bytes) > 12:
        raise ValueError("note too long")
    note_slot = note_bytes + (b"\x00" * (12 - len(note_bytes)))
    return (
        start.to_bytes(4, "little")
        + end.to_bytes(4, "little")
        + distance.to_bytes(2, "little")
        + bytes([trigger, len(note_bytes)])
        + note_slot
    )


def write_fit(path: Path, laps: list[tuple[int, int, int, int, str]], force_bad_crc: bool = False) -> None:
    payload = b"".join(encode_lap(*lap) for lap in laps)
    body = b"FITL" + bytes([1, len(laps)]) + payload
    checksum = crc16(body)
    if force_bad_crc:
        checksum = (checksum + 17) & 0xFFFF
    path.write_bytes(body + checksum.to_bytes(2, "little"))


fixtures: dict[str, list[tuple[int, int, int, int, str]]] = {
    "recovery": [
        (3600, 3660, 1000, 1, "warmup"),
        (3660, 3750, 1500, 2, "tempo"),
    ],
    "tempo": [
        (7200, 7320, 2000, 2, "steady"),
        (7320, 7440, 2200, 1, "push"),
        (7440, 7560, 2100, 3, "cool"),
    ],
    "shuffle-start-time": [
        (8400, 8520, 1200, 1, "middle"),
        (8280, 8400, 1100, 2, "early"),
        (8520, 8640, 1300, 3, "late"),
    ],
    "decode-align-fail": [
        (9010, 9070, 1055, 1, "misalign"),
        (9070, 9130, 1115, 2, "offgrid"),
    ],
    "decode-distance-align-fail": [
        (9600, 9660, 1055, 1, "bad-dist"),
    ],
    "boundary-equal-time": [
        (10800, 10800, 1000, 1, "flat"),
    ],
    "manual-trigger": [
        (11400, 11520, 1000, 0, "hand"),
        (11520, 11640, 1100, 2, "auto"),
    ],
}

for stem, laps in fixtures.items():
    write_fit(ROOT / f"{stem}.fit", laps)

write_fit(
    ROOT / "bad-crc.fit",
    [
        (9600, 9720, 1900, 2, "crc"),
        (9720, 9840, 1950, 1, "fail"),
    ],
    force_bad_crc=True,
)

catalog = {
    "stems": list(fixtures.keys()) + ["bad-crc"],
    "bundled": [
        {"stem": stem, "path": f"/app/fixtures/fit/{stem}.fit"}
        for stem in (list(fixtures.keys()) + ["bad-crc"])
    ],
}
(ROOT / "catalog.json").write_text(json.dumps(catalog, indent=2), encoding="utf-8")
print(f"generated {len(catalog['stems'])} fixtures")
