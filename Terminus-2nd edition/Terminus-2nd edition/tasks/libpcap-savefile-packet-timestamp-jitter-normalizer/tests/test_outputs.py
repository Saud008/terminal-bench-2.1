"""Verifier for pcapjitter libpcap savefile timestamp normalizer."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path
from typing import Any

APP = Path("/app")
BIN = APP / "target" / "debug" / "pcapjitter"
CAPTURES = APP / "fixtures" / "captures"
HIDDEN = Path("/opt/verifier-fixtures/pcap")
STATE = APP / "state"
OUTPUT = APP / "output"
STAGING = STATE / "pcap-stage.json"
TIMELINE = OUTPUT / "timeline.json"
LEDGER = STATE / "gap-ledger.jsonl"
SEQ = STATE / "gap-seq.txt"

PROTECTED_SHA256: dict[str, str] = {
    "001-window-order.pcap": (
        "ef8777cc3a4193c06bdf2dc70fc68f088b96eae9bfb3da099ddb56875bfa5441"
    ),
    "002-big-endian.pcap": (
        "72ec9444bf3d17634fb095c9c329d9b773803d93a4749cf1bf77272bc9cbde00"
    ),
    "003-truncated.pcap": (
        "4f5eadb7bdd05f0451943f5402597d4152dec4598f653f3c7634a7fdab0e5dd5"
    ),
    "004-gap-timeline.pcap": (
        "908c3e713332cead87c3eb1c8e5f75eebb990b285eaac891f8e2779236ca2da9"
    ),
}

HIDDEN_SHA256 = {
    "005-mixed-probe.pcap": (
        "ae4f2bf8695e0d6da5d2c70b5967d5434c925a642827e7da359af84bedc7f429"
    ),
}

MAGIC_LE = 0xA1B2C3D4
MAGIC_BE = 0xD4C3B2A1


def _policy() -> dict[str, int]:
    """Load normalization policy matching /app/docs defaults and env overrides."""
    window_us = 5000
    gap_ns = 1_000_000_000
    trunc_ns = 100
    if os.environ.get("PCAP_JITTER_WINDOW_US", "").isdigit():
        window_us = int(os.environ["PCAP_JITTER_WINDOW_US"])
    if os.environ.get("PCAP_JITTER_GAP_NS", "").isdigit():
        gap_ns = int(os.environ["PCAP_JITTER_GAP_NS"])
    if os.environ.get("PCAP_JITTER_TRUNC_NS", "").isdigit():
        trunc_ns = int(os.environ["PCAP_JITTER_TRUNC_NS"])
    return {
        "window_us": window_us,
        "gap_threshold_ns": gap_ns,
        "trunc_ns_per_byte": trunc_ns,
    }


def _read_u32(data: bytes, off: int, endian: str) -> int:
    return struct.unpack_from(endian + "I", data, off)[0]


def _detect_pcap_endian(raw: bytes) -> str:
    """Detect savefile endian using magic and version per libpcap conventions."""
    le_magic = _read_u32(raw, 0, "<")
    if le_magic == MAGIC_LE:
        if _read_u16(raw, 4, "<") == 2 and _read_u16(raw, 6, "<") == 4:
            return "<"
    be_magic = _read_u32(raw, 0, ">")
    if be_magic == MAGIC_BE:
        if _read_u16(raw, 4, ">") == 2 and _read_u16(raw, 6, ">") == 4:
            return ">"
    raise AssertionError(f"unsupported pcap magic le={le_magic:#x} be={be_magic:#x}")


def _read_u16(data: bytes, off: int, endian: str) -> int:
    return struct.unpack_from(endian + "H", data, off)[0]


def reference_parse_pcap(path: Path) -> dict[str, Any]:
    """Parse classic libpcap savefile per savefile-format.md."""
    raw = path.read_bytes()
    assert len(raw) >= 24, "pcap too short"
    endian = _detect_pcap_endian(raw)
    snaplen = _read_u32(raw, 16, endian)
    network = _read_u32(raw, 20, endian)
    offset = 24
    packets: list[dict[str, int]] = []
    index = 0
    while offset + 16 <= len(raw):
        ts_sec = _read_u32(raw, offset, endian)
        ts_usec = _read_u32(raw, offset + 4, endian)
        incl_len = _read_u32(raw, offset + 8, endian)
        orig_len = _read_u32(raw, offset + 12, endian)
        offset += 16
        assert offset + incl_len <= len(raw), "truncated payload"
        offset += incl_len
        raw_ts_us = ts_sec * 1_000_000 + ts_usec
        packets.append(
            {
                "index": index,
                "ts_sec": ts_sec,
                "ts_usec": ts_usec,
                "incl_len": incl_len,
                "orig_len": orig_len,
                "raw_ts_us": raw_ts_us,
            }
        )
        index += 1
    return {"snaplen": snaplen, "network": network, "packets": packets}


def reference_tolerance_order(packets: list[dict[str, int]], window_us: int) -> list[dict[str, int]]:
    """Stable tolerance-window ordering per tolerance-window.md."""
    ordered = list(packets)

    def compare_packets(a: dict[str, int], b: dict[str, int]) -> int:
        dt = abs(a["raw_ts_us"] - b["raw_ts_us"])
        if dt <= window_us:
            return -1 if a["index"] < b["index"] else (1 if a["index"] > b["index"] else 0)
        if a["raw_ts_us"] != b["raw_ts_us"]:
            return -1 if a["raw_ts_us"] < b["raw_ts_us"] else 1
        return -1 if a["index"] < b["index"] else (1 if a["index"] > b["index"] else 0)

    from functools import cmp_to_key

    return sorted(ordered, key=cmp_to_key(compare_packets))


def reference_timeline(staging: dict[str, Any], policy: dict[str, int]) -> tuple[dict[str, Any], list[dict[str, int]]]:
    """Compute export JSON and gap rows independently."""
    ordered = reference_tolerance_order(staging["packets"], policy["window_us"])
    packets_out: list[dict[str, int]] = []
    gaps: list[dict[str, int]] = []
    trunc_total = 0
    prev_norm = 0
    prev_raw = ordered[0]["raw_ts_us"]
    seq = 1
    for i, pkt in enumerate(ordered):
        penalty = 0
        if i > 0:
            prev_pkt = ordered[i - 1]
            if prev_pkt["incl_len"] < prev_pkt["orig_len"]:
                penalty = (prev_pkt["orig_len"] - prev_pkt["incl_len"]) * policy["trunc_ns_per_byte"]
                trunc_total += penalty
        if i == 0:
            norm_ns = 0
        else:
            delta_us = pkt["raw_ts_us"] - prev_raw
            delta_ns = delta_us * 1000 + penalty
            norm_ns = prev_norm + delta_ns
        if i > 0:
            step = norm_ns - prev_norm
            if step > policy["gap_threshold_ns"]:
                gaps.append(
                    {
                        "seq": seq,
                        "after_index": pkt["index"],
                        "gap_ns": step,
                        "prev_norm_ns": prev_norm,
                        "next_norm_ns": norm_ns,
                    }
                )
                seq += 1
        prev_raw = pkt["raw_ts_us"]
        prev_norm = norm_ns
        packets_out.append(
            {
                "index": pkt["index"],
                "norm_ns": norm_ns,
                "incl_len": pkt["incl_len"],
                "orig_len": pkt["orig_len"],
            }
        )
    export = {
        "packets": packets_out,
        "stats": {
            "gap_count": len(gaps),
            "trunc_penalty_total_ns": trunc_total,
            "packet_count": len(packets_out),
        },
    }
    return export, gaps


def _run_cli(args: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        [str(BIN), *args],
        capture_output=True,
        text=True,
        env=merged,
        check=False,
    )


def _reset_state() -> None:
    """Clear ledger and outputs between tests."""
    for path in (STAGING, TIMELINE, LEDGER, SEQ):
        if path.exists():
            path.unlink()
    if STATE.exists():
        for child in STATE.iterdir():
            if child.is_file():
                child.unlink()


def _ingest_export(pcap: Path, env: dict[str, str] | None = None) -> None:
    _reset_state()
    STATE.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    rc_i = _run_cli(
        [
            "ingest",
            "--input",
            str(pcap),
            "--staging",
            str(STAGING),
            "--ledger-root",
            str(STATE),
        ],
        env=env,
    )
    assert rc_i.returncode == 0, rc_i.stderr
    rc_e = _run_cli(
        [
            "export",
            "--output",
            str(TIMELINE),
            "--staging",
            str(STAGING),
            "--ledger-root",
            str(STATE),
        ],
        env=env,
    )
    assert rc_e.returncode == 0, rc_e.stderr


def test_binary_exists() -> None:
    """Verify pcapjitter was rebuilt before pytest."""
    assert BIN.is_file(), f"missing binary {BIN}"


def test_protected_fixture_integrity() -> None:
    """Bundled captures under /app/fixtures/captures must remain byte-identical."""
    on_disk = sorted(p.name for p in CAPTURES.glob("*.pcap"))
    assert on_disk == sorted(PROTECTED_SHA256)
    for name, digest in PROTECTED_SHA256.items():
        path = CAPTURES / name
        got = hashlib.sha256(path.read_bytes()).hexdigest()
        assert got == digest, f"fixture {name} was modified"


def test_staging_matches_reference_parse() -> None:
    """Ingest staging must record endian-correct raw_ts_us per staging-schema.md."""
    pcap = CAPTURES / "002-big-endian.pcap"
    _ingest_export(pcap)
    staging = json.loads(STAGING.read_text())
    ref = reference_parse_pcap(pcap)
    assert staging["snaplen"] == ref["snaplen"]
    assert staging["network"] == ref["network"]
    assert len(staging["packets"]) == len(ref["packets"])
    for got, exp in zip(staging["packets"], ref["packets"], strict=True):
        assert got["index"] == exp["index"]
        assert got["raw_ts_us"] == exp["raw_ts_us"]
        assert got["incl_len"] == exp["incl_len"]
        assert got["orig_len"] == exp["orig_len"]


def test_window_order_timeline() -> None:
    """Tolerance-window ordering preserves file order for near timestamps."""
    pcap = CAPTURES / "001-window-order.pcap"
    _ingest_export(pcap)
    got = json.loads(TIMELINE.read_text())
    ref, _gaps = reference_timeline(reference_parse_pcap(pcap), _policy())
    assert got["packets"] == ref["packets"]
    assert got["stats"] == ref["stats"]
    indices = [p["index"] for p in got["packets"]]
    assert indices == [0, 1, 2, 3]


def test_big_endian_timeline() -> None:
    """Big-endian savefiles must decode both ts_sec and ts_usec correctly."""
    pcap = CAPTURES / "002-big-endian.pcap"
    _ingest_export(pcap)
    got = json.loads(TIMELINE.read_text())
    ref, _ = reference_timeline(reference_parse_pcap(pcap), _policy())
    assert got == ref


def test_truncation_penalty_stats() -> None:
    """Truncated packets add per-byte penalty in stats.trunc_penalty_total_ns."""
    pcap = CAPTURES / "003-truncated.pcap"
    _ingest_export(pcap)
    got = json.loads(TIMELINE.read_text())
    ref, _ = reference_timeline(reference_parse_pcap(pcap), _policy())
    assert got["stats"]["trunc_penalty_total_ns"] == ref["stats"]["trunc_penalty_total_ns"]
    assert got["stats"]["trunc_penalty_total_ns"] > 0
    assert got["packets"] == ref["packets"]


def test_gap_ledger_rows() -> None:
    """Gap steps above threshold append JSONL rows per gap-ledger.md."""
    pcap = CAPTURES / "004-gap-timeline.pcap"
    _ingest_export(pcap)
    got = json.loads(TIMELINE.read_text())
    ref, ref_gaps = reference_timeline(reference_parse_pcap(pcap), _policy())
    assert got["stats"]["gap_count"] == ref["stats"]["gap_count"]
    assert got["stats"]["gap_count"] >= 1
    assert got["packets"] == ref["packets"]
    assert LEDGER.is_file()
    lines = [json.loads(line) for line in LEDGER.read_text().strip().splitlines()]
    assert lines == ref_gaps


def test_ledger_sequence_persists_across_exports() -> None:
    """Repeated export without input change continues gap-seq.txt monotonic sequence."""
    pcap = CAPTURES / "004-gap-timeline.pcap"
    _reset_state()
    STATE.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    assert _run_cli(
        ["ingest", "--input", str(pcap), "--staging", str(STAGING), "--ledger-root", str(STATE)]
    ).returncode == 0
    assert _run_cli(
        ["export", "--output", str(TIMELINE), "--staging", str(STAGING), "--ledger-root", str(STATE)]
    ).returncode == 0
    first_lines = LEDGER.read_text().strip().splitlines()
    first_seq = int(SEQ.read_text().strip())
    assert _run_cli(
        ["export", "--output", str(TIMELINE), "--staging", str(STAGING), "--ledger-root", str(STATE)]
    ).returncode == 0
    all_lines = LEDGER.read_text().strip().splitlines()
    assert len(all_lines) == len(first_lines) * 2
    second_seq = int(SEQ.read_text().strip())
    assert second_seq == first_seq + len(first_lines)


def test_tb3_hidden_probe_directory() -> None:
    """TB3_PCAP_DIR resolves hidden capture basenames per cli.md."""
    hidden_name = "005-mixed-probe.pcap"
    assert (HIDDEN / hidden_name).is_file()
    digest = hashlib.sha256((HIDDEN / hidden_name).read_bytes()).hexdigest()
    assert digest == HIDDEN_SHA256[hidden_name]
    with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
        probe = Path(tmp) / hidden_name
        shutil.copy(HIDDEN / hidden_name, probe)
        env = {"TB3_PCAP_DIR": tmp}
        _reset_state()
        STATE.mkdir(parents=True, exist_ok=True)
        OUTPUT.mkdir(parents=True, exist_ok=True)
        rc = _run_cli(
            [
                "ingest",
                "--input",
                hidden_name,
                "--staging",
                str(STAGING),
                "--ledger-root",
                str(STATE),
            ],
            env=env,
        )
        assert rc.returncode == 0, rc.stderr
        rc2 = _run_cli(
            [
                "export",
                "--output",
                str(TIMELINE),
                "--staging",
                str(STAGING),
                "--ledger-root",
                str(STATE),
            ],
            env=env,
        )
        assert rc2.returncode == 0, rc2.stderr
    got = json.loads(TIMELINE.read_text())
    ref, ref_gaps = reference_timeline(reference_parse_pcap(HIDDEN / hidden_name), _policy())
    assert got["packets"] == ref["packets"]
    assert got["stats"] == ref["stats"]
    if ref_gaps:
        assert LEDGER.is_file(), "gap ledger must exist when reference emits gap rows"
        lines = [json.loads(line) for line in LEDGER.read_text().strip().splitlines()]
        assert lines == ref_gaps
    else:
        assert got["stats"]["gap_count"] == 0
        assert not LEDGER.exists() or LEDGER.read_text().strip() == ""


def test_missing_input_exit_one() -> None:
    """Missing ingest input exits 1 per export-contract.md."""
    _reset_state()
    rc = _run_cli(
        [
            "ingest",
            "--input",
            "/app/fixtures/captures/does-not-exist.pcap",
            "--staging",
            str(STAGING),
            "--ledger-root",
            str(STATE),
        ]
    )
    assert rc.returncode == 1


def test_invalid_staging_exit_two() -> None:
    """Malformed staging on export exits 2."""
    _reset_state()
    STATE.mkdir(parents=True, exist_ok=True)
    STAGING.write_text("{not-json")
    rc = _run_cli(
        [
            "export",
            "--output",
            str(TIMELINE),
            "--staging",
            str(STAGING),
            "--ledger-root",
            str(STATE),
        ]
    )
    assert rc.returncode == 2
