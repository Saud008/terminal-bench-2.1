"""Independent GitLab CI lint contract math for pytest."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml


def load_pipeline(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def matrix_name(base: str, row: dict[str, str]) -> str:
    parts = [f"{k}={row[k]}" for k in sorted(row.keys())]
    return base + "/" + "/".join(parts)


def expand_jobs(pipeline: dict[str, Any]) -> list[dict[str, Any]]:
    skip = {"stages", "variables", "default", "include", "workflow"}
    jobs: list[dict[str, Any]] = []
    seen: set[str] = set()
    for base, job in pipeline.items():
        if base in skip or not isinstance(job, dict):
            continue
        par = job.get("parallel")
        rows: list[dict[str, str] | None]
        if isinstance(par, dict) and "matrix" in par:
            rows = [dict(r) for r in par["matrix"]]
        else:
            rows = [None]
        for row in rows:
            name = base if row is None else matrix_name(base, row)
            dup = name in seen
            seen.add(name)
            rules = job.get("rules") or []
            when = "on_success"
            for rule in rules:
                when = rule.get("when", "on_success")
                break
            active = when != "never"
            needs_raw = job.get("needs")
            needs = _parse_needs(needs_raw)
            arts = (job.get("artifacts") or {}).get("paths") or []
            jobs.append(
                {
                    "name": name,
                    "stage": job.get("stage", "test"),
                    "when": when,
                    "active": active,
                    "needs": needs,
                    "duplicate": dup,
                    "artifacts": {"paths": list(arts)},
                    "base": base,
                    "job_def": job,
                }
            )
    return jobs


def _parse_needs(raw: Any) -> list[dict[str, Any]]:
    if raw is None:
        return []
    if isinstance(raw, str):
        return [{"job": raw, "optional": False, "artifacts": False}]
    out: list[dict[str, Any]] = []
    for item in raw:
        if isinstance(item, str):
            out.append({"job": item, "optional": False, "artifacts": False})
        else:
            out.append(
                {
                    "job": item["job"],
                    "optional": bool(item.get("optional")),
                    "artifacts": bool(item.get("artifacts")),
                }
            )
    return out


def rules_fingerprint(jobs: list[dict[str, Any]]) -> str:
    parts = [f"{j['name']}:{j['when']}" for j in jobs if j["active"]]
    return hashlib.sha256("|".join(parts).encode()).hexdigest()


def staging_digest(run_id: str, jobs: list[dict[str, Any]], fp: str) -> str:
    body = {
        "run_id": run_id,
        "jobs": [{"name": j["name"], "stage": j["stage"], "active": j["active"]} for j in jobs],
        "rules_fingerprint": fp,
    }
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()


def lint_findings(pipeline: dict[str, Any], jobs: list[dict[str, Any]]) -> list[dict[str, str]]:
    stages = pipeline.get("stages") or []
    idx = {s: i for i, s in enumerate(stages)}
    by_name = {j["name"]: j for j in jobs}
    findings: list[dict[str, str]] = []

    for j in jobs:
        if j["duplicate"]:
            findings.append(
                {
                    "code": "MATRIX_DUPLICATE",
                    "severity": "error",
                    "job": j["name"],
                    "message": "duplicate matrix expansion",
                }
            )

    for j in jobs:
        if not j["active"]:
            continue
        for edge in j["needs"]:
            if edge["optional"]:
                continue
            prod = by_name.get(edge["job"])
            if prod is None:
                findings.append(
                    {
                        "code": "NEED_MISSING",
                        "severity": "error",
                        "job": j["name"],
                        "message": f"missing need {edge['job']}",
                    }
                )
                continue
            ci, pi = idx.get(j["stage"], -1), idx.get(prod["stage"], -1)
            if ci <= pi:
                findings.append(
                    {
                        "code": "STAGE_ORDER",
                        "severity": "error",
                        "job": j["name"],
                        "message": f"need {edge['job']} stage order violation",
                    }
                )

    # artifact closure on required chain
    for j in jobs:
        if not j["active"]:
            continue
        for edge in j["needs"]:
            if edge["optional"] or not edge.get("artifacts"):
                continue
            if not _artifact_ok(j, edge["job"], by_name, set()):
                findings.append(
                    {
                        "code": "ARTIFACT_CLOSURE",
                        "severity": "error",
                        "job": j["name"],
                        "message": f"artifact closure fail for {edge['job']}",
                    }
                )

    findings.sort(key=lambda f: (f["job"], f["code"]))
    return findings


def _artifact_ok(consumer: dict[str, Any], producer_name: str, by_name: dict, visited: set[str]) -> bool:
    if producer_name in visited:
        return True
    visited.add(producer_name)
    prod = by_name.get(producer_name)
    if prod is None:
        return False
    prod_paths = set(prod["artifacts"]["paths"])
    if not prod_paths:
        return False
    # transitive: if producer needs artifacts, walk up
    for edge in prod["needs"]:
        if edge.get("artifacts") and not edge["optional"]:
            if not _artifact_ok(prod, edge["job"], by_name, visited):
                return False
    return bool(prod_paths)


def reference_contract_report(pipeline_path: Path, run_id: str) -> dict[str, Any]:
    pipeline = load_pipeline(pipeline_path)
    jobs = expand_jobs(pipeline)
    fp = rules_fingerprint(jobs)
    findings = lint_findings(pipeline, jobs)
    summary = {"error": 0, "warn": 0, "info": 0}
    for f in findings:
        summary[f["severity"]] = summary.get(f["severity"], 0) + 1
    audit = hashlib.sha256(
        json.dumps({"codes": [f["code"] for f in findings], "summary": summary}, sort_keys=True).encode()
    ).hexdigest()
    return {
        "run_id": run_id,
        "findings": findings,
        "summary": summary,
        "audit_digest": audit,
        "staging": {
            "run_id": run_id,
            "jobs": jobs,
            "rules_fingerprint": fp,
            "staging_digest": staging_digest(run_id, jobs, fp),
            "stages": pipeline.get("stages") or [],
        },
    }
