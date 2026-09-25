"""Independent reference contract for routeleaklab evaluation."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
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


def is_private(asn: int) -> bool:
    return 64512 <= asn <= 65534


def is_reserved(asn: int) -> bool:
    return 64496 <= asn <= 64511


def extract_features(example: dict[str, Any], relationships: dict[str, str]) -> list[float]:
    path = list(example.get("as_path") or [])
    path_len = float(len(path))
    origin = float(path[-1]) if path else 0.0
    private_origin = 1.0 if path and is_private(path[-1]) else 0.0
    reserved_hop = 1.0 if any(is_reserved(asn) for asn in path) else 0.0
    unique_ratio = len(set(path)) / path_len if path_len else 0.0
    valleys = 0.0
    peer_transit = 0.0
    for index in range(len(path) - 1):
        role = relationships.get(f"{path[index]}|{path[index + 1]}")
        if role == "peer":
            peer_transit = 1.0
        if index + 2 < len(path) and role == "provider":
            if relationships.get(f"{path[index + 1]}|{path[index + 2]}") == "customer":
                valleys += 1.0
    first_hop_customer = (
        1.0
        if len(path) >= 2 and relationships.get(f"{path[0]}|{path[1]}") == "customer"
        else 0.0
    )
    return [
        path_len,
        origin,
        private_origin,
        reserved_hop,
        unique_ratio,
        valleys,
        peer_transit,
        first_hop_customer,
    ]


def assign_splits(examples: list[dict[str, Any]]) -> list[str]:
    groups = sorted({str(example["peer_group"]) for example in examples})
    roles = ("train", "validation", "test")
    by_group = {group: roles[index % 3] for index, group in enumerate(groups)}
    return [by_group[str(example["peer_group"])] for example in examples]


def standardize(
    rows: list[list[float]], splits: list[str], feature_scale: float
) -> list[list[float]]:
    if not rows:
        return []
    train_rows = [row for row, split in zip(rows, splits) if split == "train"] or rows
    count = len(train_rows)
    means = [sum(row[column] for row in train_rows) / count for column in range(len(rows[0]))]
    stds = [
        (sum((row[column] - means[column]) ** 2 for row in train_rows) / count) ** 0.5
        for column in range(len(rows[0]))
    ]
    return [
        [
            ((value - means[column]) / max(stds[column], 1e-8)) * feature_scale
            for column, value in enumerate(row)
        ]
        for row in rows
    ]


def sigmoid(logit: float) -> float:
    if logit >= 0:
        return 1.0 / (1.0 + math.exp(-logit))
    exp_logit = math.exp(logit)
    return exp_logit / (1.0 + exp_logit)


def score_rows(rows: list[list[float]], model: dict[str, Any]) -> list[float]:
    weights = [float(weight) for weight in model["weights"]]
    bias = float(model["bias"])
    return [sigmoid(bias + sum(weight * value for weight, value in zip(weights, row))) for row in rows]


def fbeta(precision: float, recall: float, beta: float = 1.5) -> float:
    beta_squared = beta * beta
    return (1 + beta_squared) * precision * recall / max(
        beta_squared * precision + recall, 1e-12
    )


def select_threshold(scores: list[float], labels: list[int]) -> tuple[float, float]:
    best_threshold, best_score, best_recall = 0.05, -1.0, -1.0
    for step in range(1, 20):
        threshold = step * 0.05
        predictions = [score >= threshold for score in scores]
        true_positive = sum(prediction and label == 1 for prediction, label in zip(predictions, labels))
        false_positive = sum(prediction and label == 0 for prediction, label in zip(predictions, labels))
        false_negative = sum(not prediction and label == 1 for prediction, label in zip(predictions, labels))
        precision = true_positive / max(true_positive + false_positive, 1)
        recall = true_positive / max(true_positive + false_negative, 1)
        value = fbeta(precision, recall)
        if (
            value > best_score + 1e-15
            or (
                abs(value - best_score) <= 1e-15
                and (threshold < best_threshold or (threshold == best_threshold and recall > best_recall))
            )
        ):
            best_threshold, best_score, best_recall = threshold, value, recall
    return best_threshold, best_score


def confusion(scores: list[float], labels: list[int], threshold: float) -> dict[str, int]:
    result = {"tp": 0, "fp": 0, "tn": 0, "fn": 0}
    for score, label in zip(scores, labels):
        key = "tp" if score >= threshold and label else "fp" if score >= threshold else "tn" if not label else "fn"
        result[key] += 1
    return result


def brier_score(scores: list[float], labels: list[int]) -> float:
    return sum((score - label) ** 2 for score, label in zip(scores, labels)) / len(scores) if scores else 0.0


def ece_score(scores: list[float], labels: list[int], n_bins: int = 10) -> float:
    if not scores:
        return 0.0
    bins: list[list[tuple[float, int]]] = [[] for _ in range(n_bins)]
    for score, label in zip(scores, labels):
        bins[min(int(score * n_bins), n_bins - 1)].append((score, label))
    return sum(
        abs(sum(score for score, _ in bucket) / len(bucket) - sum(label for _, label in bucket) / len(bucket))
        * len(bucket) / len(scores)
        for bucket in bins
        if bucket
    )


def audit_digest(rows: list[dict[str, Any]]) -> str:
    lines = [
        f"{row['example_id']}|{row['split']}|{row['label']}|{row['score']:.6f}|{row['predicted']}"
        for row in rows
    ]
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def load_experiment(exp_dir: Path) -> tuple[list[dict[str, Any]], dict[str, str], dict[str, Any]]:
    examples = [
        json.loads(line)
        for line in (exp_dir / "examples.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    relationships = json.loads((exp_dir / "relationships.json").read_text(encoding="utf-8"))
    model = json.loads((exp_dir / "model.json").read_text(encoding="utf-8"))
    return examples, relationships, model


def expected_report(exp_dir: Path, *, experiment: str | None = None, run_id: str = "default", feature_scale: float = 1.0) -> dict[str, Any]:
    examples, relationships, model = load_experiment(exp_dir)
    splits = assign_splits(examples)
    features = standardize(
        [extract_features(example, relationships) for example in examples], splits, feature_scale
    )
    scores = score_rows(features, model)
    validation = [(score, int(example["label"])) for score, example, split in zip(scores, examples, splits) if split == "validation"]
    threshold, validation_fbeta = select_threshold(
        [score for score, _ in validation], [label for _, label in validation]
    )
    rows = [
        {
            "example_id": example["example_id"],
            "peer_group": example["peer_group"],
            "split": split,
            "label": int(example["label"]),
            "score": score,
            "predicted": int(score >= threshold),
        }
        for example, split, score in zip(examples, splits, scores)
    ]
    test = [row for row in rows if row["split"] == "test"]
    return {
        "schema_version": 1,
        "run_id": run_id,
        "experiment": experiment or exp_dir.name,
        "selected_threshold": threshold,
        "validation_fbeta": validation_fbeta,
        "test_confusion": confusion([row["score"] for row in test], [row["label"] for row in test], threshold),
        "test_brier": brier_score([row["score"] for row in test], [row["label"] for row in test]),
        "test_ece": ece_score([row["score"] for row in test], [row["label"] for row in test]),
        "feature_names": list(model.get("feature_names") or FEATURE_NAMES),
        "audit_digest": audit_digest(rows),
    }


reference_eval = expected_report
