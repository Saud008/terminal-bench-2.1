#!/usr/bin/env python3
"""Fixture catalog builder for oidcgov — anti-hardcoding via seeded RNG."""
from __future__ import annotations

import hashlib
import json
import os
import random
from pathlib import Path


def _rng(scenario: str) -> random.Random:
    seed = int(hashlib.sha256(scenario.encode()).hexdigest()[:16], 16)
    return random.Random(seed)


def _issuer(rng: random.Random) -> str:
    sub = rng.choice(["auth", "login", "idp"])
    tld = rng.choice(["net", "io", "org"])
    return f"https://{sub}.{rng.choice(['example', 'corp', 'mesh'])}.{tld}"


def _audience(rng: random.Random) -> str:
    return f"{rng.choice(['api', 'svc', 'gateway'])}.{rng.choice(['example', 'corp'])}.net"


def _kid(rng: random.Random) -> str:
    return f"{rng.choice(['sig', 'key', 'kid'])}-{rng.randint(1000, 9999)}"


def overlay(scenario: str, policy: dict, timeline: list, tokens: list) -> tuple[dict, list, list]:
    rng = _rng(scenario)
    policy = dict(policy)
    policy["issuer"] = _issuer(rng)
    policy["audiences"] = [_audience(rng)]
    for tok in tokens:
        tok["iss"] = policy["issuer"]
        if scenario == "issuer-audience-bind" and tok.get("token_id") == "bad-aud":
            continue
        tok["aud"] = list(policy["audiences"])
        if scenario != "kid-casefold-lookup" and rng.random() > 0.5:
            tok["kid"] = tok["kid"].upper()
    return policy, timeline, tokens


def write_scenario(root: Path, scenario: str) -> None:
    scen_dir = root / "scenarios" / scenario
    if not scen_dir.is_dir():
        return
    policy = json.loads((scen_dir / "policy.json").read_text(encoding="utf-8"))
    timeline = [json.loads(line) for line in (scen_dir / "jwks_timeline.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    tokens = [json.loads(line) for line in (scen_dir / "token_batch.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    policy, timeline, tokens = overlay(scenario, policy, timeline, tokens)
    (scen_dir / "policy.json").write_text(json.dumps(policy, indent=2) + "\n", encoding="utf-8")
    (scen_dir / "jwks_timeline.jsonl").write_text("\n".join(json.dumps(r, separators=(",", ":")) for r in timeline) + "\n", encoding="utf-8")
    (scen_dir / "token_batch.jsonl").write_text("\n".join(json.dumps(r, separators=(",", ":")) for r in tokens) + "\n", encoding="utf-8")


def main() -> None:
    root = Path("/app/fixtures")
    hidden = os.environ.get("OIDC_HIDDEN_ROOT")
    if hidden:
        root = Path(hidden)
    for scen_dir in sorted((root / "scenarios").iterdir()):
        if scen_dir.is_dir():
            write_scenario(root, scen_dir.name)
    catalog = {"root": str(root), "scenarios": sorted(p.name for p in (root / "scenarios").iterdir() if p.is_dir())}
    (root / "catalog.json").write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {root / 'catalog.json'}")


if __name__ == "__main__":
    main()
