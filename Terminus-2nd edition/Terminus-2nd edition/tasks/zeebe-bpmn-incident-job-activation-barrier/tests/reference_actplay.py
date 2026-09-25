"""Independent actplay reference for activation atlas export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def activation_barrier_ms(sc: dict[str, Any], job: dict[str, Any]) -> tuple[int, str]:
    for inc in sc.get("incidents", []):
        if inc.get("job_key") != job["job_key"]:
            continue
        at = max(job["intent_at_ms"], inc["marker_persisted_at_ms"])
        return at, "incident_marker_persisted"
    return job["intent_at_ms"], "none"


def boundary_can_fire(sc: dict[str, Any], boundary: dict[str, Any]) -> bool:
    for job in sc.get("jobs", []):
        if job["element_id"] != boundary["attached_element"]:
            continue
        if boundary["fire_at_ms"] < job["activating_until_ms"]:
            return False
    return True


def deadline_ms(sc: dict[str, Any]) -> int:
    return sc["process_clock_ms"] + sc["job_timeout_ms"]


def merge_variables(v: dict[str, Any]) -> dict[str, Any]:
    working = dict(v.get("inputs") or {})
    protected = set((v.get("output_mapping") or {}).values())
    for key, val in (v.get("incident_overlay") or {}).items():
        if key in protected:
            continue
        working[key] = val
    resolved: dict[str, int] = {}
    for out_key, src_key in (v.get("output_mapping") or {}).items():
        resolved[out_key] = working[src_key]
    return {"working": working, "resolved_outputs": resolved}


def should_activate(seen: set[str], batch: dict[str, Any], job_key: str) -> bool:
    pair = f"{batch['batch_id']}:{job_key}"
    return not (batch.get("idempotent") and pair in seen)


def reference_export(scenario_path: Path) -> dict[str, Any]:
    sc = json.loads(scenario_path.read_text(encoding="utf-8"))
    jobs_by_key = {j["job_key"]: j for j in sc.get("jobs", [])}
    dl = deadline_ms(sc)
    activations: list[dict[str, Any]] = []
    dup_skipped = 0
    seen: set[str] = set()
    seq = 1
    for batch in sc.get("replay_batches", []):
        for job_key in batch.get("job_keys", []):
            if not should_activate(seen, batch, job_key):
                dup_skipped += 1
                continue
            job = jobs_by_key.get(job_key)
            if job is None:
                continue
            at, barrier = activation_barrier_ms(sc, job)
            activations.append(
                {
                    "job_key": job_key,
                    "activated_at_ms": at,
                    "deadline_ms": dl,
                    "barrier": barrier,
                    "sequence_no": seq,
                }
            )
            seq += 1
            seen.add(f"{batch['batch_id']}:{job_key}")
    boundaries: list[dict[str, Any]] = []
    for b in sc.get("boundaries", []):
        if not boundary_can_fire(sc, b):
            continue
        boundaries.append(
            {
                "boundary_id": b["boundary_id"],
                "attached_element": b["attached_element"],
                "fired_at_ms": b["fire_at_ms"],
                "interrupting": b["interrupting"],
            }
        )
    vars_snap = merge_variables(sc.get("variables") or {})
    return {
        "process_id": sc["process_id"],
        "partition_id": sc["partition_id"],
        "activation_sequence": activations,
        "boundary_events": boundaries,
        "variable_snapshot": vars_snap,
        "duplicate_activations_skipped": dup_skipped,
        "deadline_clock_source": "process",
    }


def pending_job_keys(sc: dict[str, Any]) -> list[str]:
    """Job keys gated on incident marker persistence (marker after job intent)."""
    jobs_by_key = {j["job_key"]: j for j in sc.get("jobs", [])}
    pending: list[str] = []
    seen: set[str] = set()
    for inc in sc.get("incidents", []):
        job_key = inc.get("job_key")
        if not job_key or job_key in seen:
            continue
        job = jobs_by_key.get(job_key)
        if job is None:
            continue
        if inc["marker_persisted_at_ms"] <= job["intent_at_ms"]:
            continue
        pending.append(job_key)
        seen.add(job_key)
    pending.sort()
    return pending


def reference_snapshot(scenario_path: Path) -> dict[str, Any]:
    sc = json.loads(scenario_path.read_text(encoding="utf-8"))
    markers = {
        inc["incident_key"]: inc["marker_persisted_at_ms"] for inc in sc.get("incidents", [])
    }
    seen: list[str] = []
    fired: list[str] = []
    for batch in sc.get("replay_batches", []):
        for job_key in batch.get("job_keys", []):
            pair = f"{batch['batch_id']}:{job_key}"
            if batch.get("idempotent") and pair in seen:
                continue
            seen.append(pair)
    for b in sc.get("boundaries", []):
        if boundary_can_fire(sc, b):
            fired.append(b["boundary_id"])
    return {
        "process_id": sc["process_id"],
        "partition_id": sc["partition_id"],
        "incident_marker_persisted_ms": markers,
        "pending_job_keys": pending_job_keys(sc),
        "boundary_events_fired": fired,
        "dedup_pairs": seen,
        "staging_written": False,
    }
