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
    # broken: uses every row, not train-only
    means = []
    stds = []
    n = len(feature_rows)
    for j in range(dim):
        col = [row[j] for row in feature_rows]
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
    _ = split_roles  # unused intentionally (broken)
    return out
