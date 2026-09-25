"""F-beta threshold search (broken baseline)."""
from __future__ import annotations


def fbeta(precision: float, recall: float, beta: float = 1.5) -> float:
    b2 = beta * beta
    denom = b2 * precision + recall
    if denom <= 1e-12:
        return 0.0
    return (1.0 + b2) * precision * recall / denom


def select_threshold(scores: list[float], labels: list[int]) -> tuple[float, float]:
    best_t = 0.5
    best_f = -1.0
    best_rec = -1.0
    for i in range(1, 20):
        t = i * 0.05
        tp = fp = fn = 0
        for s, y in zip(scores, labels):
            # broken: exclusive >
            pred = 1 if s > t else 0
            if pred == 1 and y == 1:
                tp += 1
            elif pred == 1 and y == 0:
                fp += 1
            elif pred == 0 and y == 1:
                fn += 1
        precision = tp / max(tp + fp, 1)
        recall = tp / max(tp + fn, 1)
        fb = fbeta(precision, recall)
        # broken: prefer higher threshold on ties
        if fb > best_f + 1e-15 or (
            abs(fb - best_f) <= 1e-15 and (t > best_t or (t == best_t and recall > best_rec))
        ):
            best_f = fb
            best_t = t
            best_rec = recall
    return best_t, best_f
