#!/usr/bin/env python3
"""Independent reference math for fluxpress residual-occupancy closure."""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any


def load_config(path: str = "/app/config/fluxpress.json") -> dict[str, Any]:
    cfg = json.loads(Path(path).read_text(encoding="utf-8"))
    env = os.environ.get("TB3_MICRON_EV_SCALE")
    if env:
        try:
            n = int(env)
            if n > 0:
                cfg["micron_ev_scale"] = n
        except ValueError:
            pass
    return cfg


def _round_half_away(x: float) -> float:
    return math.floor(x + 0.5) if x >= 0.0 else math.ceil(x - 0.5)


def round6(x: float) -> float:
    return _round_half_away(x * 1_000_000.0) / 1_000_000.0


def quantize(v: float, scale: int) -> float:
    return _round_half_away(v * scale) / scale


def background_at(energy_kev: float, anchors: list[dict[str, float]]) -> float:
    if not anchors:
        return 0.0
    sorted_anchors = sorted(anchors, key=lambda a: a["energy_kev"])
    if energy_kev <= sorted_anchors[0]["energy_kev"]:
        return sorted_anchors[0]["counts"]
    if energy_kev >= sorted_anchors[-1]["energy_kev"]:
        return sorted_anchors[-1]["counts"]
    for a, b in zip(sorted_anchors, sorted_anchors[1:]):
        if a["energy_kev"] <= energy_kev <= b["energy_kev"]:
            if abs(b["energy_kev"] - a["energy_kev"]) < 1e-12:
                return a["counts"]
            frac = (energy_kev - a["energy_kev"]) / (b["energy_kev"] - a["energy_kev"])
            return a["counts"] + (b["counts"] - a["counts"]) * frac
    return sorted_anchors[-1]["counts"]


def residual_counts(measured_counts: float, energy_kev: float, anchors: list[dict[str, float]]) -> float:
    return round6(measured_counts - background_at(energy_kev, anchors))


def is_vetoed(energy_q: float, windows: list[dict[str, float]], scale: int) -> bool:
    for wnd in windows:
        lo_q = quantize(wnd["lo_kev"], scale)
        hi_q = quantize(wnd["hi_kev"], scale)
        if lo_q <= energy_q <= hi_q:
            return True
    return False


def build_channels(bundle: dict[str, Any], cfg: dict[str, Any]) -> list[dict[str, Any]]:
    scale = int(cfg["micron_ev_scale"])
    channels: list[dict[str, Any]] = []
    for ch in bundle["channels"]:
        energy_q = round6(quantize(ch["energy_kev"], scale))
        width_q = round6(quantize(ch["width_kev"], scale))
        vetoed = is_vetoed(energy_q, bundle.get("veto_windows", []), scale)
        residual = 0.0 if vetoed else residual_counts(
            ch["measured_counts"], ch["energy_kev"], bundle["background_anchors"]
        )
        channels.append(
            {
                "channel_id": ch["channel_id"],
                "energy_q": energy_q,
                "residual_counts": float(residual),
                "width_q": width_q,
                "vetoed": bool(vetoed),
            }
        )
    channels.sort(key=lambda c: (c["energy_q"], c["channel_id"]))
    return channels


def scan_occupancy(channels: list[dict[str, Any]]) -> tuple[int, str]:
    survivors = [c for c in channels if not c["vetoed"]]
    if not survivors:
        return 0, ""
    best_index = 0
    best_count = 0
    for i, ch in enumerate(survivors):
        start = ch["energy_q"]
        count = sum(
            1
            for other in survivors
            if other["energy_q"] <= start <= other["energy_q"] + other["width_q"]
        )
        if count > best_count:
            best_count = count
            best_index = i
    return best_count, survivors[best_index]["channel_id"]


def rank_channels(channels: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [
        {"channel_id": c["channel_id"], "residual_counts": c["residual_counts"], "vetoed": False}
        for c in channels
        if not c["vetoed"]
    ]
    rows.sort(key=lambda r: (-r["residual_counts"], r["channel_id"]))
    for i, r in enumerate(rows):
        r["rank"] = i + 1
    return rows


def closure_digest(atlas_without_digest: dict[str, Any]) -> str:
    body = json.dumps(atlas_without_digest, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def expected_atlas(
    campaign_id: str,
    bundle: dict[str, Any],
    cfg: dict[str, Any],
    aperture_delta: int = 0,
) -> dict[str, Any]:
    channels = build_channels(bundle, cfg)
    max_occupancy, peak_channel_id = scan_occupancy(channels)
    effective_aperture = max(1, int(bundle["aperture_budget"]) + aperture_delta)
    spill_risk = max_occupancy > effective_aperture
    channel_order = [c["channel_id"] for c in channels if not c["vetoed"]]
    rows = rank_channels(channels)
    atlas: dict[str, Any] = {
        "campaign_id": campaign_id,
        "effective_aperture": effective_aperture,
        "channel_order": channel_order,
        "max_occupancy": max_occupancy,
        "peak_channel_id": peak_channel_id,
        "spill_risk": bool(spill_risk),
        "rows": rows,
    }
    atlas["closure_digest"] = closure_digest(atlas)
    return atlas


def build_ledger(
    campaign_id: str,
    bundle_name: str,
    bundle: dict[str, Any],
    cfg: dict[str, Any],
    accrual_epoch: int,
) -> dict[str, Any]:
    channels = build_channels(bundle, cfg)
    return {
        "accrual_epoch": accrual_epoch,
        "campaign_id": campaign_id,
        "bundle": bundle_name,
        "micron_ev_scale": int(cfg["micron_ev_scale"]),
        "aperture_budget": int(bundle["aperture_budget"]),
        "dwell_width_kev": float(bundle["dwell_width_kev"]),
        "channels": channels,
    }


def load_bundle(bundle_dir: str, name: str) -> dict[str, Any]:
    return json.loads(Path(bundle_dir, f"{name}.json").read_text(encoding="utf-8"))


def reference_atlas(
    campaign_id: str,
    bundle: dict[str, Any],
    cfg: dict[str, Any],
    aperture_delta: int = 0,
) -> dict[str, Any]:
    """Independent reference oracle alias used by pytest (terminus probe naming)."""
    return expected_atlas(campaign_id, bundle, cfg, aperture_delta=aperture_delta)
