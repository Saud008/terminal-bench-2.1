"""Independent CDC + merkle reference for verifier expected values."""

from __future__ import annotations

import base64
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

APP = Path("/app")
FIX = APP / "fixtures" / "binaries"


@dataclass
class Params:
    min_chunk: int
    max_chunk: int
    window: int
    mask: int
    target: int


@dataclass
class SimState:
    chunk_start: int
    window: list[int]
    offset: int
    chunks: list[dict[str, Any]]
    leaves: list[str]
    complete: bool


def params_for_seed(seed: str) -> Params:
    digest = hashlib.sha256(seed.encode()).digest()
    return Params(
        min_chunk=48 + (digest[0] % 32),
        max_chunk=2048 + (digest[1] % 512),
        window=32,
        mask=0x1FFF,
        target=digest[2] & 0x1FFF,
    )


def roll_hash(window: bytes) -> int:
    h = 0
    for b in window:
        h = ((h << 1) ^ b) & 0xFFFFFFFF
    return h


def content_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def chunk_id(seed: str, offset: int, data: bytes) -> str:
    payload = f"{seed}:{offset}:".encode() + data
    return hashlib.sha256(payload).hexdigest()[:16]


def merkle_root(leaves: list[str]) -> str:
    if not leaves:
        return hashlib.sha256(b"").hexdigest()
    level = leaves[:]
    while len(level) > 1:
        if len(level) % 2 == 1:
            level.append(level[-1])
        nxt: list[str] = []
        for i in range(0, len(level), 2):
            nxt.append(hashlib.sha256((level[i] + level[i + 1]).encode()).hexdigest())
        level = nxt
    return level[0]


def _push(window: list[int], b: int, window_size: int) -> None:
    window.append(b)
    if len(window) > window_size:
        del window[:-window_size]


def _feed(
    data: bytes,
    pos: int,
    seed: str,
    p: Params,
    chunk_start: int,
    window: list[int],
) -> tuple[int, list[int], dict[str, Any] | None]:
    _push(window, data[pos], p.window)
    chunk_len = pos - chunk_start + 1
    at_end = pos == len(data) - 1
    forced = chunk_len >= p.max_chunk
    boundary = (roll_hash(bytes(window)) & p.mask) == p.target and chunk_len >= p.min_chunk
    if (boundary or forced or at_end) and chunk_len > 0:
        chunk_data = data[chunk_start : pos + 1]
        rec = {
            "id": chunk_id(seed, chunk_start, chunk_data),
            "offset": chunk_start,
            "length": chunk_len,
            "hash": content_hash(chunk_data),
        }
        return pos + 1, window[:], rec
    return chunk_start, window, None


def fresh_state() -> SimState:
    return SimState(chunk_start=0, window=[], offset=0, chunks=[], leaves=[], complete=False)


def state_from_checkpoint(cp: dict[str, Any]) -> SimState:
    window_raw = b""
    if cp.get("window"):
        window_raw = base64.b64decode(cp["window"])
    return SimState(
        chunk_start=cp["chunk_start"],
        window=list(window_raw),
        offset=cp["offset"],
        chunks=list(cp.get("chunks", [])),
        leaves=list(cp.get("leaves", [])),
        complete=bool(cp.get("complete")),
    )


def checkpoint_from_state(state: SimState, source: str, seed: str) -> dict[str, Any]:
    window_b64 = ""
    if state.window:
        window_b64 = base64.b64encode(bytes(state.window)).decode("ascii")
    return {
        "source": source,
        "seed": seed,
        "offset": state.offset,
        "chunk_start": state.chunk_start,
        "window": window_b64,
        "chunks": state.chunks,
        "leaves": state.leaves,
        "complete": state.complete,
    }


