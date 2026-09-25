"""Independent reference oracle for icc-drift-bundler."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

STAGING_SCHEMA = "icc-softproof-stage/1"
REPORT_SCHEMA = "icc-drift-report/1"


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_digest(doc: dict[str, Any]) -> str:
    payload = json.dumps(doc, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_readings(path: Path) -> list[dict[str, Any]]:
    patches: dict[str, dict[str, Any]] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 4:
            continue
        patch_id, l_s, a_s, b_s = parts[0], parts[1], parts[2], parts[3]
        if patch_id == "patch_id" or l_s == "L":
            continue
        try:
            l_val = float(l_s)
            a_val = float(a_s)
            b_val = float(b_s)
        except ValueError:
            continue
        batch_id = parts[4] if len(parts) > 4 else ""
        patches[patch_id] = {
            "patch_id": patch_id,
            "L": l_val,
            "a": a_val,
            "b": b_val,
            "batch_id": batch_id,
        }
    return [patches[k] for k in sorted(patches)]


def profile_checksum(profile: dict[str, Any]) -> str:
    fields = profile.get("checksum_fields", [])
    subset = {k: profile[k] for k in fields if k in profile}
    payload = json.dumps(subset, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def cie76_delta(l1: float, a1: float, b1: float, l2: float, a2: float, b2: float) -> float:
    return math.sqrt((l1 - l2) ** 2 + (a1 - a2) ** 2 + (b1 - b2) ** 2)


def batch_index(paper: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(b["id"]): b for b in paper.get("batches", [])}


def effective_gamma(batch_id: str, paper: dict[str, Any]) -> float | None:
    if not batch_id:
        return None
    idx = batch_index(paper)
    current = batch_id
    visited: set[str] = set()
    while current:
        if current in visited:
            return None
        visited.add(current)
        row = idx.get(current)
        if not row:
            return None
        anchor = row.get("gamma_anchor")
        if anchor is not None:
            return float(anchor)
        parent = row.get("parent")
        current = str(parent) if parent else ""
    return None


def pick_intent(profile: dict[str, Any], policy: dict[str, Any]) -> str:
    supported = set(profile.get("rendering_intents", {}).keys())
    for intent in policy.get("intent_precedence", []):
        if intent in supported:
            return str(intent)
    return ""


def reference_lab(
    profile: dict[str, Any],
    patch_id: str,
    intent: str,
) -> tuple[float, float, float] | None:
    intents = profile.get("rendering_intents", {})
    intent_map = intents.get(intent, {})
    if patch_id in intent_map:
        row = intent_map[patch_id]
        return float(row["L"]), float(row["a"]), float(row["b"])
    ref = profile.get("reference_patches", {}).get(patch_id)
    if ref:
        return float(ref["L"]), float(ref["a"]), float(ref["b"])
    return None


def ticket_for_batch(
    tickets_doc: dict[str, Any],
    profile_id: str,
    batch_id: str,
    as_of: int,
) -> dict[str, Any] | None:
    hits: list[dict[str, Any]] = []
    for ticket in tickets_doc.get("tickets", []):
        if str(ticket.get("profile_id")) != profile_id:
            continue
        if str(ticket.get("paper_batch_id")) != batch_id:
            continue
        start = int(ticket.get("valid_from_epoch", 0))
        end = int(ticket.get("valid_until_epoch", 0))
        if as_of >= start and as_of <= end:
            hits.append(ticket)
    if not hits:
        return None
    hits.sort(key=lambda t: str(t.get("ticket_id", "")))
    return hits[0]


def stage_path_for(readings_path: Path) -> Path:
    return readings_path.parent / "icc.stage.json"


def expected_stage(
    readings_path: Path,
    profile_path: Path,
    paper_path: Path,
) -> dict[str, Any]:
    profile = load_json(profile_path)
    patches = parse_readings(readings_path)
    return {
        "schema": STAGING_SCHEMA,
        "readings_digest": file_digest(readings_path),
        "profile_digest": file_digest(profile_path),
        "paper_digest": file_digest(paper_path),
        "profile_id": str(profile.get("profile_id", "")),
        "patches": patches,
        "evaluation": None,
    }


def evaluate_patches(
    stage: dict[str, Any],
    profile_path: Path,
    paper_path: Path,
    policy_path: Path,
    tickets_path: Path,
    as_of: int,
) -> dict[str, Any]:
    profile = load_json(profile_path)
    paper = load_json(paper_path)
    policy = load_json(policy_path)
    tickets_doc = load_json(tickets_path)
    profile_id = str(profile.get("profile_id", ""))
    intent = pick_intent(profile, policy)
    checksum_ok = True
    if policy.get("require_profile_checksum", False):
        stored = str(profile.get("checksum", ""))
        checksum_ok = stored == profile_checksum(profile)
    per_patch: list[dict[str, Any]] = []
    for patch in stage.get("patches", []):
        patch_id = str(patch["patch_id"])
        batch_id = str(patch.get("batch_id", ""))
        ref = reference_lab(profile, patch_id, intent)
        flags: list[str] = []
        delta_e = 0.0
        if ref is None:
            flags.append("MISSING_REFERENCE_PATCH")
        else:
            delta_e = cie76_delta(
                float(patch["L"]),
                float(patch["a"]),
                float(patch["b"]),
                ref[0],
                ref[1],
                ref[2],
            )
            if delta_e > float(policy.get("delta_e_threshold", 2.0)):
                flags.append("DRIFT_DELTA_E")
        gamma = effective_gamma(batch_id, paper)
        prof_gamma = float(profile.get("gamma_reference", 0.0))
        if gamma is not None and abs(gamma - prof_gamma) > float(policy.get("gamma_drift_threshold", 0.01)):
            flags.append("GAMMA_LINEAGE_DRIFT")
        ticket = ticket_for_batch(tickets_doc, profile_id, batch_id, as_of) if batch_id else None
        if batch_id and ticket is None:
            flags.append("TICKET_EPOCH_INVALID")
        if not checksum_ok:
            flags.append("PROFILE_CHECKSUM_MISMATCH")
        per_patch.append(
            {
                "patch_id": patch_id,
                "delta_e": round(delta_e, 6),
                "active_intent": intent,
                "effective_gamma": gamma,
                "ticket_id": str(ticket.get("ticket_id", "")) if ticket else "",
                "drift_flags": sorted(flags),
            }
        )
    per_patch.sort(key=lambda row: row["patch_id"])
    return {
        "policy_digest": file_digest(policy_path),
        "evaluated_as_of": as_of,
        "profile_checksum_ok": checksum_ok,
        "per_patch": per_patch,
    }


def expected_stage_evaluated(
    readings_path: Path,
    profile_path: Path,
    paper_path: Path,
    policy_path: Path,
    tickets_path: Path,
    as_of: int,
) -> dict[str, Any]:
    stage = expected_stage(readings_path, profile_path, paper_path)
    stage["evaluation"] = evaluate_patches(
        stage,
        profile_path,
        paper_path,
        policy_path,
        tickets_path,
        as_of,
    )
    return stage


def expected_report(stage: dict[str, Any]) -> dict[str, Any]:
    evaluation = stage.get("evaluation") or {}
    per_patch = evaluation.get("per_patch", [])
    drift_count = sum(1 for row in per_patch if row.get("drift_flags"))
    checksum_fail = sum(1 for row in per_patch if "PROFILE_CHECKSUM_MISMATCH" in row.get("drift_flags", []))
    ticket_invalid = sum(1 for row in per_patch if "TICKET_EPOCH_INVALID" in row.get("drift_flags", []))
    delta_drift = sum(1 for row in per_patch if "DRIFT_DELTA_E" in row.get("drift_flags", []))
    return {
        "schema": REPORT_SCHEMA,
        "readings_digest": stage.get("readings_digest", ""),
        "profile_digest": stage.get("profile_digest", ""),
        "policy_digest": evaluation.get("policy_digest", ""),
        "profile_id": stage.get("profile_id", ""),
        "evaluated_as_of": evaluation.get("evaluated_as_of", 0),
        "summary": {
            "patch_count": len(per_patch),
            "drift_count": drift_count,
            "checksum_fail_count": checksum_fail,
            "ticket_invalid_count": ticket_invalid,
            "delta_e_drift_count": delta_drift,
        },
        "patches": per_patch,
    }


def expected_export_exit(report: dict[str, Any]) -> int:
    summary = report.get("summary", {})
    if int(summary.get("drift_count", 0)) > 0:
        return 2
    return 0


def make_random_readings(
    suffix: str,
    *,
    batch_id: str = "PB-CHILD",
) -> str:
    base_l = 48.0 + (hash(suffix) % 7)
    return (
        f"# random patch readings {suffix}\n"
        f"patch_id\tL\ta\tb\tbatch_id\n"
        f"RP-{suffix}\t{base_l:.1f}\t12.5\t-3.2\t{batch_id}\n"
        f"RP2-{suffix}\t55.0\t-8.0\t14.0\t{batch_id}\n"
    )
