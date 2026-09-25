#!/usr/bin/env python3
"""Independent reference for reagentwin stability correlation validation."""

from __future__ import annotations

import hashlib
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any


def lot_cert_digest(lot_id: str, as_of_date: str, assay_code: str) -> str:
    body = f"{lot_id}:{as_of_date}:{assay_code}".encode()
    return hashlib.sha256(body).hexdigest()[:16]


def resolve_lot_id(alias: str, lots: list[dict[str, Any]]) -> str | None:
    alias_lower = alias.lower()
    for lot in lots:
        if lot["lot_id"].lower() == alias_lower:
            return lot["lot_id"]
        for a in lot.get("aliases", []):
            if a.lower() == alias_lower:
                return lot["lot_id"]
    return None


def excursion_minutes(rows: list[dict[str, Any]]) -> int:
    qualifying = [
        r["minute_index"]
        for r in rows
        if r["celsius"] > r["threshold_celsius"]
        and r["minute_index"] >= r["excursion_limit_minutes"]
    ]
    return max(qualifying) if qualifying else 0


def severity_score(excursion: int, peak: float, threshold: float) -> int:
    over = int(max(peak - threshold, 0.0))
    return excursion * 10 + over


def extended_expiry(base: str, cold_chain_days: int, stability_bonus_days: int) -> str:
    parsed = date.fromisoformat(base)
    out = parsed + timedelta(days=cold_chain_days + stability_bonus_days)
    return out.isoformat()


def build_correlated_lots(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    lots = bundle["lots"]
    as_of = bundle["as_of_date"]
    rows: list[dict[str, Any]] = []
    for lot in lots:
        tele = [
            t
            for t in bundle["telemetry"]
            if resolve_lot_id(t["lot_alias"], lots) == lot["lot_id"]
        ]
        exc = excursion_minutes(tele)
        peak = max((t["celsius"] for t in tele), default=0.0)
        threshold = tele[0]["threshold_celsius"] if tele else 8.0
        sev = severity_score(exc, peak, threshold)
        ext = extended_expiry(
            lot["base_expiry"], lot["cold_chain_days"], lot["stability_bonus_days"]
        )
        rows.append(
            {
                "lot_id": lot["lot_id"],
                "assay_code": lot["assay_code"],
                "base_expiry": lot["base_expiry"],
                "cert_digest": lot_cert_digest(lot["lot_id"], as_of, lot["assay_code"]),
                "excursion_minutes": exc,
                "extended_expiry": ext,
                "severity": sev,
                "quarantine": exc > 0,
            }
        )
    return rows


def sort_closure_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda r: (-r["severity"], r["lot_id"]))


def closure_digest(summary: dict[str, Any]) -> str:
    body = json.dumps(
        {
            "excursion_events": summary["excursion_events"],
            "max_severity": summary["max_severity"],
            "quarantined": summary["quarantined"],
            "total_lots": summary["total_lots"],
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(body.encode()).hexdigest()


def reference_closure(
    session_id: str,
    bundle_name: str,
    bundle_path: Path,
    correlate_generation: int = 1,
) -> dict[str, Any]:
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    correlated = build_correlated_lots(bundle)
    closure_rows = [
        {
            "lot_id": r["lot_id"],
            "severity": r["severity"],
            "excursion_minutes": r["excursion_minutes"],
            "extended_expiry": r["extended_expiry"],
            "cert_digest": r["cert_digest"],
            "quarantine": r["quarantine"],
        }
        for r in correlated
    ]
    closure_rows = sort_closure_rows(closure_rows)
    quarantined = sum(1 for r in closure_rows if r["quarantine"])
    max_severity = max((r["severity"] for r in closure_rows), default=0)
    excursion_events = sum(1 for r in closure_rows if r["excursion_minutes"] > 0)
    summary = {
        "total_lots": len(closure_rows),
        "quarantined": quarantined,
        "max_severity": max_severity,
        "excursion_events": excursion_events,
    }
    return {
        "session_id": session_id,
        "bundle": bundle_name,
        "rows": closure_rows,
        "summary": summary,
        "closure_digest": closure_digest(summary),
        "_correlate_generation": correlate_generation,
    }


if __name__ == "__main__":
    import sys

    p = Path(sys.argv[1])
    print(json.dumps(reference_closure("sess-alpha", p.stem, p), indent=2))
