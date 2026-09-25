"""Confusion, Brier, ECE."""
from __future__ import annotations


def confusion(scores: list[float], labels: list[int], threshold: float) -> dict[str, int]:
    tp = fp = tn = fn = 0
    for s, y in zip(scores, labels):
        pred = 1 if s >= threshold else 0
        if pred == 1 and y == 1:
            tp += 1
        elif pred == 1 and y == 0:
            fp += 1
        elif pred == 0 and y == 0:
            tn += 1
        else:
            fn += 1
    return {"tp": tp, "fp": fp, "tn": tn, "fn": fn}


def brier_score(scores: list[float], labels: list[int]) -> float:
    if not scores:
        return 0.0
    return sum((s - y) ** 2 for s, y in zip(scores, labels)) / len(scores)


def ece_score(scores: list[float], labels: list[int], n_bins: int = 10) -> float:
    if not scores:
        return 0.0
    bins: list[list[tuple[float, int]]] = [[] for _ in range(n_bins)]
    for s, y in zip(scores, labels):
        idx = min(int(s * n_bins), n_bins - 1)
        if s >= 1.0:
            idx = n_bins - 1
        bins[idx].append((s, y))
    total = 0.0
    n = len(scores)
    for bucket in bins:
        if not bucket:
            continue
        ms = sum(p[0] for p in bucket) / len(bucket)
        my = sum(p[1] for p in bucket) / len(bucket)
        total += abs(ms - my) * (len(bucket) / n)
    return total
