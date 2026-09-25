"""Independent contract math for dbtsent manifest freshness verifier cases."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any


def _scope_id(seed: str, uid: str) -> str:
    x = 2166136261
    for b in (seed + ":" + uid).encode():
        x ^= b
        x = (x * 16777619) & 0xFFFFFFFF
    return f"{uid}-{x:08x}"


def _materialize(bundle: dict[str, Any], seed: str) -> dict[str, Any]:
    out = dict(bundle)
    out["models"] = []
    for m in bundle["models"]:
        out["models"].append(
            {
                "unique_id": _scope_id(seed, m["unique_id"]),
                "depends_on": [_scope_id(seed, d) for d in m.get("depends_on") or []],
                "enabled": m["enabled"],
                "last_built_at": m["last_built_at"],
            }
        )
    out["sources"] = []
    for s in bundle["sources"]:
        out["sources"].append(
            {
                "unique_id": _scope_id(seed, s["unique_id"]),
                "loaded_at": s["loaded_at"],
                "warn_after_minutes": s["warn_after_minutes"],
                "error_after_minutes": s["error_after_minutes"],
            }
        )
    out["exposures"] = []
    for e in bundle["exposures"]:
        out["exposures"].append(
            {
                "unique_id": _scope_id(seed, e["unique_id"]),
                "depends_on": [_scope_id(seed, d) for d in e.get("depends_on") or []],
            }
        )
    return out


def load_scoped_manifest(path: Path, seed: str) -> dict[str, Any]:
    bundle = json.loads(path.read_text(encoding="utf-8"))
    bundle["_materialized"] = _materialize(bundle, seed)
    return bundle


def _enabled_topo(models: list[dict[str, Any]]) -> list[str]:
    by_id = {m["unique_id"]: m for m in models}
    enabled_ids = sorted(m["unique_id"] for m in models if m["enabled"])
    visited: set[str] = set()
    out: list[str] = []

    def visit(node_id: str) -> None:
        if node_id in visited or node_id not in by_id:
            return
        visited.add(node_id)
        m = by_id[node_id]
        if not m["enabled"]:
            return
        for dep in m.get("depends_on") or []:
            if dep in by_id and by_id[dep]["enabled"]:
                visit(dep)
        out.append(node_id)

    for mid in enabled_ids:
        visit(mid)
    return out


def _freshness(sources: list[dict[str, Any]], evaluated_at: str) -> list[dict[str, Any]]:
    eval_dt = datetime.fromisoformat(evaluated_at.replace("Z", "+00:00"))
    bias = int(os.environ.get("TB3_FRESHNESS_BIAS_MINUTES", "0") or "0")
    rows: list[dict[str, Any]] = []
    for s in sources:
        loaded = datetime.fromisoformat(s["loaded_at"].replace("Z", "+00:00"))
        mins = int((eval_dt - loaded).total_seconds() // 60) + bias
        status = "ok"
        if mins > s["warn_after_minutes"]:
            status = "warn"
        if mins > s["error_after_minutes"]:
            status = "error"
        rows.append({"unique_id": s["unique_id"], "minutes_elapsed": mins, "status": status})
    return rows


def _exposure_closure(exposures: list[dict[str, Any]], models: list[dict[str, Any]]) -> dict[str, list[str]]:
    model_ids = {m["unique_id"] for m in models}
    by_id = {m["unique_id"]: m for m in models}

    def collect(start: str) -> set[str]:
        seen: set[str] = set()
        stack = [start]
        while stack:
            cur = stack.pop()
            if cur not in model_ids or cur in seen:
                continue
            seen.add(cur)
            for dep in by_id[cur].get("depends_on") or []:
                if dep in model_ids:
                    stack.append(dep)
        return seen

    out: dict[str, list[str]] = {}
    for e in exposures:
        refs: set[str] = set()
        for dep in e.get("depends_on") or []:
            if dep in model_ids:
                refs |= collect(dep)
        out[e["unique_id"]] = sorted(refs)
    return out


def _disabled_ref_ok(models: list[dict[str, Any]]) -> bool:
    enabled = {m["unique_id"] for m in models if m["enabled"]}
    disabled = {m["unique_id"] for m in models if not m["enabled"]}
    for m in models:
        if not m["enabled"]:
            continue
        for dep in m.get("depends_on") or []:
            if dep in disabled or (dep.startswith("model.") and dep not in enabled):
                return False
    return True


def _alerts(
    fresh: list[dict[str, Any]], models: list[dict[str, Any]], refs: dict[str, list[str]]
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    rank = {"error": 0, "warn": 1, "ok": 2}
    for f in fresh:
        if f["status"] == "ok":
            continue
        rows.append(
            {
                "alert_code": "SOURCE_STALE",
                "severity": f["status"],
                "subject_id": f["unique_id"],
                "message": f"source stale {f['minutes_elapsed']} min",
            }
        )
    disabled = {m["unique_id"] for m in models if not m["enabled"]}
    for m in models:
        if not m["enabled"]:
            continue
        for dep in m.get("depends_on") or []:
            if dep in disabled:
                rows.append(
                    {
                        "alert_code": "DISABLED_UPSTREAM",
                        "severity": "error",
                        "subject_id": m["unique_id"],
                        "message": f"depends on disabled {dep}",
                    }
                )
    for exp, models_list in refs.items():
        if not models_list:
            rows.append(
                {
                    "alert_code": "EXPOSURE_EMPTY",
                    "severity": "warn",
                    "subject_id": exp,
                    "message": "exposure has no model refs",
                }
            )
    rows.sort(key=lambda r: (rank.get(r["severity"], 9), r["alert_code"], r["subject_id"]))
    return rows


def _normalize_alerts(alerts: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        {
            "alert_code": row["alert_code"],
            "message": row["message"],
            "severity": row["severity"],
            "subject_id": row["subject_id"],
        }
        for row in alerts
    ]


def _audit_digest(model_order: list[str], refs: dict, alerts: list, summary: dict) -> str:
    body = json.dumps(
        {
            "alerts": _normalize_alerts(alerts),
            "exposure_refs": refs,
            "model_order": model_order,
            "summary": summary,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(body.encode()).hexdigest()


def compute_lineage_scan(bundle: dict[str, Any], seed: str) -> dict[str, Any]:
    mat = bundle["_materialized"]
    models = mat["models"]
    order = _enabled_topo(models)
    fresh = _freshness(mat["sources"], bundle["evaluated_at"])
    refs = _exposure_closure(mat["exposures"], models)
    stale = sum(1 for f in fresh if f["status"] != "ok")
    enabled_count = sum(1 for m in models if m["enabled"])
    summary = {
        "enabled_model_count": enabled_count,
        "stale_source_count": stale,
        "exposure_count": len(mat["exposures"]),
        "disabled_ref_ok": _disabled_ref_ok(models),
    }
    alerts = _alerts(fresh, models, refs)
    return {
        "model_order": order,
        "freshness": fresh,
        "exposure_refs": refs,
        "summary": summary,
        "alerts": alerts,
        "audit_digest": _audit_digest(order, refs, alerts, summary),
    }


def build_alert_report(seed: str, bundle: str, scan_id: int, scanned: dict[str, Any]) -> dict[str, Any]:
    return {
        "seed": seed,
        "bundle": bundle,
        "scan_id": scan_id,
        "model_order": scanned["model_order"],
        "freshness": scanned["freshness"],
        "exposure_refs": scanned["exposure_refs"],
        "alerts": scanned["alerts"],
        "summary": scanned["summary"],
        "audit_digest": scanned["audit_digest"],
    }
