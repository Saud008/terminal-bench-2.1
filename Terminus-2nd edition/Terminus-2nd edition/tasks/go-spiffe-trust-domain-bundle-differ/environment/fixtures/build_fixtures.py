"""Fixture catalog builder for spiffectl scenarios — anti-hardcoding via seeded RNG."""
from __future__ import annotations

import hashlib
import json
import os
import random
from pathlib import Path


def _rng(scenario: str) -> random.Random:
    seed = int(hashlib.sha256(scenario.encode()).hexdigest()[:16], 16)
    return random.Random(seed)


def _trust_domain(rng: random.Random) -> str:
    labels = ["mesh", "edge", "api", "workload"]
    tld = rng.choice(["org", "net", "io"])
    host = f"{rng.choice(labels)}.{rng.choice(labels)}.{tld}"
    if rng.random() > 0.5:
        return host.upper()
    return host


def _workload_id(rng: random.Random, td: str) -> str:
    wid = rng.randint(1000, 9999)
    return f"spiffe://{td.lower()}/workload/{wid}"


def _serial(rng: random.Random) -> str:
    n = rng.randint(1, 0xFFFF)
    raw = format(n, "x")
    if rng.random() > 0.5:
        raw = "00" + raw
    return raw.upper() if rng.random() > 0.5 else raw


def _jwks_keys(rng: random.Random) -> list[dict]:
    keys = [
        {"kid": f"enc-{rng.randint(10,99)}", "use": "enc", "alg": "RSA-OAEP-256"},
        {"kid": f"sig-{rng.randint(10,99)}", "use": "sig", "alg": "RS256"},
        {"kid": f"sig-{rng.randint(100,199)}", "use": "sig", "alg": "ES256"},
    ]
    rng.shuffle(keys)
    return keys


def bundle_for(scenario: str, variant: str) -> dict:
    rng = _rng(f"{scenario}:{variant}")
    td = _trust_domain(rng)
    epoch = rng.randint(50, 120)
    return {
        "bundle_epoch": epoch,
        "trust_domain": td if variant == "left" else td.upper(),
        "jwks": {"keys": _jwks_keys(rng)},
        "x509_svid": [
            {
                "serial": _serial(rng),
                "spiffe_id": _workload_id(rng, td),
                "last_seen_epoch": epoch - rng.randint(0, 8),
            }
        ],
        "federation_allowlist": [f"*.{td.split('.')[-2]}.{td.split('.')[-1]}", "partner.example.net"],
    }


def overlay_scenario(scenario: str, left: dict, right: dict) -> tuple[dict, dict]:
    if scenario == "trust-domain-hostfold":
        left["trust_domain"] = "SPIFFE://Mixed.Case.ORG"
        right["trust_domain"] = "spiffe://mixed.case.org"
    elif scenario == "jwks-key-order":
        left["jwks"]["keys"] = [
            {"kid": "z-enc", "use": "enc", "alg": "RSA-OAEP-256"},
            {"kid": "a-sig", "use": "sig", "alg": "RS256"},
            {"kid": "m-sig", "use": "sig", "alg": "ES256"},
        ]
        right["jwks"]["keys"] = list(left["jwks"]["keys"])
    elif scenario == "x509-serial-normalize":
        left["x509_svid"][0]["serial"] = "00ABC0"
        right["x509_svid"][0]["serial"] = "abc0"
    elif scenario == "rotation-window":
        ep = left["bundle_epoch"]
        left["x509_svid"] = [
            {
                "serial": "aa",
                "spiffe_id": "spiffe://example.org/w/in",
                "rotation_epoch": ep - 5,
                "last_seen_epoch": ep - 1,
            },
            {
                "serial": "bb",
                "spiffe_id": "spiffe://example.org/w/edge",
                "rotation_epoch": ep,
                "last_seen_epoch": ep,
            },
        ]
        right["x509_svid"] = list(left["x509_svid"])
    elif scenario == "federation-allowlist":
        left["federation_allowlist"] = ["*.example.org", "partner.example.net"]
        left["trust_domain"] = "api.example.org"
        right["trust_domain"] = "api.example.org"
        right["federation_allowlist"] = ["*.example.org", "other.example.net"]
    elif scenario == "stale-identity":
        ep = left["bundle_epoch"]
        left["x509_svid"] = [
            {"serial": "fresh", "spiffe_id": "spiffe://example.org/workload/fresh", "last_seen_epoch": ep - 1},
            {"serial": "stale", "spiffe_id": "spiffe://example.org/workload/stale", "last_seen_epoch": ep - 10},
        ]
        right["x509_svid"] = list(left["x509_svid"])
    elif scenario == "stable-diff-pair":
        left["x509_svid"] = [
            {"serial": "s1", "spiffe_id": "spiffe://example.org/workload/a", "last_seen_epoch": left["bundle_epoch"] - 1},
            {"serial": "s2", "spiffe_id": "spiffe://example.org/workload/b", "last_seen_epoch": left["bundle_epoch"] - 1},
        ]
        right["x509_svid"] = [
            {"serial": "s1", "spiffe_id": "spiffe://example.org/workload/a", "last_seen_epoch": right["bundle_epoch"] - 1},
            {"serial": "s3", "spiffe_id": "spiffe://example.org/workload/c", "last_seen_epoch": right["bundle_epoch"] - 1},
        ]
    elif scenario == "repeat-atlas":
        pass
    elif scenario == "federation-wildcard-trap":
        left["trust_domain"] = "deep.edge.example.org"
        left["federation_allowlist"] = ["*.example.org"]
        right = json.loads(json.dumps(left))
    elif scenario == "rotation-boundary-trap":
        ep = left["bundle_epoch"]
        left["x509_svid"] = [
            {
                "serial": "bound-min",
                "spiffe_id": "spiffe://example.org/workload/min",
                "rotation_epoch": ep - 5,
                "last_seen_epoch": ep - 1,
            },
            {
                "serial": "bound-max",
                "spiffe_id": "spiffe://example.org/workload/max",
                "rotation_epoch": ep,
                "last_seen_epoch": ep,
            },
        ]
        right["x509_svid"] = list(left["x509_svid"])
    return left, right


def write_scenario(root: Path, scenario: str) -> None:
    left, right = overlay_scenario(scenario, bundle_for(scenario, "left"), bundle_for(scenario, "right"))
    scen_dir = root / "scenarios" / scenario
    scen_dir.mkdir(parents=True, exist_ok=True)
    (scen_dir / "left.json").write_text(json.dumps(left, indent=2) + "\n", encoding="utf-8")
    (scen_dir / "right.json").write_text(json.dumps(right, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    root = Path("/app/fixtures")
    hidden = os.environ.get("TDB_HIDDEN_ROOT")
    if hidden:
        root = Path(hidden)
    for scen_dir in sorted((root / "scenarios").iterdir()):
        if scen_dir.is_dir():
            left_path = scen_dir / "left.json"
            right_path = scen_dir / "right.json"
            if not left_path.exists() or not right_path.exists():
                write_scenario(root, scen_dir.name)
    catalog = {
        "root": str(root),
        "scenarios": sorted(p.name for p in (root / "scenarios").iterdir() if p.is_dir()),
    }
    out = root / "catalog.json"
    out.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out}")

if __name__ == "__main__":
    main()
