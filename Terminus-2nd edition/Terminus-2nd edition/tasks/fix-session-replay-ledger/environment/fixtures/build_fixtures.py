#!/usr/bin/env python3
"""Build bundled FIX session fixtures with valid checksums."""

from __future__ import annotations

from pathlib import Path

SOH = "\x01"


def compose_fix(body_fields: list[tuple[str, str]]) -> bytes:
    body = SOH.join(f"{k}={v}" for k, v in body_fields)
    body_len = len(body.encode("ascii"))
    prefix = f"8=FIX.4.2{SOH}9={body_len}{SOH}"
    without_chk = prefix + body + SOH
    chk = sum(ord(c) for c in without_chk) % 256
    return (without_chk + f"10={chk:03d}" + SOH).encode("ascii")


def exec_report(
    *,
    cl_ord_id: str,
    exec_id: str,
    symbol: str,
    side: str,
    sending_time: str,
    exec_type: str,
    last_qty: str = "",
    last_px: str = "",
    order_qty: str = "",
) -> bytes:
    fields: list[tuple[str, str]] = [
        ("35", "8"),
        ("11", cl_ord_id),
        ("17", exec_id),
        ("55", symbol),
        ("54", side),
        ("52", sending_time),
        ("150", exec_type),
    ]
    if last_qty:
        fields.append(("32", last_qty))
    if last_px:
        fields.append(("31", last_px))
    if order_qty:
        fields.append(("38", order_qty))
    return compose_fix(fields)


def main() -> None:
    out = Path(__file__).resolve().parent
    # File order intentionally differs from SendingTime order.
    alpha_msgs = [
        exec_report(
            cl_ord_id="A-003",
            exec_id="E-003",
            symbol="AAPL",
            side="1",
            sending_time="20240624-10:00:03",
            exec_type="2",
            last_qty="100",
            last_px="152.00",
        ),
        exec_report(
            cl_ord_id="A-001",
            exec_id="E-001",
            symbol="AAPL",
            side="1",
            sending_time="20240624-10:00:01",
            exec_type="2",
            last_qty="50",
            last_px="150.00",
        ),
        exec_report(
            cl_ord_id="A-002",
            exec_id="E-002",
            symbol="AAPL",
            side="1",
            sending_time="20240624-10:00:02",
            exec_type="2",
            last_qty="50",
            last_px="151.00",
        ),
    ]
    (out / "session_alpha.fix").write_bytes(b"".join(alpha_msgs))

    beta_msgs = [
        exec_report(
            cl_ord_id="M-001",
            exec_id="E-M1",
            symbol="MSFT",
            side="1",
            sending_time="20240624-11:00:01",
            exec_type="2",
            last_qty="100",
            last_px="400.00",
        ),
        exec_report(
            cl_ord_id="M-002",
            exec_id="E-M2",
            symbol="MSFT",
            side="1",
            sending_time="20240624-11:00:02",
            exec_type="4",
            order_qty="20",
        ),
    ]
    (out / "session_beta.fix").write_bytes(b"".join(beta_msgs))


if __name__ == "__main__":
    main()
