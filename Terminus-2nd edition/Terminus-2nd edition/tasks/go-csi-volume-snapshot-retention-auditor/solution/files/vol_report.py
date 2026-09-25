from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from snapret import bp_rank, fleet_store, ns_rollup, orph_probe

DEFAULT_REPORT = "/app/output/volsnap-audit-report.json"
DEFAULT_DANGLING = "/app/output/orphan-snapshot-ledger.jsonl"
GEN_PATH = "/app/state/audit-pass-counter.json"


def emit(scenario: str, report_path: str = "", dangling_path: str = "") -> None:
    gen_path = Path(GEN_PATH)
    if not gen_path.is_file():
        raise RuntimeError("audit_pass_seq missing")
    gen = json.loads(gen_path.read_text(encoding="utf-8"))
    if int(gen.get("audit_pass_seq", 0)) <= 0:
        raise RuntimeError("emit blocked: audit_pass_seq must be > 0")
    stage = fleet_store.read_fleet_graph("")
    report, dangling_rows = _build_report(stage)
    report["scenario"] = scenario
    if not report_path:
        report_path = DEFAULT_REPORT
    if not dangling_path:
        dangling_path = DEFAULT_DANGLING
    _write_report(report_path, report)
    _write_dangling(dangling_path, dangling_rows)


def _build_report(stage: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, str]]]:
    cluster = stage["cluster"]
    now_ms = int(cluster.get("audit_clock_ms", 0))
    if now_ms <= 0:
        now_ms = int(time.time() * 1000)
    deletable: list[str] = []
    protected = 0
    for snap in cluster.get("snapshots", []):
        days = bp_rank.retention_days_for_snapshot(cluster, snap)
        if bp_rank.is_protected(snap, days):
            protected += 1
            continue
        age_days = (now_ms - int(snap.get("creation_clock_ms", 0))) // (86400 * 1000)
        if age_days >= days:
            deletable.append(snap["uid"])
    deletable.sort()
    violations = ns_rollup.quota_violations(cluster)
    report = {
        "protected_count": protected,
        "deletable_snapshot_uids": deletable,
        "quota_violations": violations,
    }
    report["report_digest"] = _report_digest(report)
    return report, orph_probe.dangling_snapshots(cluster)


def _report_digest(report: dict[str, Any]) -> str:
    payload = {
        "deletable_snapshot_uids": report["deletable_snapshot_uids"],
        "protected_count": report["protected_count"],
        "quota_violations": report["quota_violations"],
        "scenario": report.get("scenario", ""),
    }
    data = json.dumps(payload, separators=(",", ":")).encode()
    return hashlib.sha256(data).hexdigest()


def _write_report(path: str, report: dict[str, Any]) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def _write_dangling(path: str, rows: list[dict[str, str]]) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(row, separators=(",", ":")) for row in rows]
    out.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
