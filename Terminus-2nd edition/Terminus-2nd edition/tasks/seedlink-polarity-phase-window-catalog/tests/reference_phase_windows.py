"""Independent reference for SLWS waveform snippets and phase-window catalogs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

P_PRE_US = 2_000_000
P_POST_US = 4_000_000
S_PRE_US = 3_000_000
S_POST_US = 5_000_000
X_PRE_US = 1_000_000
X_POST_US = 1_000_000
STAGING_VERSION = 1


def crc16(data: bytes) -> int:
    return sum(data) & 0xFFFF


def phase_label(code: int) -> str:
    return {0: "P", 1: "S", 2: "X"}.get(code, "?")


def window_bounds(code: int) -> tuple[int, int]:
    if code == 0:
        return P_PRE_US, P_POST_US
    if code == 1:
        return S_PRE_US, S_POST_US
    return X_PRE_US, X_POST_US


def polarity_label(effective: int, signed_sample: int) -> str:
    sign = effective * signed_sample
    if sign > 0:
        return "up"
    if sign < 0:
        return "down"
    return "unknown"


def load_polarity_sheet(network: str, config_root: Path = Path("/app/config/polarity")) -> dict[str, int]:
    path = config_root / f"{network}.pol"
    if not path.is_file():
        return {}
    return {k: int(v) for k, v in json.loads(path.read_text(encoding="utf-8")).items()}


def load_leap_epochs(leap_root: Path | None = None) -> set[int]:
    if leap_root is None:
        leap_root = Path("/app/config/leap")
    path = leap_root / "leap-epochs.json"
    if not path.is_file():
        return set()
    data = json.loads(path.read_text(encoding="utf-8"))
    return {int(x) for x in data.get("positive_leap_epochs", [])}


def parse_slws(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    if len(raw) < 30:
        raise ValueError("too short")
    if raw[:4] != b"SLWS":
        raise ValueError("bad magic")
    if raw[4] != 1:
        raise ValueError("bad version")
    network = raw[5:7].decode("ascii")
    station = raw[7:11].decode("ascii").rstrip("\x00")
    epoch_sec = int.from_bytes(raw[11:15], "little")
    leap_marker = raw[15]
    sample_count = int.from_bytes(raw[16:18], "little")
    rate_mhz = int.from_bytes(raw[18:22], "little")
    body_polarity = int.from_bytes(raw[22:23], "little", signed=True)
    mask_len = int.from_bytes(raw[23:25], "little")
    off = 25
    clip_mask = raw[off : off + mask_len]
    off += mask_len
    pick_count = raw[off]
    off += 1
    picks: list[dict[str, int]] = []
    for _ in range(pick_count):
        sample_idx = int.from_bytes(raw[off : off + 2], "little")
        phase_code = raw[off + 2]
        picks.append({"sample_idx": sample_idx, "phase_code": phase_code})
        off += 3
    samples: list[int] = []
    for i in range(sample_count):
        samples.append(int.from_bytes(raw[off : off + 2], "little", signed=True))
        off += 2
    expected_crc = int.from_bytes(raw[off : off + 2], "little")
    actual_crc = crc16(raw[:off])
    if expected_crc != actual_crc:
        raise ValueError("crc mismatch")
    return {
        "network": network,
        "station": station,
        "epoch_sec": epoch_sec,
        "leap_marker": leap_marker,
        "sample_count": sample_count,
        "rate_mhz": rate_mhz,
        "body_polarity": body_polarity,
        "clip_mask": clip_mask,
        "picks": picks,
        "samples": samples,
    }


def clip_bit(mask: bytes, idx: int) -> bool:
    byte = idx // 8
    bit = idx % 8
    if byte >= len(mask):
        return False
    return ((mask[byte] >> bit) & 1) == 1


def leap_adjust_us(epoch_sec: int, leap_marker: int, leap_epochs: set[int]) -> int:
    if leap_marker != 1:
        return 0
    if epoch_sec in leap_epochs or (epoch_sec + 1) in leap_epochs:
        return 1_000_000
    return 0


def sample_period_us(rate_mhz: int) -> int:
    return (1_000_000 * 1000) // rate_mhz


def effective_polarity(
    network: str,
    station: str,
    body_polarity: int,
    config_root: Path = Path("/app/config/polarity"),
) -> int:
    sheet = load_polarity_sheet(network, config_root)
    if station in sheet:
        return sheet[station]
    return body_polarity


def pick_center_us(parsed: dict[str, Any], pick: dict[str, int], leap_epochs: set[int]) -> int:
    period = sample_period_us(parsed["rate_mhz"])
    base = parsed["epoch_sec"] * 1_000_000 + pick["sample_idx"] * period
    return base + leap_adjust_us(parsed["epoch_sec"], parsed["leap_marker"], leap_epochs)


def window_sample_range(parsed: dict[str, Any], pick: dict[str, int], leap_epochs: set[int]) -> tuple[int, int]:
    center = pick_center_us(parsed, pick, leap_epochs)
    pre, post = window_bounds(pick["phase_code"])
    period = sample_period_us(parsed["rate_mhz"])
    start_us = center - pre
    end_us = center + post
    first = max(0, int((start_us - parsed["epoch_sec"] * 1_000_000) // period))
    last = min(parsed["sample_count"] - 1, int((end_us - parsed["epoch_sec"] * 1_000_000) // period))
    return first, max(first, last)


def clipped_fraction(parsed: dict[str, Any], pick: dict[str, int], leap_epochs: set[int]) -> float:
    first, last = window_sample_range(parsed, pick, leap_epochs)
    if last < first:
        return 0.0
    total = last - first + 1
    clipped = sum(1 for i in range(first, last + 1) if clip_bit(parsed["clip_mask"], i))
    return round(clipped / total, 4)


def peak_amplitude(parsed: dict[str, Any], pick: dict[str, int], leap_epochs: set[int]) -> int:
    first, last = window_sample_range(parsed, pick, leap_epochs)
    window = parsed["samples"][first : last + 1]
    if not window:
        return 0
    return max(window, key=abs)


def invariant_ok(picks: list[dict[str, int]], sample_count: int) -> bool:
    if not picks:
        return True
    seen: set[int] = set()
    for pick in picks:
        if pick["sample_idx"] >= sample_count:
            return False
        if pick["sample_idx"] in seen:
            return False
        seen.add(pick["sample_idx"])
    return True


def digest(picks: list[dict[str, int]], effective_polarity: int) -> str:
    rows = sorted(picks, key=lambda row: row["sample_idx"])
    acc = 1469598103934665603
    for row in rows:
        acc ^= row["sample_idx"]
        acc = (acc * 1099511628211) & 0xFFFFFFFFFFFFFFFF
        acc ^= row["phase_code"]
        acc = (acc * 1099511628211) & 0xFFFFFFFFFFFFFFFF
        acc ^= effective_polarity & 0xFF
        acc = (acc * 1099511628211) & 0xFFFFFFFFFFFFFFFF
    return f"{acc:016x}"


def expected_stage(
    path: Path,
    stem: str,
    config_root: Path = Path("/app/config/polarity"),
    leap_root: Path | None = None,
) -> dict[str, Any]:
    parsed = parse_slws(path)
    eff = effective_polarity(parsed["network"], parsed["station"], parsed["body_polarity"], config_root)
    picks_sorted = sorted(parsed["picks"], key=lambda row: row["sample_idx"])
    return {
        "source": str(path),
        "stem": stem,
        "staging_version": STAGING_VERSION,
        "network": parsed["network"],
        "station": parsed["station"],
        "epoch_sec": parsed["epoch_sec"],
        "leap_marker": parsed["leap_marker"],
        "sample_count": parsed["sample_count"],
        "rate_mhz": parsed["rate_mhz"],
        "effective_polarity": eff,
        "picks": picks_sorted,
        "digest": digest(parsed["picks"], eff),
    }


def expected_export(
    path: Path,
    stem: str,
    config_root: Path = Path("/app/config/polarity"),
    leap_root: Path | None = None,
) -> dict[str, Any]:
    stage = expected_stage(path, stem, config_root, leap_root)
    parsed = parse_slws(path)
    leap_epochs = load_leap_epochs(leap_root)
    windows: list[dict[str, Any]] = []
    for pick in stage["picks"]:
        center = pick_center_us(parsed, pick, leap_epochs)
        pre, post = window_bounds(pick["phase_code"])
        peak = peak_amplitude(parsed, pick, leap_epochs)
        eff = stage["effective_polarity"]
        windows.append(
            {
                "phase": phase_label(pick["phase_code"]),
                "pick_sample": pick["sample_idx"],
                "center_us": center,
                "start_us": center - pre,
                "end_us": center + post,
                "polarity": polarity_label(eff, peak),
                "clipped_fraction": clipped_fraction(parsed, pick, leap_epochs),
                "peak_amplitude": peak,
                "invariant_ok": invariant_ok(stage["picks"], parsed["sample_count"]),
            }
        )
    return {
        "schema": "seedlink-phase-catalog/1",
        "source": stage["source"],
        "stem": stage["stem"],
        "staging_version": STAGING_VERSION,
        "network": stage["network"],
        "station": stage["station"],
        "digest": stage["digest"],
        "window_count": len(windows),
        "windows": windows,
    }


def load_catalog(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