def simulate_roll(
    data: bytes,
    seed: str,
    *,
    max_new_chunks: int = 0,
    initial: SimState | None = None,
) -> SimState:
    p = params_for_seed(seed)
    state = initial or fresh_state()
    new_chunks = 0
    for pos in range(state.offset, len(data)):
        chunk_start, window, rec = _feed(
            data,
            pos,
            seed,
            p,
            state.chunk_start,
            state.window,
        )
        state.chunk_start = chunk_start
        state.window = window
        if rec is not None:
            state.chunks.append(rec)
            state.leaves.append(rec["hash"])
            new_chunks += 1
            if max_new_chunks > 0 and new_chunks >= max_new_chunks:
                state.offset = pos + 1
                state.complete = False
                return state
    state.offset = len(data)
    state.complete = True
    return state


def split_all(data: bytes, seed: str, p: Params) -> list[dict[str, Any]]:
    state = simulate_roll(data, seed)
    return state.chunks


def reference_roll(data: bytes, seed: str, source: str) -> dict[str, Any]:
    p = params_for_seed(seed)
    chunks = split_all(data, seed, p)
    leaves = [c["hash"] for c in chunks]
    return {
        "source": source,
        "seed": seed,
        "bytes_total": len(data),
        "chunk_count": len(chunks),
        "merkle_root": merkle_root(leaves),
        "resumed": False,
        "chunks": chunks,
    }


def reference_phased_roll(
    data: bytes,
    seed: str,
    source: str,
    phase_limits: list[int],
) -> dict[str, Any]:
    state: SimState | None = None
    resumed = False
    for idx, limit in enumerate(phase_limits):
        state = simulate_roll(data, seed, max_new_chunks=limit, initial=state)
        if idx < len(phase_limits) - 1:
            resumed = True
            if state.complete:
                break
    assert state is not None
    report = {
        "source": source,
        "seed": seed,
        "bytes_total": len(data),
        "chunk_count": len(state.chunks),
        "merkle_root": merkle_root(state.leaves),
        "resumed": resumed,
        "chunks": state.chunks,
    }
    return report


def inject_byte(data: bytes, seed: str) -> bytes:
    if not data:
        return data
    digest = hashlib.sha256(f"inject:{seed}".encode()).digest()
    idx = digest[0] % len(data)
    buf = bytearray(data)
    buf[idx] ^= 0x01
    return bytes(buf)


def max_chunk_length(chunks: list[dict[str, Any]]) -> int:
    return max((c["length"] for c in chunks), default=0)


def craft_min_chunk_payload(seed: str, min_size: int = 301) -> bytes:
    """Build bytes where a boundary candidate appears before min_chunk is satisfied."""
    p = params_for_seed(seed)
    data: list[int] = []
    window: list[int] = []
    chunk_start = 0
    for attempt in range(8000):
        chunk_len = len(data) - chunk_start + 1
        chosen: int | None = None
        if chunk_len < p.min_chunk:
            for b in range(256):
                trial = window + [b]
                if len(trial) > p.window:
                    trial = trial[-p.window :]
                if (roll_hash(bytes(trial)) & p.mask) == p.target:
                    chosen = b
                    break
        if chosen is None:
            chosen = (attempt * 37) & 0xFF
        data.append(chosen)
        window.append(chosen)
        if len(window) > p.window:
            window = window[-p.window :]
        if len(data) >= min_size and first_boundary_before_min(bytes(data), seed) is not None:
            return bytes(data)
    raise RuntimeError(f"unable to craft min-chunk payload for seed {seed}")


def first_boundary_before_min(data: bytes, seed: str) -> int | None:
    """Return first byte index where boundary would fire before min_chunk, if any."""
    p = params_for_seed(seed)
    window: list[int] = []
    chunk_start = 0
    for pos, b in enumerate(data):
        _push(window, b, p.window)
        chunk_len = pos - chunk_start + 1
        boundary = (roll_hash(bytes(window)) & p.mask) == p.target
        if boundary and chunk_len < p.min_chunk:
            return pos
        at_end = pos == len(data) - 1
        forced = chunk_len >= p.max_chunk
        if (boundary and chunk_len >= p.min_chunk) or forced or at_end:
            chunk_start = pos + 1
    return None
