#!/usr/bin/env bash
set -euo pipefail
cd /solution

cat > /app/routeleak_lab/features.py <<'EOF_FEATURES'
"""AS-path and relationship feature extraction."""
from __future__ import annotations

from typing import Any


FEATURE_NAMES = [
    "path_len",
    "origin_asn",
    "private_origin",
    "reserved_hop",
    "unique_asn_ratio",
    "valley_count",
    "peer_peer_transit",
    "first_hop_customer",
]


def _is_private(asn: int) -> bool:
    return 64512 <= asn <= 65534


def _is_reserved(asn: int) -> bool:
    return 64496 <= asn <= 64511


def extract_features(example: dict[str, Any], relationships: dict[str, str]) -> list[float]:
    path = list(example.get("as_path") or [])
    path_len = float(len(path))
    origin = float(path[-1]) if path else 0.0
    private_origin = 1.0 if path and _is_private(path[-1]) else 0.0
    reserved_hop = 1.0 if any(_is_reserved(a) for a in path) else 0.0
    unique_asn_ratio = (len(set(path)) / path_len) if path_len > 0 else 0.0

    valley = 0.0
    peer_peer = 0.0
    for i in range(len(path) - 1):
        a, b = path[i], path[i + 1]
        role = relationships.get(f"{a}|{b}")
        if role == "peer":
            peer_peer = 1.0
        if i + 2 < len(path):
            c = path[i + 2]
            if role == "provider" and relationships.get(f"{b}|{c}") == "customer":
                valley += 1.0

    first_hop_customer = 0.0
    if len(path) >= 2 and relationships.get(f"{path[0]}|{path[1]}") == "customer":
        first_hop_customer = 1.0

    return [
        path_len,
        origin,
        private_origin,
        reserved_hop,
        unique_asn_ratio,
        valley,
        peer_peer,
        first_hop_customer,
    ]
EOF_FEATURES

cat > /app/routeleak_lab/normalize.py <<'EOF_NORMALIZE'
"""Feature standardization."""
from __future__ import annotations


def standardize(
    feature_rows: list[list[float]],
    split_roles: list[str],
    feature_scale: float,
) -> list[list[float]]:
    if not feature_rows:
        return []
    dim = len(feature_rows[0])
    train_rows = [row for row, role in zip(feature_rows, split_roles) if role == "train"]
    if not train_rows:
        train_rows = list(feature_rows)
    n = len(train_rows)
    means = []
    stds = []
    for j in range(dim):
        col = [row[j] for row in train_rows]
        mu = sum(col) / max(n, 1)
        var = sum((x - mu) ** 2 for x in col) / max(n, 1)
        means.append(mu)
        stds.append(var ** 0.5)
    out = []
    for row in feature_rows:
        scaled = []
        for j, x in enumerate(row):
            denom = stds[j] if stds[j] > 1e-8 else 1e-8
            scaled.append(((x - means[j]) / denom) * feature_scale)
        out.append(scaled)
    return out
EOF_NORMALIZE

cat > /app/routeleak_lab/score.py <<'EOF_SCORE'
"""Linear scoring and sigmoid."""
from __future__ import annotations

import math
from typing import Any


def logit(features: list[float], weights: list[float], bias: float) -> float:
    return bias + sum(w * x for w, x in zip(weights, features))


def sigmoid(z: float) -> float:
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    ez = math.exp(z)
    return ez / (1.0 + ez)


def score_rows(
    feature_rows: list[list[float]],
    model: dict[str, Any],
) -> list[float]:
    weights = list(model["weights"])
    bias = float(model["bias"])
    return [sigmoid(logit(row, weights, bias)) for row in feature_rows]
EOF_SCORE

cat > /app/routeleak_lab/split.py <<'EOF_SPLIT'
"""Group-aware holdout split."""
from __future__ import annotations

from typing import Any


def assign_splits(examples: list[dict[str, Any]]) -> list[str]:
    groups = sorted({ex["peer_group"] for ex in examples})
    role_by_group: dict[str, str] = {}
    for i, g in enumerate(groups):
        r = i % 3
        role_by_group[g] = "train" if r == 0 else "validation" if r == 1 else "test"
    return [role_by_group[ex["peer_group"]] for ex in examples]
EOF_SPLIT

cat > /app/routeleak_lab/threshold.py <<'EOF_THRESHOLD'
"""F-beta threshold search."""
from __future__ import annotations


def fbeta(precision: float, recall: float, beta: float = 1.5) -> float:
    b2 = beta * beta
    denom = b2 * precision + recall
    if denom <= 1e-12:
        return 0.0
    return (1.0 + b2) * precision * recall / denom


def select_threshold(scores: list[float], labels: list[int]) -> tuple[float, float]:
    best_t = 0.05
    best_f = -1.0
    best_rec = -1.0
    for i in range(1, 20):
        t = i * 0.05
        tp = fp = fn = 0
        for s, y in zip(scores, labels):
            pred = 1 if s >= t else 0
            if pred == 1 and y == 1:
                tp += 1
            elif pred == 1 and y == 0:
                fp += 1
            elif pred == 0 and y == 1:
                fn += 1
        precision = tp / max(tp + fp, 1)
        recall = tp / max(tp + fn, 1)
        fb = fbeta(precision, recall)
        better = False
        if fb > best_f + 1e-15:
            better = True
        elif abs(fb - best_f) <= 1e-15:
            if t < best_t:
                better = True
            elif t == best_t and recall > best_rec:
                better = True
        if better:
            best_f = fb
            best_t = t
            best_rec = recall
    return best_t, best_f
EOF_THRESHOLD

cat > /app/routeleak_lab/metrics.py <<'EOF_METRICS'
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
EOF_METRICS

cat > /app/routeleak_lab/report.py <<'EOF_REPORT'
"""Snapshot and sealed model-card report."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def audit_digest(rows: list[dict[str, Any]]) -> str:
    lines = [
        f"{r['example_id']}|{r['split']}|{r['label']}|{r['score']:.6f}|{r['predicted']}"
        for r in rows
    ]
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def write_snapshot(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
EOF_REPORT

bash /app/scripts/rebuild-routeleaklab.sh
/usr/local/bin/routeleaklab evaluate --experiment basic-leak --run-id oracle-smoke --report /app/output/routeleak_eval_report.json
test -s /app/state/eval-snapshot.json
test -s /app/output/routeleak_eval_report.json
