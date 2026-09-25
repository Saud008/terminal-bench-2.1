from __future__ import annotations

import hashlib
import json
from datetime import date, timedelta


def parse_d(s: str) -> date:
    y, m, d = map(int, s.split("-"))
    return date(y, m, d)


def is_weekend(d: date) -> bool:
    return d.weekday() >= 5


def is_holiday(d: date, holidays: set[str]) -> bool:
    return d.isoformat() in holidays


def is_business(d: date, holidays: set[str]) -> bool:
    return not is_weekend(d) and not is_holiday(d, holidays)


def add_bdays(start: date, n: int, holidays: set[str]) -> date:
    cur = start
    added = 0
    step = 1 if n >= 0 else -1
    target = abs(n)
    while added < target:
        cur += timedelta(days=step)
        if is_business(cur, holidays):
            added += 1
    return cur


def adjust_following(d: date, holidays: set[str], modified: bool = False) -> date:
    if is_business(d, holidays):
        return d
    cur = d
    while not is_business(cur, holidays):
        cur += timedelta(days=1)
    if modified and cur.month != d.month:
        cur = d
        while not is_business(cur, holidays):
            cur -= timedelta(days=1)
    return cur


def thirt360(start: date, end: date) -> float:
    y1, m1, d1 = start.year, start.month, start.day
    y2, m2, d2 = end.year, end.month, end.day
    if d1 == 31:
        d1 = 30
    if d2 == 31 and d1 == 30:
        d2 = 30
    days = (y2 - y1) * 360 + (m2 - m1) * 30 + (d2 - d1)
    return days / 360.0


def act360(start: date, end: date) -> float:
    return (end - start).days / 360.0


def act_act(start: date, end: date) -> float:
    days = (end - start).days
    denom = 366 if any(date(y, 2, 29) >= start and date(y, 2, 29) < end for y in range(start.year, end.year + 1)) else 365
    return days / denom


def year_fraction(start: date, end: date, conv: str) -> float:
    if end <= start:
        return 0.0
    if conv == "ACT/360":
        return act360(start, end)
    if conv == "30/360":
        return thirt360(start, end)
    if conv == "ACT/ACT":
        return act_act(start, end)
    return 0.0


def coupon_dates(issue: date, maturity: date, freq: int) -> list[date]:
    months = 12 // freq
    out: list[date] = []
    cur = issue
    while cur < maturity:
        nm, ny = cur.month + months, cur.year
        while nm > 12:
            nm -= 12
            ny += 1
        dom = cur.day
        import calendar as calmod

        last = calmod.monthrange(ny, nm)[1]
        if dom > last:
            dom = last
        nxt = date(ny, nm, dom)
        if nxt >= maturity:
            break
        out.append(nxt)
        cur = nxt
    out.append(maturity)
    return out


def period_containing(settle: date, issue: date, dates: list[date]) -> tuple[date, date]:
    prev = issue
    for cp in dates:
        if settle < cp:
            return prev, cp
        prev = cp
    return prev, dates[-1]


def ex_coupon_date(coupon: date, ex_days: int) -> date:
    return coupon - timedelta(days=ex_days)


def trade_ex(trade: date, coupon: date, ex_days: int) -> bool:
    return trade >= ex_coupon_date(coupon, ex_days)


def accrued_cents(face: int, bps: int, yf: float) -> int:
    return int(round(face * bps / 10000.0 * yf))


def reference_accrual_row(bond: dict, trade: dict, cal: dict) -> dict:
    """Independent reference accrual row for subprocess CLI verification."""
    holidays = set(cal.get("holidays", []))
    issue = parse_d(bond["issue_date"])
    maturity = parse_d(bond["maturity_date"])
    dates = coupon_dates(issue, maturity, bond.get("frequency", 2))
    trade_d = parse_d(trade["trade_date"])
    settle = add_bdays(trade_d, trade.get("settle_lag_bdays", 2), holidays)
    p0, p1 = period_containing(settle, issue, dates)
    yf = year_fraction(p0, settle, bond["day_count"])
    acc = accrued_cents(bond["face_cents"], bond["coupon_bps"], yf)
    ex = trade_ex(trade_d, p1, bond.get("ex_days", 7))
    if ex:
        acc = 0
    return {
        "trade_id": trade["trade_id"],
        "isin": bond["isin"],
        "period_start": p0.isoformat(),
        "period_end": p1.isoformat(),
        "settlement_date": settle.isoformat(),
        "accrued_cents": acc,
        "ex_coupon": ex,
    }


def expected_row(bond: dict, trade: dict, cal: dict) -> dict:
    return reference_accrual_row(bond, trade, cal)


def reference_atlas_digest(rows: list[dict]) -> str:
    """Reference sha256 digest for accrual atlas rows."""
    canon = []
    for r in rows:
        canon.append(
            {
                "trade_id": r["trade_id"],
                "isin": r["isin"],
                "period_start": r["period_start"],
                "period_end": r["period_end"],
                "settlement_date": r["settlement_date"],
                "accrued_cents": r["accrued_cents"],
                "ex_coupon": r["ex_coupon"],
            }
        )
    payload = json.dumps(canon, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def atlas_digest(rows: list[dict]) -> str:
    return reference_atlas_digest(rows)
