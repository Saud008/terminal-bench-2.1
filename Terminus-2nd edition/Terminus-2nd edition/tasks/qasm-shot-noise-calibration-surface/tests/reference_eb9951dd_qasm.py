"""Independent reference for qasmenv shot-noise calibration envelope."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_row(counts: list[int]) -> list[float]:
    total = sum(counts)
    return [c / total for c in counts]


def normalize_histogram(rows: list[dict[str, Any]]) -> dict[str, list[float]]:
    out: dict[str, list[float]] = {}
    for row in rows:
        out[row["qubit"]] = normalize_row(row["counts"])
    return out


def tie_break_prefix(seed_hash: str, offset: int = 0) -> str:
    prefix = seed_hash[:6]
    if offset:
        return f"{prefix}:{offset}"
    return prefix


def select_matrix(
    candidates: list[dict[str, Any]],
    dimension: int,
    seed_hash: str,
    offset: int = 0,
) -> dict[str, Any]:
    matching = [c for c in candidates if c["dimension"] == dimension]
    if not matching:
        raise ValueError("no matching matrix")
    max_pri = max(c["priority"] for c in matching)
    tied = [c for c in matching if c["priority"] == max_pri]
    if len(tied) == 1:
        return tied[0]
    prefix = tie_break_prefix(seed_hash, offset)
    qualified = [c for c in tied if c["id"] >= prefix]
    pool = qualified if qualified else tied
    return min(pool, key=lambda c: c["id"])


def apply_drift(
    normalized: dict[str, list[float]],
    factors: dict[str, float],
) -> dict[str, list[float]]:
    out: dict[str, list[float]] = {}
    for qubit, probs in normalized.items():
        factor = factors.get(qubit, 1.0)
        adjusted = [p * factor for p in probs]
        total = sum(adjusted)
        out[qubit] = [v / total for v in adjusted] if total else adjusted
    return out


def apply_matrix(matrix: list[list[float]], probs: list[float]) -> list[float]:
    result: list[float] = []
    for row in matrix:
        val = sum(coeff * probs[j] for j, coeff in enumerate(row))
        result.append(round(val, 6))
    return result


def wilson_intervals(mitigated: list[float], total_shots: int) -> list[dict[str, float]]:
    n = float(total_shots)
    z = 1.96
    intervals: list[dict[str, float]] = []
    for p in mitigated:
        if n <= 0:
            half = 0.0
        else:
            half = (z / (2.0 * n)) * (4.0 * n * p * (1.0 - p) + z * z) ** 0.5 / (1.0 + (z * z) / n)
        lower = max(0.0, p - half)
        upper = min(1.0, p + half)
        intervals.append(
            {
                "lower": round(lower, 6),
                "upper": round(upper, 6),
            }
        )
    return intervals


def build_provenance_chain(
    calibration_ids: list[str],
    experiment_id: str,
    matrix_id: str,
) -> list[str]:
    chain = list(calibration_ids) + [experiment_id, matrix_id]
    chain.sort()
    return chain


def provenance_digest(chain: list[str]) -> str:
    payload = json.dumps(chain, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def tb3_seed_offset() -> int:
    raw = os.environ.get("TB3_SEED_OFFSET", "0")
    try:
        return int(raw)
    except ValueError:
        return 0


def reference_compute(staging: dict[str, Any], *, seed_offset: int | None = None) -> dict[str, Any]:
    offset = tb3_seed_offset() if seed_offset is None else seed_offset
    rows = staging["histogram"]["rows"]
    normalized = normalize_histogram(rows)
    dimension = len(staging["histogram"]["qubits"])
    selected = select_matrix(
        staging["mitigation"]["candidates"],
        dimension,
        staging["manifest"]["seed_hash"],
        offset,
    )
    factors = {k: v["factor"] for k, v in staging["drift"]["factors"].items()}
    drift_corrected = apply_drift(normalized, factors)

    envelopes: dict[str, Any] = {}
    for row in rows:
        qubit = row["qubit"]
        mitigated = apply_matrix(selected["matrix"], drift_corrected[qubit])
        total_shots = sum(row["counts"])
        intervals = wilson_intervals(mitigated, total_shots)
        envelopes[qubit] = {
            "mitigated": mitigated,
            "intervals": intervals,
            "total_shots": total_shots,
        }

    chain = build_provenance_chain(
        staging["manifest"]["calibration_ids"],
        staging["manifest"]["experiment_id"],
        selected["id"],
    )
    return {
        "ingest_seq": staging["ingest_seq"],
        "experiment_id": staging["manifest"]["experiment_id"],
        "selected_matrix_id": selected["id"],
        "normalized_probs": normalized,
        "drift_corrected": drift_corrected,
        "envelopes": envelopes,
        "provenance": {
            "chain": chain,
            "digest": provenance_digest(chain),
        },
    }


def reference_export(ledger: dict[str, Any]) -> dict[str, Any]:
    return {
        "experiment_id": ledger["experiment_id"],
        "selected_matrix_id": ledger["selected_matrix_id"],
        "envelopes": ledger["envelopes"],
        "provenance": ledger["provenance"],
    }


def reference_digest_from_export(exported: dict[str, Any]) -> str:
    envelopes = {k: exported["envelopes"][k] for k in sorted(exported["envelopes"])}
    payload = {
        "experiment_id": exported["experiment_id"],
        "selected_matrix_id": exported["selected_matrix_id"],
        "envelopes": envelopes,
        "provenance": exported["provenance"],
    }
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def reference_digest(ledger: dict[str, Any]) -> str:
    return reference_digest_from_export(reference_export(ledger))


def count_gates(qasm_text: str) -> int:
    count = 0
    for line in qasm_text.splitlines():
        t = line.strip()
        if t.endswith(";") and (
            t.startswith("h") or t.startswith("cx") or t.startswith("measure")
        ):
            count += 1
    return count
