from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from snapret import bp_rank, claim_bind, fleet_store, ns_rollup, orph_probe

FINDINGS_PATH = "/app/work/scoring-findings.json"
GEN_PATH = "/app/state/audit-pass-counter.json"


def run(scenario: str) -> None:
    stage = fleet_store.read_fleet_graph("")
    findings = _analyze(stage)
    out = {
        "scenario": scenario,
        "finding_count": len(findings),
        "findings": findings,
    }
    _write_findings(out)
    _bump_revision()


def _analyze(stage: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    cluster = stage["cluster"]
    for snap in cluster.get("snapshots", []):
        if not claim_bind.snapshot_pvc(cluster, snap)[1]:
            findings.append(
                {
                    "code": "pvc_missing",
                    "snapshot_uid": snap["uid"],
                    "namespace": snap["namespace"],
                    "detail": "no_pvc_join",
                }
            )
    for row in orph_probe.dangling_snapshots(cluster):
        findings.append(
            {
                "code": "dangling_snap",
                "snapshot_uid": row["uid"],
                "namespace": row["namespace"],
                "detail": row["source_pvc"],
            }
        )
    for snap in cluster.get("snapshots", []):
        days = bp_rank.retention_days_for_snapshot(cluster, snap)
        if bp_rank.is_protected(snap, days):
            findings.append(
                {
                    "code": "retain_pin",
                    "snapshot_uid": snap["uid"],
                    "detail": "protected",
                }
            )
    if len(ns_rollup.quota_violations(cluster)) > 0:
        findings.append({"code": "quota_pressure", "detail": "over_cap"})
    findings.sort(key=lambda row: (row.get("snapshot_uid", ""), row["code"]))
    return findings


def _write_findings(payload: dict[str, Any]) -> None:
    path = Path(FINDINGS_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _bump_revision() -> None:
    gen_path = Path(GEN_PATH)
    gen: dict[str, int] = {"audit_pass_seq": 0}
    if gen_path.is_file():
        gen = json.loads(gen_path.read_text(encoding="utf-8"))
    gen["audit_pass_seq"] = gen.get("audit_pass_seq", 0) + 1
    gen_path.parent.mkdir(parents=True, exist_ok=True)
    gen_path.write_text(json.dumps(gen, indent=2) + "\n", encoding="utf-8")
