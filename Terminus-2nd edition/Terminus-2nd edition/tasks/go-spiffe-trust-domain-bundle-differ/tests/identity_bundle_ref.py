"""Independent SPIFFE trust-domain bundle refmath for spiffectl."""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

DEFAULT_ROT_WINDOW = 5
STALE_THRESHOLD = 3


def rot_window() -> int:
    raw = os.environ.get("TB3_ROT_WINDOW", "")
    if raw:
        return int(raw)
    return DEFAULT_ROT_WINDOW


def load_pair(fixture_root: Path, scenario: str) -> tuple[dict[str, Any], dict[str, Any]]:
    base = fixture_root / "scenarios" / scenario
    left = json.loads((base / "left.json").read_text(encoding="utf-8"))
    right = json.loads((base / "right.json").read_text(encoding="utf-8"))
    return left, right


def bundle_canon_keys(bundle: dict[str, Any]) -> dict[str, Any]:
    svids = []
    for s in bundle.get("x509_svid", []):
        entry: dict[str, Any] = {
            "serial": s["serial"],
            "spiffe_id": s["spiffe_id"],
        }
        if "rotation_epoch" in s:
            entry["rotation_epoch"] = int(s["rotation_epoch"])
        entry["last_seen_epoch"] = int(s["last_seen_epoch"])
        svids.append(entry)
    return {
        "bundle_epoch": int(bundle["bundle_epoch"]),
        "trust_domain": bundle["trust_domain"],
        "jwks": bundle["jwks"],
        "x509_svid": svids,
        "federation_allowlist": bundle.get("federation_allowlist", []),
    }


def expected_pair_capture(scenario: str, fixture_root: Path) -> dict[str, Any]:
    left, right = load_pair(fixture_root, scenario)
    left_c = bundle_canon_keys(left)
    right_c = bundle_canon_keys(right)
    payload = {"left": left_c, "right": right_c, "scenario": scenario}
    digest = hashlib.sha256(json.dumps(payload, separators=(",", ":")).encode()).hexdigest()
    return {
        "engine": "spiffectl",
        "scenario": scenario,
        "left": left_c,
        "right": right_c,
        "capture_digest": digest,
    }


def canonical_trust_domain(raw: str) -> str:
    td = raw.strip()
    if td.lower().startswith("spiffe://"):
        td = td[len("spiffe://") :]
    return td.lower()


def canonical_spiffe_id(raw: str) -> str:
    ident = raw.strip()
    if not ident.lower().startswith("spiffe://"):
        ident = "spiffe://" + ident
    host_end = ident.find("/", 9)
    if host_end == -1:
        return ident.lower()
    host = ident[9:host_end].lower()
    return "spiffe://" + host + ident[host_end:].lower()


def order_jwks_keys(keys: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sig = sorted([k for k in keys if k.get("use") == "sig"], key=lambda k: k["kid"])
    enc = sorted([k for k in keys if k.get("use") == "enc"], key=lambda k: k["kid"])
    return sig + enc


def normalize_serial(raw: str) -> str:
    s = raw.strip().lower()
    s = re.sub(r"^0+(?=.)", "", s)
    return s or "0"


def in_rotation_window(epoch: int, bundle_epoch: int) -> bool:
    win = rot_window()
    lo = bundle_epoch - win
    hi = bundle_epoch
    return lo <= epoch <= hi


def wildcard_match(host: str, pattern: str) -> bool:
    host = host.lower().strip()
    pat = pattern.lower().strip()
    if pat.startswith("*."):
        suffix = pat[1:]
        return host.endswith(suffix) or host == pat[2:]
    return host == pat


def filter_federation(host: str, allowlist: list[str]) -> list[str]:
    out = [p for p in allowlist if wildcard_match(host, p)]
    return sorted(out)


def drop_stale(svids: list[dict[str, Any]], bundle_epoch: int) -> list[dict[str, Any]]:
    cutoff = bundle_epoch - STALE_THRESHOLD
    kept = [s for s in svids if int(s["last_seen_epoch"]) >= cutoff]
    return sorted(kept, key=lambda s: s["spiffe_id"])


def normalize_trust_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    out = json.loads(json.dumps(bundle))
    out["trust_domain"] = canonical_trust_domain(out["trust_domain"])
    out["jwks"]["keys"] = order_jwks_keys(out.get("jwks", {}).get("keys", []))
    svids: list[dict[str, Any]] = []
    for s in out.get("x509_svid", []):
        rot_epoch = int(s.get("rotation_epoch") or s["last_seen_epoch"])
        if not in_rotation_window(rot_epoch, int(out["bundle_epoch"])):
            continue
        svids.append(
            {
                "serial": normalize_serial(s["serial"]),
                "spiffe_id": canonical_spiffe_id(s["spiffe_id"]),
                "rotation_epoch": rot_epoch,
                "last_seen_epoch": int(s["last_seen_epoch"]),
            }
        )
    out["x509_svid"] = drop_stale(svids, int(out["bundle_epoch"]))
    out["federation_allowlist"] = filter_federation(out["trust_domain"], out.get("federation_allowlist", []))
    return out


def svid_map(bundle: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for s in bundle.get("x509_svid", []):
        out[s["spiffe_id"]] = s["serial"] + ":" + s["spiffe_id"]
    return out


def build_changes(left: dict[str, Any], right: dict[str, Any]) -> list[dict[str, Any]]:
    left_map = svid_map(left)
    right_map = svid_map(right)
    changes: list[dict[str, Any]] = []
    for sid, rv in right_map.items():
        if sid not in left_map:
            changes.append({"path": f"/x509_svid/{sid}", "change_type": "added", "right_value": rv})
        elif left_map[sid] != rv:
            changes.append(
                {
                    "path": f"/x509_svid/{sid}",
                    "change_type": "modified",
                    "left_value": left_map[sid],
                    "right_value": rv,
                }
            )
    for sid, lv in left_map.items():
        if sid not in right_map:
            changes.append({"path": f"/x509_svid/{sid}", "change_type": "removed", "left_value": lv})
    if left.get("trust_domain") != right.get("trust_domain"):
        changes.append(
            {
                "path": "/trust_domain",
                "change_type": "modified",
                "left_value": left["trust_domain"],
                "right_value": right["trust_domain"],
            }
        )
    changes.sort(key=lambda c: c["path"])
    return changes


def report_digest(report: dict[str, Any]) -> str:
    payload = {
        "change_count": report["change_count"],
        "changes": report["changes"],
        "scenario": report["scenario"],
    }
    return hashlib.sha256(json.dumps(payload, separators=(",", ":")).encode()).hexdigest()


def expected_federation_atlas(scenario: str, fixture_root: Path) -> dict[str, Any]:
    left, right = load_pair(fixture_root, scenario)
    norm_left = normalize_trust_bundle(left)
    norm_right = normalize_trust_bundle(right)
    changes = build_changes(norm_left, norm_right)
    report = {"scenario": scenario, "change_count": len(changes), "changes": changes}
    report["report_digest"] = report_digest(report)
    return report
