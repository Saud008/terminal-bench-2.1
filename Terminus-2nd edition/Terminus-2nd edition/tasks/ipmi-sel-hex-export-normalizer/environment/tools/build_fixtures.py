#!/usr/bin/env python3
"""Build deterministic SEL binary fixtures for the task image."""

from __future__ import annotations

import struct
from pathlib import Path


def xor_bytes(data: bytes) -> int:
    x = 0
    for b in data:
        x ^= b
    return x & 0xFF


def pack_record(
    record_id: int,
    record_type: int,
    timestamp: int,
    generator_id: int,
    event_rev: int,
    sensor_type: int,
    sensor_number: int,
    event_dir_type: int,
    event_data1: int = 0,
    event_data2: int = 0,
    *,
    corrupt_xor: bool = False,
) -> bytes:
    body = struct.pack(
        "<HBIHBBBBBB",
        record_id,
        record_type,
        timestamp,
        generator_id,
        event_rev,
        sensor_type,
        sensor_number,
        event_dir_type,
        event_data1,
        event_data2,
    )
    chk = xor_bytes(body)
    if corrupt_xor:
        chk ^= 0xFF
    return body + bytes([chk])


def pack_file(records: list[bytes], record_length: int = 16) -> bytes:
    header = b"SEL1" + struct.pack("<HB", len(records), record_length)
    header += bytes([xor_bytes(header)])
    return header + b"".join(records)


def main() -> None:
  root = Path(__file__).resolve().parents[1]
  fixtures = root / "fixtures"
  fixtures.mkdir(parents=True, exist_ok=True)

  alpha = [
      pack_record(1, 0x02, 1_700_000_100, 0x0020, 0x04, 0x07, 0x01, 0x07),
      pack_record(2, 0x02, 1_700_000_050, 0x0020, 0x04, 0x0C, 0x02, 0x01),
      pack_record(3, 0x02, 1_700_000_200, 0x0020, 0x04, 0x04, 0x03, 0x08),
      pack_record(4, 0x02, 1_700_000_150, 0x0020, 0x04, 0x13, 0x01, 0x02),
  ]
  (fixtures / "sel_alpha.bin").write_bytes(pack_file(alpha))

  beta = [
      pack_record(10, 0x02, 1_700_100_000, 0x0030, 0x04, 0xC0, 0x01, 0x01),
      pack_record(11, 0x02, 1_700_100_030, 0x0030, 0x04, 0xDC, 0x02, 0x07),
      pack_record(12, 0x02, 1_700_100_010, 0x0030, 0x04, 0xC1, 0x03, 0x06),
      pack_record(13, 0x03, 1_700_100_999, 0x0030, 0x04, 0x01, 0x01, 0x01),
      pack_record(14, 0x02, 1_700_100_020, 0x0030, 0x04, 0x23, 0x01, 0x03, corrupt_xor=True),
  ]
  (fixtures / "sel_beta.bin").write_bytes(pack_file(beta))


if __name__ == "__main__":
    main()
