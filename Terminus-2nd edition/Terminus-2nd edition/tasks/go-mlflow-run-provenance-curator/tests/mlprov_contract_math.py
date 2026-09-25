"""Independent curation math for mlprov — not part of the agent contract."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any


def _scope_run(seed: str, run_id: str) -> str:
    x = 2166136261
    for b in (seed + ":" + run_id).encode():
        x ^= b
        x = (x * 16777619) & 0xFFFFFFFF
    return f"{run_id}-{x:08x}"


def _hydrate_runs(sc: dict[str, Any], seed: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for r in sc["runs"]:
        parent = r.get("parent_run_id") or ""
        if parent:
            parent = _scope_run(seed, parent)
        rows.append(
            {
                "run_id": _scope_run(seed, r["run_id"]),
                "parent_run_id": parent,
                "params": dict(r.get("params") or {}),
                "metrics": [dict(m) for m in r.get("metrics") or []],
                "artifacts": [dict(a) for a in r.get("artifacts") or []],
                "dataset_pins": [dict(p) for p in r.get("dataset_pins") or []],
            }
        )
    return rows


def _lookup_run(runs: list[dict[str, Any]], rid: str) -> dict[str, Any] | None:
    for r in runs:
        if r["run_id"] == rid:
            return r
    return None


def _ancestor_ids(runs: list[dict[str, Any]], focus: str) -> list[str]:
    chain: list[str] = []
    cur = focus
    seen: set[str] = set()
    while cur and cur not in seen:
        seen.add(cur)
        chain.append(cur)
        row = _lookup_run(runs, cur)
        if not row or not row.get("parent_run_id"):
            break
        cur = row["parent_run_id"]
    chain.reverse()
    return chain


def _clean_rel(path: str) -> str:
    p = path.removeprefix("./")
    return p.replace("\\", "/")


def _sha_artifact(rel_path: str, content: str) -> str:
    rel = _clean_rel(rel_path)
    return hashlib.sha256((rel + "\n" + content).encode()).hexdigest()


def _sorted_metrics(metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(metrics, key=lambda m: (m["epoch"], m["step"], m["key"]))


def _epochs_monotone(ordered: list[dict[str, Any]]) -> bool:
    if not ordered:
        return True
    peak_step: dict[int, int] = {}
    prev_epoch = ordered[0]["epoch"]
    peak_step[prev_epoch] = ordered[0]["step"]
    for m in ordered[1:]:
        if m["epoch"] > prev_epoch:
            if m["step"] < peak_step[prev_epoch]:
                return False
            prev_epoch = m["epoch"]
        peak_step[m["epoch"]] = max(peak_step.get(m["epoch"], 0), m["step"])
    return True


def _manifest_hash(manifest: dict[str, Any]) -> str:
    h = manifest["version_hash"]
    salt = os.environ.get("TB3_MANIFEST_SALT", "")
    return h + salt if salt else h


def _pin_rows(
    run: dict[str, Any], manifests: dict[str, Any]
) -> tuple[list[dict[str, Any]], bool]:
    bindings: list[dict[str, Any]] = []
    all_ok = len(run.get("dataset_pins") or []) > 0
    for pin in run.get("dataset_pins") or []:
        manifest = manifests.get(pin["name"])
        bind_ok = False
        row = 0
        if manifest:
            row = int(manifest["row_count"])
            bind_ok = pin["version_hash"] == _manifest_hash(manifest)
        if not bind_ok:
            all_ok = False
        bindings.append(
            {
                "name": pin["name"],
                "version_hash": pin["version_hash"],
                "row_count": row,
                "bind_ok": bind_ok,
            }
        )
    return bindings, all_ok


def _digest_rows(run: dict[str, Any]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for a in run.get("artifacts") or []:
        rel = _clean_rel(a["rel_path"])
        out.append({"rel_path": rel, "digest": _sha_artifact(a["rel_path"], a["content"])})
    out.sort(key=lambda x: x["rel_path"])
    return out


def _audit_blob(summary: dict[str, Any], chain: list[str], manifests: dict[str, Any]) -> str:
    hashes = sorted(_manifest_hash(m) for m in manifests.values())
    chain_json = json.dumps(chain, separators=(",", ":"))
    hash_json = json.dumps(hashes, separators=(",", ":"))
    body = (
        "{"
        f'"artifact_count":{int(summary["artifact_count"])},'
        f'"binding_ok":{str(summary["binding_ok"]).lower()},'
        f'"epoch_monotonic_ok":{str(summary["epoch_monotonic_ok"]).lower()},'
        f'"lineage_depth":{int(summary["lineage_depth"])},'
        f'"lineage_chain":{chain_json},'
        f'"version_hashes":{hash_json}'
        "}"
    )
    return hashlib.sha256(body.encode()).hexdigest()


def reference_load_scenario(path: Path, seed: str) -> dict[str, Any]:
    """Independent reference loader (gate-visible reference_* name)."""
    return read_fixture_bundle(path, seed)


def read_fixture_bundle(path: Path, seed: str) -> dict[str, Any]:
    sc = json.loads(path.read_text(encoding="utf-8"))
    sc["_runs"] = _hydrate_runs(sc, seed)
    sc["_focus"] = _scope_run(seed, sc["focus_run_id"])
    return sc


def reference_curate(sc: dict[str, Any], seed: str) -> dict[str, Any]:
    """Independent reference curation (gate-visible reference_* name)."""
    return independent_curation_expectation(sc, seed)


def independent_curation_expectation(sc: dict[str, Any], seed: str) -> dict[str, Any]:
    runs = sc["_runs"]
    focus_id = sc["_focus"]
    focus = _lookup_run(runs, focus_id)
    assert focus is not None
    chain = _ancestor_ids(runs, focus_id)
    ordered = _sorted_metrics(focus["metrics"])
    bindings, binding_ok = _pin_rows(focus, sc["dataset_manifests"])
    artifacts = _digest_rows(focus)
    summary = {
        "binding_ok": binding_ok,
        "epoch_monotonic_ok": _epochs_monotone(ordered),
        "lineage_depth": len(chain),
        "artifact_count": len(artifacts),
    }
    return {
        "lineage_chain": chain,
        "artifact_digests": artifacts,
        "metric_epochs": ordered,
        "dataset_bindings": bindings,
        "summary": summary,
        "audit_digest": _audit_blob(summary, chain, sc["dataset_manifests"]),
    }


def reference_report(
    seed: str,
    scenario: str,
    focus_run_id: str,
    run_id: int,
    curated: dict[str, Any],
) -> dict[str, Any]:
    """Independent reference export payload (gate-visible reference_* name)."""
    return independent_export_payload(seed, scenario, focus_run_id, run_id, curated)


def independent_export_payload(
    seed: str,
    scenario: str,
    focus_run_id: str,
    run_id: int,
    curated: dict[str, Any],
) -> dict[str, Any]:
    return {
        "seed": seed,
        "scenario": scenario,
        "focus_run_id": focus_run_id,
        "run_id": run_id,
        "lineage_chain": curated["lineage_chain"],
        "artifact_digests": curated["artifact_digests"],
        "metric_epochs": curated["metric_epochs"],
        "dataset_bindings": curated["dataset_bindings"],
        "summary": curated["summary"],
        "audit_digest": curated["audit_digest"],
    }
