from __future__ import annotations

import hashlib
import json
from datetime import date, timedelta
from pathlib import Path


def load_scenario(scenario: str, fixture_root: Path) -> dict:
    path = fixture_root / "cycles" / f"{scenario}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def parse_day(s: str) -> date:
    y, m, d = (int(x) for x in s.split("-"))
    return date(y, m, d)


def inclusive_days(start: str, end: str) -> int:
    a, b = parse_day(start), parse_day(end)
    if b < a:
        return 0
    return (b - a).days + 1


def day_str(d: date) -> str:
    return d.isoformat()


def build_segments(sc: dict) -> list[dict]:
    cycle_start = sc["cycle_start"]
    cycle_end = sc["cycle_end"]
    initial = sc["initial_plan"]
    changes = [e for e in sc.get("events", []) if e["event_type"] == "plan_change"]
    changes.sort(key=lambda e: e["event_date"])
    cycle_days = inclusive_days(cycle_start, cycle_end)
    plans = sc["plans"]
    bounds = [cycle_start] + [c["event_date"] for c in changes] + [cycle_end]
    plan_ids = [initial] + [c["to_plan"] for c in changes]
    shifts = sc.get("anchor_shifts") or []
    segments: list[dict] = []
    for i, plan_id in enumerate(plan_ids):
        seg_start = bounds[i]
        if i + 1 < len(bounds) - 0:
            next_bound = bounds[i + 1]
            if i < len(plan_ids) - 1:
                seg_end = day_str(parse_day(next_bound) - timedelta(days=1))
            else:
                seg_end = cycle_end
        else:
            seg_end = cycle_end
        seg_end = adjust_window_end(seg_start, seg_end, cycle_end, shifts)
        monthly = int(plans[plan_id]["monthly_cents"])
        seg_days = inclusive_days(seg_start, seg_end)
        base = monthly * seg_days // cycle_days if cycle_days else 0
        if i > 0:
            prev = changes[i - 1]
            credit = proration_credit(int(plans[prev["from_plan"]]["monthly_cents"]), prev["event_date"], cycle_end, cycle_days)
            base -= credit
        segments.append(
            {
                "segment_index": i,
                "plan_id": plan_id,
                "window_start": seg_start,
                "window_end": seg_end,
                "segment_days": seg_days,
                "base_cents": base,
            }
        )
    return segments


def adjust_window_end(window_start: str, window_end: str, cycle_end: str, shifts: list[dict]) -> str:
    end = parse_day(window_end)
    we = parse_day(window_end)
    for sh in sorted(shifts, key=lambda s: s["effective_date"]):
        eff = parse_day(sh["effective_date"])
        if eff > we:
            continue
        anchor_day = int(sh["new_anchor_day"])
        y, m, _ = (int(x) for x in sh["effective_date"].split("-"))
        candidate = date(y, m, min(anchor_day, 28))
        while candidate < eff:
            if m == 12:
                y, m = y + 1, 1
            else:
                m += 1
            candidate = date(y, m, min(anchor_day, 28))
        if candidate <= end and candidate <= parse_day(cycle_end):
            end = candidate
    return day_str(end)


def proration_credit(old_monthly: int, change_date: str, cycle_end: str, cycle_days: int) -> int:
    rem = inclusive_days(change_date, cycle_end)
    if cycle_days <= 0:
        return 0
    return old_monthly * rem // cycle_days


def usage_in_segment(sc: dict, seg_start: str, seg_end: str) -> int:
    total = 0
    for ev in sc.get("events", []):
        if ev["event_type"] != "usage":
            continue
        d = ev["event_date"]
        if seg_start <= d <= seg_end:
            total += int(ev["units"])
    return total


def is_downgrade(from_plan: str, to_plan: str, plans: dict) -> bool:
    return int(plans[to_plan]["monthly_cents"]) < int(plans[from_plan]["monthly_cents"])


def apply_coupons(subtotal: int, coupons: list[dict]) -> int:
    if subtotal <= 0 or not coupons:
        return 0
    ordered = sorted(coupons, key=lambda c: int(c["precedence"]))
    non_stack = [c for c in ordered if not c.get("stackable")]
    stack = [c for c in ordered if c.get("stackable")]
    discount = 0
    remaining = subtotal
    if non_stack:
        best = 0
        for c in non_stack:
            best = max(best, coupon_amount(subtotal, c))
        discount += best
        remaining = subtotal - best
    for c in stack:
        d = coupon_amount(remaining, c)
        discount += d
        remaining -= d
        remaining = max(remaining, 0)
    return min(discount, subtotal)


def coupon_amount(base: int, c: dict) -> int:
    if c["kind"] == "percent":
        return base * int(c["value"]) // 100
    if c["kind"] == "fixed":
        return min(int(c["value"]), base)
    return 0


def reference_staging(scenario: str, fixture_root: Path) -> dict:
    sc = load_scenario(scenario, fixture_root)
    segments = build_segments(sc)
    compact = json.dumps(segments, separators=(",", ":"))
    digest = hashlib.sha256(compact.encode()).hexdigest()
    return {"segments": segments, "buffer_digest": digest}


def reference_invoices(
    scenario: str,
    fixture_root: Path,
    reconcile_pass: int = 1,
    proration_bps: int | None = None,
) -> dict:
    sc = load_scenario(scenario, fixture_root)
    segments = build_segments(sc)
    plans = sc["plans"]
    coupons = sc.get("coupons") or []
    changes = [e for e in sc.get("events", []) if e["event_type"] == "plan_change"]
    carry = 0
    lines: list[dict] = []
    for i, seg in enumerate(segments):
        plan = plans[seg["plan_id"]]
        usage = usage_in_segment(sc, seg["window_start"], seg["window_end"])
        billable = max(0, usage - int(plan["included_units"]) - carry)
        over_cents = billable * int(plan["overage_cents"])
        base = int(seg["base_cents"])
        if proration_bps is not None and i > 0:
            base = base * proration_bps // 10000
        subtotal = base + over_cents
        disc = apply_coupons(subtotal, coupons)
        lines.append(
            {
                "segment_index": seg["segment_index"],
                "line_kind": "subscription",
                "plan_id": seg["plan_id"],
                "base_cents": base,
                "proration_cents": 0,
                "overage_cents": over_cents,
                "coupon_cents": disc,
                "total_cents": subtotal - disc,
            }
        )
        if i < len(changes):
            ch = changes[i]
            if is_downgrade(ch["from_plan"], ch["to_plan"], plans):
                carry = max(0, int(plans[ch["from_plan"]]["included_units"]) - usage)
            else:
                carry = 0
    lines.sort(key=lambda r: (r["line_kind"], r["segment_index"]))
    digest = hashlib.sha256(json.dumps(lines, separators=(",", ":")).encode()).hexdigest()
    return {
        "scenario_id": sc["scenario_id"],
        "customer_id": sc["customer_id"],
        "reconcile_pass": reconcile_pass,
        "invoice_lines": lines,
        "ledger_digest": digest,
    }
