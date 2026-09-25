"""Independent reference for modbus poll catalog drift pipeline."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_frames(path: Path) -> list[dict[str, Any]]:
    frames: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        frames.append(json.loads(line))
    return frames


def manifest_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compute_frames_digest(frames: list[dict[str, Any]]) -> str:
    ordered = sorted(frames, key=lambda f: (f["received_ms"], f["frame_id"]))
    body = "".join(json.dumps(fr, separators=(",", ":")) + "\n" for fr in ordered)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def decode_raw(frame: dict[str, Any], word_order: str) -> int:
    if frame["width"] == "uint16":
        return int(frame["words"][0]) & 0xFFFF
    w0 = int(frame["words"][0]) & 0xFFFF
    w1 = int(frame["words"][1]) & 0xFFFF
    if word_order == "little_endian_words":
        raw = (w1 << 16) | w0
    else:
        raw = (w0 << 16) | w1
    if raw >= 0x80000000:
        raw -= 0x100000000
    return raw


def effective_for_register(manifest: dict[str, Any], register: int) -> dict[str, Any]:
    out = {
        "word_order": manifest.get("default_word_order") or "big_endian_words",
        "clock_skew_ms": int(manifest["clock_skew_ms"]),
        "scale_epoch": "",
    }
    ov = (manifest.get("register_overrides") or {}).get(str(register)) or {}
    if ov.get("word_order"):
        out["word_order"] = ov["word_order"]
    if ov.get("clock_skew_ms"):
        out["clock_skew_ms"] = int(ov["clock_skew_ms"])
    if ov.get("scale_epoch"):
        out["scale_epoch"] = ov["scale_epoch"]
    return out


def select_epoch(manifest: dict[str, Any], received_ms: int, pin: str) -> dict[str, Any]:
    if pin:
        for ep in manifest["scale_epochs"]:
            if ep["epoch_id"] == pin:
                return ep
    chosen = None
    for ep in manifest["scale_epochs"]:
        if int(ep["effective_ms"]) <= received_ms:
            if chosen is None or int(ep["effective_ms"]) >= int(chosen["effective_ms"]):
                chosen = ep
    if chosen is None and manifest["scale_epochs"]:
        return manifest["scale_epochs"][0]
    return chosen or {"epoch_id": "", "factor": 1.0, "offset": 0.0}


def is_stale(received_ms: int, device_clock_ms: int, skew_limit: int) -> bool:
    if skew_limit <= 0:
        return False
    return abs(device_clock_ms - received_ms) > skew_limit


def is_suppressed(manifest: dict[str, Any], frame: dict[str, Any]) -> bool:
    for row in manifest.get("alarm_suppression") or []:
        if row["device_id"] != frame["device_id"] or int(row["register"]) != int(frame["register"]):
            continue
        if int(row["start_ms"]) <= int(frame["received_ms"]) <= int(row["end_ms"]):
            return True
    return False


def engineering(raw: int, epoch: dict[str, Any]) -> float:
    return float(raw) * float(epoch["factor"]) + float(epoch["offset"])


def _normalize_json(value: Any) -> Any:
    if isinstance(value, float) and value == int(value):
        return int(value)
    if isinstance(value, dict):
        return {k: _normalize_json(v) for k, v in sorted(value.items())}
    if isinstance(value, list):
        return [_normalize_json(v) for v in value]
    return value


def catalog_digest(body: dict[str, Any]) -> str:
    payload = {k: v for k, v in body.items() if k != "catalog_digest"}
    raw = json.dumps(_normalize_json(payload), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def reference_catalog(
    manifest: dict[str, Any],
    frames: list[dict[str, Any]],
    *,
    catalog_generation: int = 1,
    staging_generation: int = 1,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    threshold = float(manifest.get("drift_threshold") or 5.0)
    rejected: list[dict[str, Any]] = []
    entries: list[dict[str, Any]] = []
    for fr in frames:
        eff = effective_for_register(manifest, int(fr["register"]))
        if is_stale(int(fr["received_ms"]), int(fr["device_clock_ms"]), int(eff["clock_skew_ms"])):
            rejected.append({"frame_id": fr["frame_id"], "reason": "stale_device_clock"})
            continue
        raw = decode_raw(fr, eff["word_order"])
        ep = select_epoch(manifest, int(fr["received_ms"]), eff["scale_epoch"])
        eng = engineering(raw, ep)
        base = float(manifest["baseline"][str(fr["register"])])
        drift = abs(eng - base)
        suppressed = is_suppressed(manifest, fr)
        drift_alarm = drift > threshold and not suppressed
        entries.append(
            {
                "frame_id": fr["frame_id"],
                "device_id": fr["device_id"],
                "register": int(fr["register"]),
                "raw": raw,
                "engineering": eng,
                "baseline": base,
                "drift": drift,
                "drift_alarm": drift_alarm,
                "suppressed": suppressed,
                "scale_epoch": ep["epoch_id"],
            }
        )
    drift_catalog = {
        "catalog_generation": catalog_generation,
        "staging_generation": staging_generation,
        "entries": entries,
    }
    drift_catalog["catalog_digest"] = catalog_digest(drift_catalog)
    return drift_catalog, rejected


def reference_staging(manifest_path: Path, frames: list[dict[str, Any]], staging_generation: int = 1) -> dict[str, Any]:
    return {
        "frames": frames,
        "frames_digest": compute_frames_digest(frames),
        "manifest_sha256": manifest_sha256(manifest_path),
        "manifest_path": str(manifest_path),
        "staging_generation": staging_generation,
    }


def mutate_manifest_parametrize(manifest: dict[str, Any], seed: int) -> dict[str, Any]:
    m = deepcopy(manifest)
    factor = 0.005 + (seed % 7) * 0.003
    m["scale_epochs"][0]["factor"] = factor
    m["baseline"][next(iter(m["baseline"]))] = 10.0 + seed
    m["clock_skew_ms"] = 1000 + seed * 250
    return m
