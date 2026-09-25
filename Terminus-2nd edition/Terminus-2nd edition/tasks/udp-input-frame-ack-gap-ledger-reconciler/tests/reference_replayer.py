"""Independent Python reference for udpctl staging and export parity."""

from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path
from typing import Any

MASK64 = (1 << 64) - 1
MASK32 = (1 << 32) - 1


def _u32(x: int) -> int:
    return x & MASK32


def _i64(x: int) -> int:
    x &= MASK64
    if x >= (1 << 63):
        x -= 1 << 64
    return x


def _seq_before(a: int, b: int) -> bool:
    diff = _u32(b - a)
    return diff != 0 and diff < 0x80000000


def _seed_client_id(base: int, seed: int) -> int:
    return _u32(base ^ _u32(_u32(seed) * 0x9E3779B9))


def _mutate_raw(raw: bytes, seed: int) -> bytes:
    out = bytearray(raw)
    if len(out) >= 12:
        seq = struct.unpack_from("<I", out, 8)[0]
        bump = _u32(seed * 17)
        struct.pack_into("<I", out, 8, _u32(seq + bump))
    if len(out) >= 8:
        cid = struct.unpack_from("<I", out, 4)[0]
        struct.pack_into("<I", out, 4, _seed_client_id(cid, seed))
    return bytes(out)


def _parse_frame(raw: bytes) -> dict[str, Any]:
    if len(raw) < 29 or raw[0:4] != b"UDPI":
        raise ValueError("bad frame")
    client_id, frame_seq, ack_base = struct.unpack_from("<III", raw, 4)
    loss_mask = struct.unpack_from("<Q", raw, 16)[0]
    base_tick = struct.unpack_from("<I", raw, 24)[0]
    num_inputs = raw[28]
    need = 29 + num_inputs * 5
    if len(raw) < need or num_inputs > 64:
        raise ValueError("short frame")
    inputs = []
    off = 29
    for _ in range(num_inputs):
        tick_offset, opcode, value = struct.unpack_from("<Hbh", raw, off)
        inputs.append({"tick_offset": tick_offset, "opcode": opcode, "value": value})
        off += 5
    return {
        "client_id": client_id,
        "frame_seq": frame_seq,
        "ack_base": ack_base,
        "loss_mask": loss_mask,
        "base_tick": base_tick,
        "inputs": inputs,
    }


def _gaps_from_mask(ack_base: int, mask: int) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    start: int | None = None
    for bit in range(64):
        lost = ((mask >> bit) & 1) == 1
        seq = _u32(ack_base - 1 - bit)
        if lost:
            if start is None:
                start = seq
        elif start is not None:
            prev = _u32(ack_base - 1 - bit + 1)
            out.append((start, prev))
            start = None
    if start is not None:
        out.append((start, _u32(ack_base - 64)))
    return out


def _recompute_playhead(seen: set[int]) -> tuple[int, list[tuple[int, int]]]:
    if not seen:
        return 0, []
    origins = [s for s in seen if _u32(s - 1) not in seen]

    def origin_key(a: int) -> tuple[int, int]:
        return (sum(1 for b in origins if _seq_before(b, a)), a)

    origins.sort(key=origin_key)
    origin = origins[0]
    playhead = origin
    while _u32(playhead + 1) in seen:
        playhead = _u32(playhead + 1)

    gaps: list[tuple[int, int]] = []
    cursor = origin
    gap_start: int | None = None
    while True:
        if cursor in seen:
            if gap_start is not None:
                gaps.append((gap_start, _u32(cursor - 1)))
                gap_start = None
        elif gap_start is None:
            gap_start = cursor
        if cursor == playhead:
            break
        cursor = _u32(cursor + 1)
    if gap_start is not None:
        gaps.append((gap_start, playhead))
    return playhead, gaps


