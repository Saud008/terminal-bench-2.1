"""Independent expected math for spectrum license bundle validation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def point_in_bbox(lat: float, lon: float, area: dict[str, float]) -> bool:
    return (
        area["lat_min"] <= lat <= area["lat_max"]
        and area["lon_min"] <= lon <= area["lon_max"]
    )


def bands_overlap(a_low: float, a_high: float, b_low: float, b_high: float) -> bool:
    return a_low <= b_high and b_low <= a_high


def license_valid(renewal_date: str, as_of_date: str) -> bool:
    return renewal_date >= as_of_date


def pick_license(site: dict[str, Any], licenses: list[dict[str, Any]]) -> dict[str, Any] | None:
    declared = site.get("license_id") or ""
    if declared:
        for lic in licenses:
            if (
                lic["license_id"] == declared
                and lic["band_id"] == site["band_id"]
                and point_in_bbox(site["lat"], site["lon"], lic["area"])
            ):
                return lic
        return None
    best: dict[str, Any] | None = None
    for lic in licenses:
        if lic["band_id"] != site["band_id"]:
            continue
        if not point_in_bbox(site["lat"], site["lon"], lic["area"]):
            continue
        if best is None or lic["priority"] > best["priority"]:
            best = lic
    return best


def site_excluded(site: dict[str, Any], exclusions: list[dict[str, Any]]) -> bool:
    for ex in exclusions:
        if ex["band_id"] != site["band_id"]:
            continue
        if point_in_bbox(site["lat"], site["lon"], ex["area"]):
            return True
    return False


def count_band_peers(band_id: str, mhz_low: float, mhz_high: float, bands: list[dict[str, Any]]) -> int:
    n = 0
    for b in bands:
        if b["band_id"] == band_id:
            continue
        if bands_overlap(mhz_low, mhz_high, b["mhz_low"], b["mhz_high"]):
            n += 1
    return n


def scoped_atlas_seq_id(seed: str, bundle: str, gen: int) -> str:
    body = f"{seed}:{bundle}:{gen}".encode()
    return "atl-" + hashlib.sha256(body).hexdigest()[:12]


def load_bundle(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_catalog_rows(bundle: dict[str, Any], atlas_seq_id: str) -> tuple[list[dict[str, Any]], dict[str, int]]:
    bands = bundle["bands"]
    band_map = {b["band_id"]: b for b in bands}
    expired_dropped = 0
    rows: list[dict[str, Any]] = []
    for site in bundle["transmitters"]:
        lic = pick_license(site, bundle["licenses"])
        if lic is None:
            continue
        if not license_valid(lic["renewal_date"], bundle["as_of_date"]):
            expired_dropped += 1
            continue
        band = band_map[site["band_id"]]
        peers = count_band_peers(site["band_id"], band["mhz_low"], band["mhz_high"], bands)
        rows.append(
            {
                "site_id": site["site_id"],
                "license_id": lic["license_id"],
                "holder": lic["holder"],
                "band_id": site["band_id"],
                "effective_mhz_low": band["mhz_low"],
                "effective_mhz_high": band["mhz_high"],
                "excluded": site_excluded(site, bundle["exclusions"]),
                "overlap_peer_count": peers,
                "valid_through": lic["renewal_date"],
                "atlas_seq_id": atlas_seq_id,
            }
        )
    rows.sort(key=lambda r: (r["holder"], r["band_id"], r["site_id"]))
    return rows, {"expired_dropped": expired_dropped}


def count_overlap_pairs(rows: list[dict[str, Any]]) -> int:
    n = 0
    for i, a in enumerate(rows):
        for b in rows[i + 1 :]:
            if a["band_id"] != b["band_id"] and bands_overlap(
                a["effective_mhz_low"],
                a["effective_mhz_high"],
                b["effective_mhz_low"],
                b["effective_mhz_high"],
            ):
                n += 1
    return n


def audit_digest(summary: dict[str, Any]) -> str:
    body = json.dumps(
        {
            "active_sites": summary["active_sites"],
            "expired_dropped": summary["expired_dropped"],
            "overlap_pairs": summary["overlap_pairs"],
            "total_sites": summary["total_sites"],
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(body.encode()).hexdigest()


def reference_atlas(
    seed: str,
    bundle_name: str,
    bundle_path: Path,
    load_generation: int,
) -> dict[str, Any]:
    bundle = load_bundle(bundle_path)
    cov_id = scoped_atlas_seq_id(seed, bundle_name, load_generation)
    rows, extra = build_catalog_rows(bundle, cov_id)
    excluded = sum(1 for r in rows if r["excluded"])
    summary = {
        "total_sites": len(rows),
        "active_sites": len(rows) - excluded,
        "excluded_sites": excluded,
        "overlap_pairs": count_overlap_pairs(rows),
        "expired_dropped": extra["expired_dropped"],
    }
    return {
        "seed": seed,
        "bundle": bundle_name,
        "atlas_seq_id": cov_id,
        "catalog_rows": rows,
        "summary": summary,
        "audit_digest": audit_digest(summary),
    }


if __name__ == "__main__":
    import sys

    p = Path(sys.argv[1])
    print(json.dumps(reference_atlas("seed-alpha", p.stem, p, 1), indent=2))
