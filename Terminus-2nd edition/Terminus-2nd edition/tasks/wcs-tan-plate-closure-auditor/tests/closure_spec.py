"""Independent plate-closure reference math for verifier assertions."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

REJECT = 0x04


def half_up6(v: float) -> float:
    return math.floor(v * 1e6 + 0.5) / 1e6


def parse_cards(cards: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for card in cards:
        if "=" not in card:
            continue
        key, val = card.split("=", 1)
        out[key.strip()] = val.strip().strip("'")
    return out


def project(cards: dict[str, str], x: float, y: float) -> tuple[float, float]:
    crpix1 = float(cards["CRPIX1"])
    crpix2 = float(cards["CRPIX2"])
    crval1 = float(cards["CRVAL1"])
    crval2 = float(cards["CRVAL2"])
    cd11 = float(cards["CD1_1"])
    cd12 = float(cards["CD1_2"])
    cd21 = float(cards["CD2_1"])
    cd22 = float(cards["CD2_2"])
    xi = x - crpix1
    eta = y - crpix2
    return crval1 + cd11 * xi + cd12 * eta, crval2 + cd21 * xi + cd22 * eta


def nudge_ra(ra: float, star_epoch: float, plate_epoch: float) -> float:
    return ra + (0.012 * (star_epoch - plate_epoch)) / 3600.0


def closure_digest(scenario_id: str, star_ids: list[str], rms_ra: float, rms_dec: float) -> str:
    ids = sorted(star_ids)
    stars_json = json.dumps(ids, separators=(",", ":"), ensure_ascii=False)
    raw = (
        f'{{"scenario_id":{json.dumps(scenario_id)},'
        f'"active_count":{len(ids)},'
        f'"star_ids":{stars_json},'
        f'"rms_ra_arcsec":{rms_ra:.6f},'
        f'"rms_dec_arcsec":{rms_dec:.6f}}}'
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def reference_certificate(scenario_path: Path, match_override: float | None = None) -> dict:
    body = json.loads(scenario_path.read_text(encoding="utf-8"))
    cards = parse_cards(body["header_cards"])
    plate_epoch = float(cards["EPOCH"])
    tol = float(body.get("match_arcsec", 2.5))
    if match_override is not None:
        tol = match_override
    rows = []
    for star in body["stars"]:
        if (int(star["det_mask"]) | int(star["cat_mask"])) & REJECT:
            continue
        pra, pdec = project(cards, float(star["x_pixel"]), float(star["y_pixel"]))
        target = nudge_ra(float(star["ra_deg"]), float(star["epoch_year"]), plate_epoch)
        dra = (pra - target) * 3600.0
        ddec = (pdec - float(star["dec_deg"])) * 3600.0
        sep = math.hypot(dra, ddec)
        if sep <= tol:
            rows.append((star["star_id"], dra, ddec, sep))
    rows.sort(key=lambda r: r[0])
    if not rows:
        raise AssertionError(f"no active rows for {scenario_path}")
    rms_ra = half_up6(math.sqrt(sum(r[1] * r[1] for r in rows) / len(rows)))
    rms_dec = half_up6(math.sqrt(sum(r[2] * r[2] for r in rows) / len(rows)))
    ids = [r[0] for r in rows]
    klass = "tight" if rms_ra < 0.35 and rms_dec < 0.35 else "loose"
    return {
        "scenario_id": body["scenario_id"],
        "matched_count": len(rows),
        "active_count": len(rows),
        "rms_ra_arcsec": rms_ra,
        "rms_dec_arcsec": rms_dec,
        "closure_class": klass,
        "stars": ids,
        "closure_digest": closure_digest(body["scenario_id"], ids, rms_ra, rms_dec),
    }
