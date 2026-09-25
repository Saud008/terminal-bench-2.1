#!/usr/bin/env python3
"""Fixture catalog builder for termsetctl public scenarios — anti-hardcoding via seeded RNG."""
from __future__ import annotations

import hashlib
import hmac
import json
import random
from pathlib import Path


BUNDLED = (
    "clean-settle",
    "reversal-pair",
    "cutoff-window",
    "seq-strict",
    "multi-merchant",
    "stale-reversal",
    "hmac-republish",
)


def _rng(scenario: str) -> random.Random:
    seed = int(hashlib.sha256(scenario.encode()).hexdigest()[:16], 16)
    return random.Random(seed)


def _terminal_key_hex(scenario: str, salt: str = "") -> str:
    material = f"termset-key:{scenario}:{salt}"
    return hashlib.sha256(material.encode()).hexdigest()


def _attestation_probe(key_hex: str, journal_digest: str) -> str:
    key = bytes.fromhex(key_hex)
    return hmac.new(key, journal_digest.encode(), hashlib.sha256).hexdigest()


def _scenario_body(scenario: str, rng: random.Random, salt: str = "") -> dict:
    batch_id = f"batch-{scenario[:8]}"
    terminal_key_id = f"tk-{rng.randint(1000, 9999)}"
    merchant_a = f"mer-{rng.randint(100, 999)}"
    merchant_b = f"mer-{rng.randint(1000, 1999)}"
    terminal_a = f"term-{rng.randint(10, 99)}"
    terminal_b = f"term-{rng.randint(100, 199)}"
    base_ms = rng.randint(1_700_000_000_000, 1_700_005_000_000)
    cutoff_ms = base_ms + 3_600_000
    auth_sale = f"{rng.randint(0x100000, 0xffffff):06x}"
    auth_other = f"{rng.randint(0x100000, 0xffffff):06x}"

    transcripts: list[dict] = []

    if scenario == "clean-settle":
        transcripts = [
            {
                "batch_id": batch_id,
                "terminal_key_id": terminal_key_id,
                "merchant_id": merchant_a,
                "terminal_id": terminal_a,
                "txn_id": f"txn-{scenario}-1",
                "auth_code": auth_sale.upper(),
                "amount_cents": 2500,
                "txn_type": "sale",
                "links_sale_id": "",
                "event_ms": base_ms,
            },
            {
                "batch_id": batch_id,
                "terminal_key_id": terminal_key_id,
                "merchant_id": merchant_a,
                "terminal_id": terminal_a,
                "txn_id": f"txn-{scenario}-2",
                "auth_code": auth_other.upper(),
                "amount_cents": 1100,
                "txn_type": "sale",
                "links_sale_id": "",
                "event_ms": base_ms + 60_000,
            },
        ]
    elif scenario == "reversal-pair":
        sale_id = f"txn-{scenario}-sale"
        transcripts = [
            {
                "batch_id": batch_id,
                "terminal_key_id": terminal_key_id,
                "merchant_id": merchant_a,
                "terminal_id": terminal_a,
                "txn_id": sale_id,
                "auth_code": auth_sale.upper(),
                "amount_cents": 4200,
                "txn_type": "sale",
                "links_sale_id": "",
                "event_ms": base_ms,
            },
            {
                "batch_id": batch_id,
                "terminal_key_id": terminal_key_id,
                "merchant_id": merchant_a,
                "terminal_id": terminal_a,
                "txn_id": f"txn-{scenario}-rev",
                "auth_code": auth_sale.upper(),
                "amount_cents": 4200,
                "txn_type": "reversal",
                "links_sale_id": sale_id,
                "event_ms": base_ms + 120_000,
            },
        ]
    elif scenario == "cutoff-window":
        transcripts = [
            {
                "batch_id": batch_id,
                "terminal_key_id": terminal_key_id,
                "merchant_id": merchant_a,
                "terminal_id": terminal_a,
                "txn_id": f"txn-{scenario}-in",
                "auth_code": auth_sale.upper(),
                "amount_cents": 900,
                "txn_type": "sale",
                "links_sale_id": "",
                "event_ms": cutoff_ms,
            },
            {
                "batch_id": batch_id,
                "terminal_key_id": terminal_key_id,
                "merchant_id": merchant_a,
                "terminal_id": terminal_a,
                "txn_id": f"txn-{scenario}-out",
                "auth_code": auth_other.upper(),
                "amount_cents": 500,
                "txn_type": "sale",
                "links_sale_id": "",
                "event_ms": cutoff_ms + 1,
            },
        ]
    elif scenario == "seq-strict":
        transcripts = [
            {
                "batch_id": batch_id,
                "terminal_key_id": terminal_key_id,
                "merchant_id": merchant_a,
                "terminal_id": terminal_a,
                "txn_id": f"txn-{scenario}-b",
                "auth_code": auth_other.upper(),
                "amount_cents": 300,
                "txn_type": "sale",
                "links_sale_id": "",
                "event_ms": base_ms + 30_000,
            },
            {
                "batch_id": batch_id,
                "terminal_key_id": terminal_key_id,
                "merchant_id": merchant_b,
                "terminal_id": terminal_b,
                "txn_id": f"txn-{scenario}-a",
                "auth_code": auth_sale.upper(),
                "amount_cents": 700,
                "txn_type": "sale",
                "links_sale_id": "",
                "event_ms": base_ms,
            },
        ]
    elif scenario == "multi-merchant":
        transcripts = [
            {
                "batch_id": batch_id,
                "terminal_key_id": terminal_key_id,
                "merchant_id": merchant_a,
                "terminal_id": terminal_a,
                "txn_id": f"txn-{scenario}-a",
                "auth_code": auth_sale.upper(),
                "amount_cents": 1500,
                "txn_type": "sale",
                "links_sale_id": "",
                "event_ms": base_ms,
            },
            {
                "batch_id": batch_id,
                "terminal_key_id": terminal_key_id,
                "merchant_id": merchant_b,
                "terminal_id": terminal_b,
                "txn_id": f"txn-{scenario}-b",
                "auth_code": auth_other.upper(),
                "amount_cents": 2200,
                "txn_type": "sale",
                "links_sale_id": "",
                "event_ms": base_ms + 45_000,
            },
        ]
    elif scenario == "stale-reversal":
        transcripts = [
            {
                "batch_id": batch_id,
                "terminal_key_id": terminal_key_id,
                "merchant_id": merchant_a,
                "terminal_id": terminal_a,
                "txn_id": f"txn-{scenario}-orphan",
                "auth_code": auth_sale.upper(),
                "amount_cents": 1800,
                "txn_type": "reversal",
                "links_sale_id": "txn-missing-sale",
                "event_ms": base_ms,
            },
        ]
    elif scenario == "hmac-republish":
        transcripts = [
            {
                "batch_id": batch_id,
                "terminal_key_id": terminal_key_id,
                "merchant_id": merchant_a,
                "terminal_id": terminal_a,
                "txn_id": f"txn-{scenario}-1",
                "auth_code": auth_sale.upper(),
                "amount_cents": 3300,
                "txn_type": "sale",
                "links_sale_id": "",
                "event_ms": base_ms,
            },
        ]
    else:
        transcripts = []

    return {
        "scenario": scenario,
        "batch_id": batch_id,
        "terminal_key_id": terminal_key_id,
        "cutoff_event_ms": cutoff_ms,
        "terminal_key_hex": _terminal_key_hex(scenario, salt),
        "transcripts": transcripts,
    }


def _write_scenario(root: Path, scenario: str) -> None:
    rng = _rng(scenario)
    body = _scenario_body(scenario, rng, salt="")
    if body.get("terminal_key_hex") and body.get("transcripts"):
        probe_digest = hashlib.sha256(scenario.encode()).hexdigest()
        _attestation_probe(body["terminal_key_hex"], probe_digest)
    out_dir = root / "scenarios"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{scenario}.json"
    path.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    base = Path("/app/fixtures")
    if not Path("/app").exists():
        base = Path(__file__).resolve().parent
    for name in BUNDLED:
        _write_scenario(base, name)


if __name__ == "__main__":
    main()
