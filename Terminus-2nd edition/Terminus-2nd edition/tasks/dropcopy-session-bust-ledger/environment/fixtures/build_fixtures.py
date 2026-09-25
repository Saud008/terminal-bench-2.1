"""Generate JSONL FIX streams with valid checksums for dropcopy fixtures."""

from __future__ import annotations

import json
from pathlib import Path

SOH = "\x01"


def checksum(body_prefix: str) -> str:
    total = sum(ord(c) for c in body_prefix) % 256
    return f"{total:03d}"


def build_fix(fields: list[tuple[str, str]]) -> str:
    pairs = [f"{k}={v}" for k, v in fields if k not in ("9", "10")]
    body = SOH.join(pairs) + SOH
    body_len = len(body.encode("latin-1"))
    with_len = f"9={body_len}{SOH}" + body
    prefix = "8=FIX.4.2" + SOH + with_len
    cs = checksum(prefix)
    wire = prefix + f"10={cs}" + SOH
    return wire.replace(SOH, "|")


def row(session: str, seq: int, sending: str, fix_body: str) -> str:
    return json.dumps(
        {
            "session": session,
            "msg_seq": seq,
            "sending_time": sending,
            "fix_body": fix_body,
        },
        separators=(",", ":"),
    )


def exec_report(
    *,
    session: str,
    seq: int,
    sending: str,
    cl_ord_id: str,
    exec_id: str,
    symbol: str,
    side: str,
    qty: int,
    px: str,
    exec_trans_type: str = "0",
    exec_type: str = "0",
    orig: str = "",
) -> str:
    fields: list[tuple[str, str]] = [
        ("35", "8"),
        ("34", str(seq)),
        ("52", sending),
        ("11", cl_ord_id),
        ("17", exec_id),
        ("20", exec_trans_type),
        ("150", exec_type),
        ("55", symbol),
        ("54", side),
        ("32", str(qty)),
        ("31", px),
    ]
    if orig:
        fields.append(("41", orig))
    return row(session, seq, sending, build_fix(fields))


def logon_reset(session: str, seq: int, sending: str) -> str:
    return row(
        session,
        seq,
        sending,
        build_fix(
            [
                ("35", "A"),
                ("34", str(seq)),
                ("52", sending),
                ("141", "Y"),
            ]
        ),
    )


