"""Independent Nextflow resume-cache audit reference for verifier."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def norm_digest(raw: str) -> str:
    s = raw.strip()
    if s.lower().startswith("sha256:"):
        s = s[7:]
    return s.lower()


def expand_sorted(run_dir: Path, pattern: str) -> list[str]:
    paths: list[str] = []
    for p in sorted(run_dir.glob(pattern)):
        if p.is_file():
            paths.append(p.relative_to(run_dir).as_posix())
    return sorted(paths)


def expansion_hash(run_dir: Path, globs: list[str]) -> str:
    h = hashlib.sha256()
    all_paths: list[str] = []
    for g in globs:
        all_paths.extend(expand_sorted(run_dir, g))
    for p in sorted(all_paths):
        h.update(p.encode())
        h.update(b"\0")
    return h.hexdigest()


def lineage_digest(parents: list[str], task_hash: str) -> str:
    h = hashlib.sha256()
    for p in [*parents, task_hash]:
        h.update(p.strip().encode())
        h.update(b"\0")
    return h.hexdigest()


def load_run(fixture_root: Path, scenario: str) -> tuple[dict[str, Any], list[dict[str, Any]], Path]:
    manifest = json.loads((fixture_root / "scenarios" / f"{scenario}.json").read_text(encoding="utf-8"))
    run_dir = fixture_root / manifest["run_dir"]
    meta = json.loads((run_dir / "run.meta.json").read_text(encoding="utf-8"))
    tasks: list[dict[str, Any]] = []
    for path in sorted((run_dir / "trace").glob("*.json")):
        tasks.append(json.loads(path.read_text(encoding="utf-8")))
    return meta, tasks, run_dir


def stage_tasks(fixture_root: Path, scenario: str) -> list[dict[str, Any]]:
    _meta, tasks, run_dir = load_run(fixture_root, scenario)
    staged: list[dict[str, Any]] = []
    for rec in tasks:
        tid = rec["task_id"]
        marker_path = run_dir / "work" / tid.replace(":", "_") / ".nf_cached.json"
        cache_session = ""
        if marker_path.is_file():
            cache_session = json.loads(marker_path.read_text(encoding="utf-8")).get("session_id", "")
        computed_lineage = lineage_digest(rec.get("parent_hashes", []), rec["hash"])
        claimed = rec.get("lineage_digest") or computed_lineage
        staged.append(
            {
                "task_id": tid,
                "hash": rec["hash"],
                "lineage_digest": claimed,
                "parent_hashes": rec.get("parent_hashes", []),
                "container_digest": norm_digest(rec["container_digest"]),
                "expansion_hash": rec.get("expansion_hash", ""),
                "computed_expansion_hash": expansion_hash(run_dir, rec.get("input_globs", [])),
                "attempt": rec.get("attempt", 1),
                "cached": rec.get("cached", False),
                "exit_status": rec.get("exit_status", 0),
                "prior_digest": norm_digest(rec.get("prior_digest", "")),
                "prior_exit_status": rec.get("prior_exit_status"),
                "cache_session_id": cache_session,
            }
        )
    return staged


def collect_findings(meta: dict[str, Any], staged: list[dict[str, Any]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for t in staged:
        if t["cached"] and t["prior_digest"] and t["container_digest"] != t["prior_digest"]:
            out.append(
                {
                    "task_id": t["task_id"],
                    "rule": "digest_drift",
                    "detail": f"cached digest {t['container_digest']} != prior {t['prior_digest']}",
                }
            )
        if t["expansion_hash"] and t["computed_expansion_hash"] != t["expansion_hash"]:
            out.append(
                {
                    "task_id": t["task_id"],
                    "rule": "glob_expansion_mismatch",
                    "detail": f"recorded {t['expansion_hash']} computed {t['computed_expansion_hash']}",
                }
            )
        expected = lineage_digest(t["parent_hashes"], t["hash"])
        if expected != t["lineage_digest"]:
            out.append(
                {
                    "task_id": t["task_id"],
                    "rule": "lineage_break",
                    "detail": f"staged {t['lineage_digest']} expected {expected}",
                }
            )
        pes = t["prior_exit_status"]
        if t["attempt"] > 1 and t["cached"] and pes is not None and pes != 0:
            out.append(
                {
                    "task_id": t["task_id"],
                    "rule": "retry_stale_cache",
                    "detail": f"attempt {t['attempt']} cached after prior exit {pes}",
                }
            )
        if (
            meta.get("resumed")
            and t["cached"]
            and t["cache_session_id"]
            and t["cache_session_id"] != meta.get("session_id")
        ):
            out.append(
                {
                    "task_id": t["task_id"],
                    "rule": "provenance_crossrun",
                    "detail": (
                        f"cache session {t['cache_session_id']} != "
                        f"run session {meta.get('session_id')}"
                    ),
                }
            )
    out.sort(key=lambda f: (f["task_id"], f["rule"]))
    return out


def audit_digest(findings: list[dict[str, str]]) -> str:
    return hashlib.sha256(json.dumps(findings, separators=(",", ":")).encode()).hexdigest()


def reference_report(fixture_root: Path, scenario: str) -> dict[str, Any]:
    meta, _, _ = load_run(fixture_root, scenario)
    staged = stage_tasks(fixture_root, scenario)
    findings = collect_findings(meta, staged)
    return {
        "scenario": scenario,
        "audit_generation": 1,
        "unsafe_count": len(findings),
        "findings": findings,
        "audit_digest": audit_digest(findings),
        "safe_for_resume": len(findings) == 0,
    }
