"""Generate deterministic SLWS waveform fixtures and catalog."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path("/app/fixtures/slws")
ROOT.mkdir(parents=True, exist_ok=True)
POL = Path("/app/config/polarity")
POL.mkdir(parents=True, exist_ok=True)
LEAP = Path("/app/config/leap")
LEAP.mkdir(parents=True, exist_ok=True)

RATE = 100_000  # 100 Hz in millihertz


def crc16(data: bytes) -> int:
    return sum(data) & 0xFFFF


def clip_mask_for(indices: set[int], sample_count: int) -> bytes:
    nbytes = (sample_count + 7) // 8
    mask = bytearray(nbytes)
    for idx in indices:
        mask[idx // 8] |= 1 << (idx % 8)
    return bytes(mask)


def encode_slws(
    network: str,
    station: str,
    epoch_sec: int,
    leap_marker: int,
    samples: list[int],
    picks: list[tuple[int, int]],
    body_polarity: int,
    clipped: set[int] | None = None,
    force_bad_crc: bool = False,
) -> bytes:
    clipped = clipped or set()
    mask = clip_mask_for(clipped, len(samples))
    header = (
        b"SLWS"
        + bytes([1])
        + network.encode("ascii")[:2].ljust(2, b"X")
        + station.encode("ascii")[:4].ljust(4, b"\x00")
        + epoch_sec.to_bytes(4, "little")
        + bytes([leap_marker])
        + len(samples).to_bytes(2, "little")
        + RATE.to_bytes(4, "little")
        + body_polarity.to_bytes(1, "little", signed=True)
        + len(mask).to_bytes(2, "little")
        + mask
        + bytes([len(picks)])
    )
    pick_bytes = b"".join(idx.to_bytes(2, "little") + bytes([phase]) for idx, phase in picks)
    sample_bytes = b"".join(s.to_bytes(2, "little", signed=True) for s in samples)
    body = header + pick_bytes + sample_bytes
    checksum = crc16(body)
    if force_bad_crc:
        checksum = (checksum + 23) & 0xFFFF
    return body + checksum.to_bytes(2, "little")


def sine_samples(n: int, amp: int = 800) -> list[int]:
    return [int(amp * ((i % 20) - 10) / 10) for i in range(n)]


samples_calm = sine_samples(400)
write_calm = encode_slws("NE", "ABC1", 1_700_000_000, 0, samples_calm, [(120, 0), (280, 1)], 1)

samples_leap = sine_samples(300)
write_leap = encode_slws("NE", "ABC1", 1_483_228_799, 1, samples_leap, [(150, 0)], 1)

samples_clip = sine_samples(350)
write_clip = encode_slws(
    "NE",
    "ABC1",
    1_700_010_000,
    0,
    samples_clip,
    [(100, 0)],
    1,
    clipped=set(range(90, 111)),
)

samples_flip = sine_samples(320)
write_flip = encode_slws("NE", "DEF2", 1_700_020_000, 0, samples_flip, [(140, 1)], 1)

samples_shuffle = sine_samples(360)
write_shuffle = encode_slws(
    "NE",
    "ABC1",
    1_700_030_000,
    0,
    samples_shuffle,
    [(300, 1), (80, 0), (200, 2)],
    1,
)

samples_invariant = sine_samples(200)
write_invariant = encode_slws("NE", "ABC1", 1_700_040_000, 0, samples_invariant, [(50, 0), (50, 1)], 1)

fixtures = {
    "calm-pwave": write_calm,
    "leap-edge": write_leap,
    "clip-heavy": write_clip,
    "polarity-flip": write_flip,
    "shuffle-picks": write_shuffle,
    "decode-invariant-fail": write_invariant,
}

for stem, blob in fixtures.items():
    (ROOT / f"{stem}.slws").write_bytes(blob)

(ROOT / "bad-crc.slws").write_bytes(
    encode_slws("NE", "ABC1", 1_700_050_000, 0, sine_samples(100), [(40, 0)], 1, force_bad_crc=True)
)

(POL / "NE.pol").write_text(
    json.dumps({"ABC1": 1, "DEF2": -1, "GHZ3": 1}, indent=2),
    encoding="utf-8",
)
(LEAP / "leap-epochs.json").write_text(
    json.dumps({"positive_leap_epochs": [1_483_228_800]}, indent=2),
    encoding="utf-8",
)

catalog = {
    "stems": list(fixtures.keys()) + ["bad-crc"],
    "bundled": [{"stem": stem, "path": f"/app/fixtures/slws/{stem}.slws"} for stem in fixtures]
    + [{"stem": "bad-crc", "path": "/app/fixtures/slws/bad-crc.slws"}],
}
(ROOT / "catalog.json").write_text(json.dumps(catalog, indent=2), encoding="utf-8")

TB3 = Path("/app/tb3-bundle")
TB3.mkdir(parents=True, exist_ok=True)
(TB3 / "leap-epochs.json").write_text(
    json.dumps({"positive_leap_epochs": [1_262_304_000]}, indent=2),
    encoding="utf-8",
)
(TB3 / "HV.pol").write_text(json.dumps({"GHZ3": -1}, indent=2), encoding="utf-8")
tb3_leap = encode_slws("NE", "ABC1", 1_262_303_999, 1, sine_samples(250), [(125, 0)], 1)
(TB3 / "tb3-leap.slws").write_bytes(tb3_leap)
tb3_polarity = encode_slws("HV", "GHZ3", 1_700_100_000, 0, sine_samples(280), [(160, 1)], 1)
(TB3 / "tb3-polarity.slws").write_bytes(tb3_polarity)
(TB3 / "tb3-shuffle.slws").write_bytes(write_shuffle)
(TB3 / "tb3-invariant-fail.slws").write_bytes(write_invariant)
print(f"generated {len(catalog['stems'])} fixtures")
