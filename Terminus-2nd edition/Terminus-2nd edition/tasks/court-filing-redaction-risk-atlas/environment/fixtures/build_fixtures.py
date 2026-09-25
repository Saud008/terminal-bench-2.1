#!/usr/bin/env python3
"""Fixture catalog builder for filingatlas — anti-hardcoding via seeded RNG."""
from __future__ import annotations

import hashlib
import json
import os
import random
from pathlib import Path


def _rng(scenario: str) -> random.Random:
    seed = int(hashlib.sha256(scenario.encode()).hexdigest()[:16], 16)
    return random.Random(seed)


def _party_name(rng: random.Random) -> str:
    return f"{rng.choice(['Acme', 'Beta', 'Delta', 'Echo'])} {rng.choice(['Corp', 'LLC', 'AG', 'Trust'])}"


def _docket(rng: random.Random) -> str:
    return f"CV-{rng.randint(2020, 2029)}-{rng.randint(100, 999):03d}"


def overlay(scenario: str, policy: dict, dockets: list, parties: list, pages: list, sealed: list) -> tuple:
    rng = _rng(scenario)
    policy = dict(policy)
    policy["court_id"] = f"DIST-{rng.randint(10, 99)}"
    for d in dockets:
        if not d.get("primary_flag"):
            d["number"] = _docket(rng)
    # Party names and page text stay paired per scenario; only non-primary dockets vary.
    return policy, dockets, parties, pages, sealed


def write_scenario(root: Path, scenario: str) -> None:
    scen_dir = root / "scenarios" / scenario
    if not scen_dir.is_dir():
        return
    policy = json.loads((scen_dir / "policy.json").read_text(encoding="utf-8"))
    dockets = [json.loads(line) for line in (scen_dir / "dockets.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    parties_wrap = json.loads((scen_dir / "parties.json").read_text(encoding="utf-8"))
    pages = [json.loads(line) for line in (scen_dir / "pages.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    sealed_wrap = json.loads((scen_dir / "sealed_terms.json").read_text(encoding="utf-8"))
    policy, dockets, parties_wrap["parties"], pages, sealed_wrap["terms"] = overlay(
        scenario, policy, dockets, parties_wrap["parties"], pages, sealed_wrap["terms"]
    )
    (scen_dir / "policy.json").write_text(json.dumps(policy, indent=2) + "\n", encoding="utf-8")
    (scen_dir / "dockets.jsonl").write_text("\n".join(json.dumps(r, separators=(",", ":")) for r in dockets) + "\n", encoding="utf-8")
    (scen_dir / "parties.json").write_text(json.dumps(parties_wrap, indent=2) + "\n", encoding="utf-8")
    (scen_dir / "pages.jsonl").write_text("\n".join(json.dumps(r, separators=(",", ":")) for r in pages) + "\n", encoding="utf-8")
    (scen_dir / "sealed_terms.json").write_text(json.dumps(sealed_wrap, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    root = Path("/app/fixtures")
    hidden = os.environ.get("FILING_HIDDEN_ROOT")
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
