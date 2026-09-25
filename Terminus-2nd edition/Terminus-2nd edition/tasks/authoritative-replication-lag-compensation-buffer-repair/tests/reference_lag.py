"""Independent EWMA lag and snapshot-merge reference helpers."""

from __future__ import annotations

EWMA_ALPHA = 0.25


def ewma_lag_us(samples: list[int]) -> int:
    """Return rounded EWMA lag estimate in microseconds."""
    if not samples:
        return 0
    estimate = float(samples[0])
    for sample in samples[1:]:
        estimate = EWMA_ALPHA * sample + (1.0 - EWMA_ALPHA) * estimate
    return round(estimate)


def merge_snapshot_rows(deltas: list[tuple[int, int, int]]) -> list[tuple[int, int]]:
    """Return (seq, cumulative_xor) rows with gap fill per snapshot-merge.md."""
    if not deltas:
        return []
    xor_by_seq = {seq: xor for seq, _base, xor in deltas}
    min_seq = min(xor_by_seq)
    max_seq = max(xor_by_seq)
    cumulative = 0
    rows: list[tuple[int, int]] = []
    for seq in range(min_seq, max_seq + 1):
        if seq in xor_by_seq:
            cumulative ^= xor_by_seq[seq]
        rows.append((seq, cumulative))
    return rows


def merged_state_hash(deltas: list[tuple[int, int, int]]) -> int:
    rows = merge_snapshot_rows(deltas)
    if not rows:
        return 0
    return rows[-1][1]