def _apply_input(sim: dict[str, Any], tick: int, opcode: int, value: int) -> None:
    sim["inputs_applied"] += 1
    sim["tick"] = max(sim["tick"], tick)
    if opcode == 0:
        sim["accumulator"] = _i64(sim["accumulator"] + value)
    elif opcode == 1:
        # Rust: mix ^= (tick as u64).wrapping_mul(value as u64) with i16→u64 sign extend
        v = value & MASK64 if value >= 0 else ((value + (1 << 64)) & MASK64)
        sim["mix"] = (sim["mix"] ^ ((tick * v) & MASK64)) & MASK64
    elif opcode == 2:
        mult = max(value, 1)
        sim["accumulator"] = _i64(sim["accumulator"] * mult)
    else:
        v = value & MASK64 if value >= 0 else ((value + (1 << 64)) & MASK64)
        sim["mix"] = (sim["mix"] + v) & MASK64


def _hash_state(sim: dict[str, Any], client_id: int, seed: int) -> str:
    payload = (
        f"{client_id}:{seed}:{sim['tick']}:{sim['accumulator']}:"
        f"{sim['mix']}:{sim['inputs_applied']}"
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def _merge_ranges_u32(raw: list[tuple[int, int]]) -> list[dict[str, int]]:
    if not raw:
        return []
    pairs = sorted(((_u32(s), _u32(e)) for s, e in raw), key=lambda p: (p[0], p[1]))
    out: list[dict[str, int]] = []
    start, end = pairs[0]
    for s, e in pairs[1:]:
        wrap_next = _u32(end + 1)
        if s <= wrap_next:
            end = max(end, e)
        else:
            out.append({"start": start, "end": end})
            start, end = s, e
    out.append({"start": start, "end": end})
    return out


def _run_ingest(bundle_path: Path, seed: int) -> dict[str, Any]:
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    seen: set[int] = set()
    gaps: list[tuple[int, int]] = []
    peer_loss: list[tuple[int, int]] = []
    duplicate_acks = 0
    frames_received = 0
    playhead = 0
    client_id = 0
    sim: dict[str, Any] = {"tick": 0, "accumulator": 0, "mix": 0, "inputs_applied": 0}

    for pkt in bundle["packets"]:
        raw = _mutate_raw(bytes.fromhex(pkt["hex"].strip()), seed)
        frame = _parse_frame(raw)
        client_id = frame["client_id"]
        frames_received += 1
        seq = frame["frame_seq"]
        if seq in seen:
            duplicate_acks += 1
        else:
            seen.add(seq)
        playhead, gaps = _recompute_playhead(seen)
        peer_loss.extend(_gaps_from_mask(frame["ack_base"], frame["loss_mask"]))
        for inp in frame["inputs"]:
            tick = frame["base_tick"] + inp["tick_offset"]
            _apply_input(sim, tick, inp["opcode"], inp["value"])

    return {
        "bundle_id": bundle["bundle_id"],
        "seed": seed,
        "client_id": client_id,
        "ledger_raw": {
            "playhead": playhead,
            "gaps_raw": [list(t) for t in gaps],
            "peer_loss_raw": [list(t) for t in peer_loss],
            "duplicate_acks": duplicate_acks,
            "frames_received": frames_received,
        },
        "sim": sim,
    }


def reference_staging(bundle_path: Path, seed: int) -> dict[str, Any]:
    return _run_ingest(Path(bundle_path), seed)


def reference_replay(bundle_path: Path, seed: int) -> dict[str, Any]:
    snap = _run_ingest(Path(bundle_path), seed)
    sim = snap["sim"]
    gaps_raw = [tuple(t) for t in snap["ledger_raw"]["gaps_raw"]]
    peer_raw = [tuple(t) for t in snap["ledger_raw"]["peer_loss_raw"]]
    return {
        "bundle_id": snap["bundle_id"],
        "seed": snap["seed"],
        "client_id": snap["client_id"],
        "state_hash": _hash_state(sim, snap["client_id"], seed),
        "ledger": {
            "playhead": snap["ledger_raw"]["playhead"],
            "gaps": _merge_ranges_u32(gaps_raw),
            "duplicate_acks": snap["ledger_raw"]["duplicate_acks"],
            "peer_loss_gaps": _merge_ranges_u32(peer_raw),
            "frames_received": snap["ledger_raw"]["frames_received"],
        },
        "sim": {
            "tick": sim["tick"],
            "accumulator": sim["accumulator"],
            "mix": sim["mix"],
            "inputs_applied": sim["inputs_applied"],
        },
    }
