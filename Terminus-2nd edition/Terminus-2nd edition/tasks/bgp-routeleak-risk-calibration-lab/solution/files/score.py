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