def write(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text, encoding="utf-8")


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    fx = root / "fixtures"
    hid = root / "hidden"

    write(
        fx / "streams" / "bust_chain.jsonl",
        [
            exec_report(
                session="desk1",
                seq=1,
                sending="20240601-10:00:00.000",
                cl_ord_id="ORD1",
                exec_id="EX1",
                symbol="AAPL",
                side="1",
                qty=100,
                px="190.50",
            ),
            exec_report(
                session="desk1",
                seq=2,
                sending="20240601-10:00:01.000",
                cl_ord_id="ORD1B",
                exec_id="EX2",
                symbol="AAPL",
                side="1",
                qty=100,
                px="190.50",
                exec_type="H",
                orig="ORD1",
            ),
        ],
    )

    write(
        fx / "streams" / "cancel_correct.jsonl",
        [
            exec_report(
                session="desk2",
                seq=1,
                sending="20240601-11:00:00.000",
                cl_ord_id="C1",
                exec_id="CX1",
                symbol="MSFT",
                side="2",
                qty=50,
                px="420.00",
            ),
            exec_report(
                session="desk2",
                seq=2,
                sending="20240601-11:00:01.000",
                cl_ord_id="C1CAN",
                exec_id="CX2",
                symbol="MSFT",
                side="2",
                qty=50,
                px="420.00",
                exec_trans_type="1",
                orig="C1",
            ),
            exec_report(
                session="desk2",
                seq=3,
                sending="20240601-11:00:02.000",
                cl_ord_id="C1COR",
                exec_id="CX3",
                symbol="MSFT",
                side="2",
                qty=30,
                px="421.00",
                exec_trans_type="2",
                orig="C1",
            ),
        ],
    )

    write(
        fx / "streams" / "seq_reset_fill.jsonl",
        [
            exec_report(
                session="desk3",
                seq=5,
                sending="20240601-12:00:00.000",
                cl_ord_id="R1",
                exec_id="RX1",
                symbol="IBM",
                side="1",
                qty=10,
                px="180.00",
            ),
            logon_reset("desk3", 6, "20240601-12:00:01.000"),
            exec_report(
                session="desk3",
                seq=1,
                sending="20240601-12:00:02.000",
                cl_ord_id="R2",
                exec_id="RX2",
                symbol="IBM",
                side="1",
                qty=20,
                px="181.00",
            ),
        ],
    )

    write(
        fx / "streams" / "execid_dup.jsonl",
        [
            exec_report(
                session="desk4",
                seq=1,
                sending="20240601-13:00:00.000",
                cl_ord_id="D1",
                exec_id="DUP1",
                symbol="GOOG",
                side="1",
                qty=5,
                px="2800.00",
            ),
            exec_report(
                session="desk4",
                seq=2,
                sending="20240601-13:00:01.000",
                cl_ord_id="D1LATE",
                exec_id="DUP1",
                symbol="GOOG",
                side="1",
                qty=999,
                px="2800.00",
            ),
        ],
    )

    write(
        hid / "streams" / "seq_bias_base.jsonl",
        [
            exec_report(
                session="hdesk",
                seq=2,
                sending="20240602-09:00:00.000",
                cl_ord_id="H1",
                exec_id="HX1",
                symbol="TSLA",
                side="1",
                qty=12,
                px="200.00",
            ),
        ],
    )

    write(
        hid / "streams" / "rollback_bad_seq.jsonl",
        [
            exec_report(
                session="xdesk",
                seq=1,
                sending="20240603-08:00:00.000",
                cl_ord_id="X1",
                exec_id="XX1",
                symbol="NFLX",
                side="1",
                qty=7,
                px="620.00",
            ),
            exec_report(
                session="xdesk",
                seq=1,
                sending="20240603-08:00:01.000",
                cl_ord_id="X2",
                exec_id="XX2",
                symbol="NFLX",
                side="1",
                qty=8,
                px="621.00",
            ),
        ],
    )

    bad = exec_report(
        session="bad",
        seq=1,
        sending="20240604-08:00:00.000",
        cl_ord_id="B1",
        exec_id="BX1",
        symbol="BAD",
        side="1",
        qty=1,
        px="1.00",
    ).replace("|10=", "|10=000|")
    write(hid / "streams" / "bad_checksum.jsonl", [bad])

    scenarios = {
        "bust-chain": ["streams/bust_chain.jsonl"],
        "cancel-correct": ["streams/cancel_correct.jsonl"],
        "seq-reset": ["streams/seq_reset_fill.jsonl"],
        "execid-dup": ["streams/execid_dup.jsonl"],
    }
    for name, streams in scenarios.items():
        write_text(
            fx / "scenarios" / f"{name}.json",
            json.dumps({"scenario_id": name, "streams": streams}, indent=2),
        )

    hidden_scenarios = {
        "seq-bias-trap": ["streams/seq_bias_base.jsonl"],
        "rollback-trap": ["streams/rollback_bad_seq.jsonl"],
        "bad-checksum": ["streams/bad_checksum.jsonl"],
    }
    for name, streams in hidden_scenarios.items():
        write_text(
            hid / "scenarios" / f"{name}.json",
            json.dumps({"scenario_id": name, "streams": streams}, indent=2),
        )

    write_text(
        fx / "seeds.json",
        json.dumps({"seeds": ["alpha", "beta", "gamma", "delta"]}, indent=2),
    )
    print("fixtures ok")


if __name__ == "__main__":
    main()
