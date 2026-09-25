from __future__ import annotations

import hashlib
import json
import math
from datetime import date, datetime, timedelta, timezone
from pathlib import Path


def load_scenario(scenario: str, fixture_root: Path) -> dict:
    path = fixture_root / "scenarios" / f"{scenario}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def floor_interval_utc(ts: str, interval_minutes: int = 15) -> str:
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc)
    step = interval_minutes or 15
    minute = (dt.minute // step) * step
    aligned = dt.replace(minute=minute, second=0, microsecond=0)
    return aligned.strftime("%Y-%m-%dT%H:%M:%SZ")


def curtailment_active(interval_start: str, windows: list[dict]) -> bool:
    when = datetime.fromisoformat(interval_start.replace("Z", "+00:00")).astimezone(timezone.utc)
    for window in windows:
        start = datetime.fromisoformat(window["start_utc"].replace("Z", "+00:00")).astimezone(timezone.utc)
        end = datetime.fromisoformat(window["end_utc"].replace("Z", "+00:00")).astimezone(timezone.utc)
        if start <= when < end:
            return True
    return False


def market_price_cents(interval_start: str, prices: list[dict]) -> int:
    for row in prices:
        if row["interval_start_utc"] == interval_start:
            return int(row["price_cents"])
    raise KeyError(interval_start)


def settlement_price_cents(strike: int, market: int) -> int:
    return max(strike, market)


def amount_cents(mwh: float, settlement: int) -> int:
    return int(math.floor(mwh * settlement + 0.5))


def billing_days(period_start: str, period_end: str, holidays: list[str]) -> int:
    start = date.fromisoformat(period_start)
    end = date.fromisoformat(period_end)
    holiday_set = set(holidays)
    total = 0
    trimmed = 0
    d = start
    while d <= end:
        total += 1
        if d.isoformat() in holiday_set:
            trimmed += 1
        d += timedelta(days=1)
    return total - trimmed


def reference_lines(scenario: str, fixture_root: Path) -> list[dict]:
    sc = load_scenario(scenario, fixture_root)
    strike = int(sc["strike_price_cents"])
    interval = int(sc.get("interval_minutes", 15))
    lines: list[dict] = []
    for meter in sc["meters"]:
        for reading in meter["readings"]:
            aligned = floor_interval_utc(reading["ts_utc"], interval)
            if curtailment_active(aligned, sc.get("curtailments", [])):
                lines.append(
                    {
                        "meter_id": meter["meter_id"],
                        "interval_start_utc": aligned,
                        "mwh": reading["mwh"],
                        "strike_cents": strike,
                        "market_cents": 0,
                        "settlement_cents": 0,
                        "amount_cents": 0,
                        "skipped_curtail": True,
                    }
                )
                continue
            market = market_price_cents(aligned, sc["market_prices"])
            settle = settlement_price_cents(strike, market)
            amount = amount_cents(float(reading["mwh"]), settle)
            lines.append(
                {
                    "meter_id": meter["meter_id"],
                    "interval_start_utc": aligned,
                    "mwh": reading["mwh"],
                    "strike_cents": strike,
                    "market_cents": market,
                    "settlement_cents": settle,
                    "amount_cents": amount,
                    "skipped_curtail": False,
                }
            )
    return lines


def reference_invoice(scenario: str, fixture_root: Path) -> dict:
    sc = load_scenario(scenario, fixture_root)
    lines = reference_lines(scenario, fixture_root)
    active = [line for line in lines if not line["skipped_curtail"]]
    total = sum(int(line["amount_cents"]) for line in active)
    digest = hashlib.sha256(json.dumps(lines, separators=(",", ":")).encode()).hexdigest()
    return {
        "scenario_id": scenario,
        "ppa_id": sc["ppa_id"],
        "period_start": sc["period_start"],
        "period_end": sc["period_end"],
        "billing_days": billing_days(sc["period_start"], sc["period_end"], sc.get("holidays", [])),
        "line_count": len(active),
        "total_amount_cents": total,
        "lines_digest": digest,
    }
