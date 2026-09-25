#!/usr/bin/env python3
"""Build TB3 FIX session fixtures for verifier-only ingest traps."""

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
    root = Path(__file__).resolve().parent
    chain_dir = root / "chain"
    idem_dir = root / "idem"
    vwap_dir = root / "vwap"
    for d in (chain_dir, idem_dir, vwap_dir):
        d.mkdir(parents=True, exist_ok=True)

    sym = "TB3Z"
    chain = [
        exec_report(
            cl_ord_id="TB3-CHAIN-2",
            exec_id="TB3-X-2",
            symbol=sym,
            side="1",
            sending_time="20240624-12:00:02",
            exec_type="2",
            last_qty="40",
            last_px="110.00",
        ),
        exec_report(
            cl_ord_id="TB3-CHAIN-1",
            exec_id="TB3-X-1",
            symbol=sym,
            side="1",
            sending_time="20240624-12:00:01",
            exec_type="2",
            last_qty="60",
            last_px="100.00",
        ),
        exec_report(
            cl_ord_id="TB3-CHAIN-3",
            exec_id="TB3-X-3",
            symbol=sym,
            side="1",
            sending_time="20240624-12:00:03",
            exec_type="4",
            order_qty="30",
        ),
    ]
    (chain_dir / "chain_partial_cancel.fix").write_bytes(b"".join(chain))

    idem = exec_report(
        cl_ord_id="TB3-IDEM-1",
        exec_id="TB3-IE-1",
        symbol="TB3I",
        side="1",
        sending_time="20240624-13:00:01",
        exec_type="2",
        last_qty="25",
        last_px="50.00",
    )
    (idem_dir / "idem_once.fix").write_bytes(idem)

    vwap = [
        exec_report(
            cl_ord_id="TB3-VW-b",
            exec_id="TB3-V-b",
            symbol="TB3V",
            side="1",
            sending_time="20240624-16:00:02",
            exec_type="2",
            last_qty="30",
            last_px="200.00",
        ),
        exec_report(
            cl_ord_id="TB3-VW-a",
            exec_id="TB3-V-a",
            symbol="TB3V",
            side="1",
            sending_time="20240624-16:00:01",
            exec_type="2",
            last_qty="70",
            last_px="100.00",
        ),
    ]
    (vwap_dir / "vwap_two_fills.fix").write_bytes(b"".join(vwap))


if __name__ == "__main__":
    main()
