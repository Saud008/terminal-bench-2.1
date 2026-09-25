"""Independent reference for rig alignment bundle pipeline."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CAL_LIMIT = 0.5


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_captures(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def load_checker(path: Path) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            row = json.loads(line)
            out[row["capture_id"]] = row
    return out


def mount_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_exif_ms(raw: str, tz_min: int) -> int:
    dt = datetime.fromisoformat(raw).replace(tzinfo=timezone.utc)
    base_ms = int(dt.timestamp() * 1000)
    return base_ms - tz_min * 60000


def compute_captures_digest(captures: list[dict[str, Any]]) -> str:
    keyed = []
    for cap in captures:
        norm = normalize_exif_ms(cap["timestamp_raw"], int(cap["timestamp_tz"]))
        keyed.append((norm, cap["capture_id"], cap))
    keyed.sort(key=lambda t: (t[0], t[1]))
    body = "".join(json.dumps(cap, separators=(",", ":")) + "\n" for _, _, cap in keyed)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def slot_map(mount: dict[str, Any]) -> dict[int, dict[str, Any]]:
    return {int(row["slot"]): row for row in mount.get("slots", [])}


def validate_rig_slot(mount: dict[str, Any], cap: dict[str, Any]) -> str | None:
    slot = int(cap["rig_slot"])
    row = slot_map(mount).get(slot)
    if row is None:
        return "rig_slot_mismatch"
    if row.get("camera_serial") != cap["camera_serial"]:
        return "rig_slot_mismatch"
    allowed = row.get("allowed_lens_ids") or []
    if cap["lens_id"] not in allowed:
        return "lens_not_allowed"
    return None


def match_lens_profile(profiles: list[dict[str, Any]], lens_id: str, normalized_ms: int) -> dict[str, Any] | None:
    chosen = None
    for row in profiles:
        if row.get("lens_id") != lens_id:
            continue
        if int(row.get("effective_capture_ms", 0)) <= normalized_ms:
            if chosen is None or int(row["effective_capture_ms"]) >= int(chosen["effective_capture_ms"]):
                chosen = row
    return chosen


def checker_fail(checker: dict[str, dict[str, Any]], capture_id: str, limit: float = CAL_LIMIT) -> bool:
    row = checker.get(capture_id)
    if row is None:
        return False
    if not row.get("board_detected", True):
        return True
    return float(row.get("reprojection_error", 0)) > limit


def missing_frames(mount: dict[str, Any], accepted: list[dict[str, Any]]) -> list[dict[str, int]]:
    start = int(mount.get("frame_index_start", 1))
    count = int(mount.get("expected_frames_per_slot", 0))
    expected = set(range(start, start + count))
    by_slot: dict[int, set[int]] = {}
    for row in accepted:
        by_slot.setdefault(int(row["rig_slot"]), set()).add(int(row["frame_index"]))
    missing: list[dict[str, int]] = []
    for slot_row in mount.get("slots", []):
        slot = int(slot_row["slot"])
        seen = by_slot.get(slot, set())
        for idx in sorted(expected - seen):
            missing.append({"rig_slot": slot, "frame_index": idx})
    return missing


def _normalize_json(value: Any) -> Any:
    if isinstance(value, float) and value == int(value):
        return int(value)
    if isinstance(value, dict):
        return {k: _normalize_json(v) for k, v in sorted(value.items())}
    if isinstance(value, list):
        return [_normalize_json(v) for v in value]
    return value


def manifest_digest(body: dict[str, Any]) -> str:
    payload = {k: v for k, v in body.items() if k != "manifest_digest"}
    raw = json.dumps(_normalize_json(payload), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def reference_align(
    mount: dict[str, Any],
    captures: list[dict[str, Any]],
    lenses_doc: dict[str, Any],
    checker: dict[str, dict[str, Any]],
    *,
    align_generation: int = 1,
    staging_generation: int = 1,
    mount_sha: str = "",
    cal_limit: float = CAL_LIMIT,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    profiles = lenses_doc.get("profiles") or []
    entries: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    accepted_for_gap: list[dict[str, Any]] = []
    for cap in captures:
        reason = validate_rig_slot(mount, cap)
        if reason:
            rejected.append({"capture_id": cap["capture_id"], "reason": reason})
            continue
        norm = normalize_exif_ms(cap["timestamp_raw"], int(cap["timestamp_tz"]))
        prof = match_lens_profile(profiles, cap["lens_id"], norm)
        if prof is None:
            rejected.append({"capture_id": cap["capture_id"], "reason": "missing_lens_profile"})
            continue
        if checker_fail(checker, cap["capture_id"], cal_limit):
            rejected.append({"capture_id": cap["capture_id"], "reason": "calibration_failed"})
            continue
        row = {
            "capture_id": cap["capture_id"],
            "rig_slot": int(cap["rig_slot"]),
            "camera_serial": cap["camera_serial"],
            "lens_id": cap["lens_id"],
            "frame_index": int(cap["frame_index"]),
            "normalized_ms": norm,
            "profile_revision": prof.get("profile_revision", ""),
            "focal_mm": float(prof.get("focal_mm", 0)),
            "aligned": True,
        }
        entries.append(row)
        accepted_for_gap.append({"rig_slot": row["rig_slot"], "frame_index": row["frame_index"]})
    entries.sort(key=lambda r: (r["normalized_ms"], r["capture_id"]))
    align_doc = {
        "generation": align_generation,
        "staging_generation": staging_generation,
        "mount_sha256": mount_sha,
        "entries": entries,
        "missing_frames": missing_frames(mount, accepted_for_gap),
    }
    bundle = {
        "align_generation": align_generation,
        "staging_generation": staging_generation,
        "entries": deepcopy(entries),
        "missing_frames": deepcopy(align_doc["missing_frames"]),
    }
    bundle["manifest_digest"] = manifest_digest(bundle)
    return bundle, rejected


def reference_bundle_from_align(align: dict[str, Any]) -> dict[str, Any]:
    bundle = {
        "align_generation": align["generation"],
        "staging_generation": align["staging_generation"],
        "entries": deepcopy(align["entries"]),
        "missing_frames": deepcopy(align["missing_frames"]),
    }
    bundle["manifest_digest"] = manifest_digest(bundle)
    return bundle
