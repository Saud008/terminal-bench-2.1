#!/usr/bin/env python3
"""Build libpcap savefile fixtures for pcapjitter task."""

from __future__ import annotations

import hashlib
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CAPTURES = ROOT / "captures"
HIDDEN = ROOT / "hidden"

MAGIC_LE = 0xA1B2C3D4
MAGIC_BE = 0xD4C3B2A1


def write_pcap(path: Path, packets: list[tuple[int, int, bytes, int | None]], big_endian: bool) -> None:
    """Write classic pcap. packets: (ts_sec, ts_usec, payload, orig_len override)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    magic = MAGIC_BE if big_endian else MAGIC_LE
    endian = ">" if big_endian else "<"
    parts = [struct.pack(f"{endian}I", magic)]
    parts.append(struct.pack(f"{endian}HH", 2, 4))
    parts.append(struct.pack(f"{endian}i", 0))
    parts.append(struct.pack(f"{endian}I", 0))
    parts.append(struct.pack(f"{endian}I", 65535))
    parts.append(struct.pack(f"{endian}I", 1))
    for ts_sec, ts_usec, payload, orig_override in packets:
        incl = len(payload)
        orig = incl if orig_override is None else orig_override
        parts.append(struct.pack(f"{endian}IIII", ts_sec, ts_usec, incl, orig))
        parts.append(payload)
    path.write_bytes(b"".join(parts))


def payload(tag: int, size: int = 60) -> bytes:
    base = bytes([tag & 0xFF]) * 4
    return (base * (size // len(base) + 1))[:size]


def main() -> None:
    CAPTURES.mkdir(parents=True, exist_ok=True)
    HIDDEN.mkdir(parents=True, exist_ok=True)

    write_pcap(
        CAPTURES / "001-window-order.pcap",
        [
            (1, 0, payload(1), None),
            (1, 3003, payload(2), None),
            (1, 2002, payload(3), None),
            (1, 10000, payload(4), None),
        ],
        big_endian=False,
    )

    write_pcap(
        CAPTURES / "002-big-endian.pcap",
        [
            (2, 0, payload(10), None),
            (2, 1500, payload(11), None),
            (2, 2500, payload(12), None),
        ],
        big_endian=True,
    )

    write_pcap(
        CAPTURES / "003-truncated.pcap",
        [
            (10, 0, payload(20, 40), 80),
            (10, 5000, payload(21), None),
            (10, 9000, payload(22, 30), 60),
        ],
        big_endian=False,
    )

    write_pcap(
        CAPTURES / "004-gap-timeline.pcap",
        [
            (100, 0, payload(30), None),
            (101, 500000, payload(31), None),
            (103, 0, payload(32), None),
        ],
        big_endian=False,
    )

    write_pcap(
        HIDDEN / "005-mixed-probe.pcap",
        [
            (5, 0, payload(40, 50), 100),
            (5, 4000, payload(41), None),
            (5, 3500, payload(42), None),
            (6, 0, payload(43), None),
        ],
        big_endian=True,
    )

    for label, directory in (("captures", CAPTURES), ("hidden", HIDDEN)):
        print(f"# {label}")
        for path in sorted(directory.glob("*.pcap")):
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            print(f"{path.name} {digest}")


if __name__ == "__main__":
    main()
