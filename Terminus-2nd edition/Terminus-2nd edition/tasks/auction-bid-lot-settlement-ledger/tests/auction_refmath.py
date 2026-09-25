from __future__ import annotations

import hashlib
import json
from pathlib import Path


def load_scenario(scenario: str, fixture_root: Path) -> dict:
    path = fixture_root / "scenarios" / f"{scenario}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def pick_winner(bids: list[dict]) -> dict | None:
    if not bids:
        return None
    ordered = sorted(
        bids,
        key=lambda b: (
            -int(b["amount_cents"]),
            b["bid_ts"],
            int(b["bid_seq"]),
            b["bidder_id"],
        ),
    )
    return ordered[0]


def reference_awards(scenario: str, fixture_root: Path) -> list[dict]:
    sc = load_scenario(scenario, fixture_root)
    lots = {lot["lot_id"]: lot for lot in sc["lots"]}
    bids_by_lot: dict[str, list[dict]] = {}
    for bid in sc["bids"]:
        bids_by_lot.setdefault(bid["lot_id"], []).append(bid)
    awards: list[dict] = []
    for lot_id in sorted(lots):
        lot = lots[lot_id]
        if lot.get("withdrawn"):
            awards.append(
                {
                    "lot_id": lot_id,
                    "status": "withdrawn",
                    "bidder_id": "",
                    "hammer_cents": 0,
                }
            )
            continue
        winner = pick_winner(bids_by_lot.get(lot_id, []))
        if winner is None:
            awards.append(
                {"lot_id": lot_id, "status": "passed", "bidder_id": "", "hammer_cents": 0}
            )
            continue
        if int(winner["amount_cents"]) >= int(lot["reserve_cents"]):
            awards.append(
                {
                    "lot_id": lot_id,
                    "status": "awarded",
                    "bidder_id": winner["bidder_id"],
                    "hammer_cents": int(winner["amount_cents"]),
                }
            )
        else:
            awards.append(
                {"lot_id": lot_id, "status": "passed", "bidder_id": "", "hammer_cents": 0}
            )
    return awards


def premium_cents(hammer: int, tier: str, schedule: dict, override_bps: int | None = None) -> int:
    row = schedule.get(tier) or schedule["standard"]
    rate = int(row["rate_bps"])
    if override_bps is not None:
        rate = override_bps
    prem = hammer * rate // 10000
    cap = int(row["cap_cents"])
    return min(prem, cap)


def reference_invoices(
    scenario: str,
    fixture_root: Path,
    adjudication_pass: int = 1,
    premium_bps_override: int | None = None,
) -> dict:
    sc = load_scenario(scenario, fixture_root)
    schedule = sc["premium_schedule"]
    deposits = {d["bidder_id"]: int(d["deposit_cents"]) for d in sc.get("deposits", [])}
    adj_map: dict[tuple[str, str], int] = {}
    for adj in sc.get("adjustments", []):
        key = (adj["lot_id"], adj["bidder_id"])
        adj_map[key] = adj_map.get(key, 0) + int(adj["adjustment_cents"])
    lots = {lot["lot_id"]: lot for lot in sc["lots"]}
    rem = dict(deposits)
    invoices: list[dict] = []
    for aw in reference_awards(scenario, fixture_root):
        if aw["status"] != "awarded":
            continue
        lot = lots[aw["lot_id"]]
        hammer = int(aw["hammer_cents"])
        prem = premium_cents(hammer, lot["premium_tier"], schedule, premium_bps_override)
        adj = adj_map.get((aw["lot_id"], aw["bidder_id"]), 0)
        subtotal = hammer + prem + adj
        bidder = aw["bidder_id"]
        applied = min(rem.get(bidder, 0), subtotal)
        rem[bidder] = rem.get(bidder, 0) - applied
        invoices.append(
            {
                "lot_id": aw["lot_id"],
                "bidder_id": bidder,
                "hammer_cents": hammer,
                "premium_cents": prem,
                "adjustment_cents": adj,
                "deposit_applied": applied,
                "amount_due_cents": subtotal - applied,
            }
        )
    invoices.sort(key=lambda r: (r["lot_id"], r["bidder_id"]))
    digest = hashlib.sha256(json.dumps(invoices, separators=(",", ":")).encode()).hexdigest()
    return {
        "scenario_id": sc["scenario_id"],
        "adjudication_pass": adjudication_pass,
        "invoices": invoices,
        "ledger_digest": digest,
    }
