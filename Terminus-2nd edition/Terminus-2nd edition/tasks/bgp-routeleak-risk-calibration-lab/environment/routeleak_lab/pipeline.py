"""End-to-end evaluation pipeline."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from routeleak_lab.features import FEATURE_NAMES, extract_features
from routeleak_lab.metrics import brier_score, confusion, ece_score
from routeleak_lab.normalize import standardize
from routeleak_lab.report import audit_digest, write_report, write_snapshot
from routeleak_lab.score import score_rows
from routeleak_lab.split import assign_splits
from routeleak_lab.threshold import select_threshold


def load_experiment(exp_dir: Path) -> tuple[list[dict[str, Any]], dict[str, str], dict[str, Any]]:
    examples = []
    with (exp_dir / "examples.jsonl").open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                examples.append(json.loads(line))
    relationships = json.loads((exp_dir / "relationships.json").read_text(encoding="utf-8"))
    model = json.loads((exp_dir / "model.json").read_text(encoding="utf-8"))
    return examples, relationships, model


def evaluate_experiment(
    exp_dir: Path,
    *,
    experiment: str,
    run_id: str,
    feature_scale: float,
    snapshot_path: Path,
    report_path: Path,
) -> dict[str, Any]:
    examples, relationships, model = load_experiment(exp_dir)
    splits = assign_splits(examples)
    raw_features = [extract_features(ex, relationships) for ex in examples]
    std_features = standardize(raw_features, splits, feature_scale)
    scores = score_rows(std_features, model)

    val_scores = [s for s, sp in zip(scores, splits) if sp == "validation"]
    val_labels = [int(ex["label"]) for ex, sp in zip(examples, splits) if sp == "validation"]
    threshold, val_fbeta = select_threshold(val_scores, val_labels)

    rows = []
    for ex, sp, sc in zip(examples, splits, scores):
        pred = 1 if sc >= threshold else 0
        rows.append(
            {
                "example_id": ex["example_id"],
                "peer_group": ex["peer_group"],
                "split": sp,
                "label": int(ex["label"]),
                "score": float(sc),
                "predicted": pred,
            }
        )

    test_scores = [r["score"] for r in rows if r["split"] == "test"]
    test_labels = [r["label"] for r in rows if r["split"] == "test"]
    conf = confusion(test_scores, test_labels, threshold)
    brier = brier_score(test_scores, test_labels)
    ece = ece_score(test_scores, test_labels)

    split_counts = {
        "train": sum(1 for s in splits if s == "train"),
        "validation": sum(1 for s in splits if s == "validation"),
        "test": sum(1 for s in splits if s == "test"),
    }
    snapshot = {
        "schema_version": 1,
        "run_id": run_id,
        "experiment": experiment,
        "feature_scale": feature_scale,
        "selected_threshold": threshold,
        "split_counts": split_counts,
        "rows": rows,
    }
    write_snapshot(snapshot_path, snapshot)

    report = {
        "schema_version": 1,
        "run_id": run_id,
        "experiment": experiment,
        "selected_threshold": threshold,
        "validation_fbeta": val_fbeta,
        "test_confusion": conf,
        "test_brier": brier,
        "test_ece": ece,
        "feature_names": list(model.get("feature_names") or FEATURE_NAMES),
        "audit_digest": audit_digest(rows),
    }
    write_report(report_path, report)
    return report
