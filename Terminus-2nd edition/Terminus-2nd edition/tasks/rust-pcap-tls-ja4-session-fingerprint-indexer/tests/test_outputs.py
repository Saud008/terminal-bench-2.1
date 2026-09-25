"""Pytest contract suite for the JA4 PCAP capsule session indexer."""

from __future__ import annotations

import hashlib
import json
import os
import struct
import subprocess
from pathlib import Path

APP = Path("/app")
ENV = APP / "environment"
BIN = ENV / "tools" / "ja4idx" / "ja4idx"
STATE = APP / "state" / "session_ledger.jsonl"
OUT = APP / "output" / "session_index.json"
DEFAULT_CAPS = ENV / "fixtures" / "capsules"
HIDDEN_CAPS = Path("/tests/hidden_capsules")


def capsule_dir() -> Path:
    tb3 = os.environ.get("TB3_CAPSULE_DIR")
    if tb3:
        return Path(tb3)
    return DEFAULT_CAPS


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)


def rebuild() -> None:
    run(["bash", str(ENV / "scripts" / "build_all.sh")])


def pipeline(caps: Path | None = None) -> None:
    caps = caps or capsule_dir()
    STATE.parent.mkdir(parents=True, exist_ok=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if STATE.exists():
        STATE.unlink()
    if OUT.exists():
        OUT.unlink()
    run([str(BIN), "intake", "--capsules-dir", str(caps), "--ledger", str(STATE)])
    run([str(BIN), "emit", "--ledger", str(STATE), "--out", str(OUT)])


def load_index() -> dict:
    return json.loads(OUT.read_text(encoding="utf-8"))


def read_capsules(dir_path: Path) -> list[dict]:
    frames: list[dict] = []
    for cap in sorted(dir_path.glob("*.cap")):
        raw = cap.read_bytes()
        assert raw[:4] == b"CAPS"
        count = struct.unpack_from("<I", raw, 4)[0]
        off = 8
        for _ in range(count):
            quad = raw[off : off + 8]
            off += 8
            seq = struct.unpack_from("<I", raw, off)[0]
            off += 4
            direction = raw[off]
            off += 1
            retrans = raw[off]
            off += 1
            plen = struct.unpack_from("<H", raw, off)[0]
            off += 2
            payload = raw[off : off + plen]
            off += plen
            frames.append(
                {
                    "quad": quad,
                    "seq": seq,
                    "direction": direction,
                    "retrans": retrans,
                    "payload": payload,
                }
            )
    frames.sort(key=lambda f: (f["quad"], f["seq"]))
    return frames


def dedupe_frames(frames: list[dict]) -> list[dict]:
    seen_seq: set[tuple[bytes, int]] = set()
    seen_payload: set[bytes] = set()
    out: list[dict] = []
    for f in frames:
        sk = (f["quad"], f["seq"])
        ph = f["payload"]
        if sk in seen_seq or ph in seen_payload:
            continue
        seen_seq.add(sk)
        seen_payload.add(ph)
        out.append(f)
    return out


def ip_fmt(oct: bytes) -> str:
    return ".".join(str(b) for b in oct)


def role_map_for_quad(quad: bytes, frames: list[dict]) -> dict[str, str]:
    client = quad[0:4]
    server = quad[4:8]
    for f in sorted(frames, key=lambda x: x["seq"]):
        if f["quad"] == quad and f["direction"] == 0:
            return {ip_fmt(client): "client", ip_fmt(server): "server"}
    return {ip_fmt(client): "client"}


def first_client_hello_body(buf: bytes) -> bytes:
    off = 0
    while off + 5 <= len(buf):
        ctype = buf[off]
        ln = struct.unpack(">H", buf[off + 3 : off + 5])[0]
        if off + 5 + ln > len(buf):
            break
        body = buf[off + 5 : off + 5 + ln]
        if ctype == 0x16 and body and body[0] == 0x01:
            return body
        off += 5 + ln
    return buf


def parity_ja4_from_handshake(buf: bytes) -> str:
    body = first_client_hello_body(buf)
    tls_version = 0x0303
    ciphers: list[int] = []
    extensions: list[int] = []
    alpn = ""
    if len(body) >= 6:
        tls_version = struct.unpack(">H", body[4:6])[0]
    if len(body) > 38:
        off = 38
        if off < len(body):
            sid_len = body[off]
            off += 1 + sid_len
        if off + 2 <= len(body):
            cs_len = struct.unpack(">H", body[off : off + 2])[0]
            off += 2
            for _ in range(cs_len // 2):
                if off + 2 > len(body):
                    break
                ciphers.append(struct.unpack(">H", body[off : off + 2])[0])
                off += 2
            if off + 2 <= len(body):
                ext_len = struct.unpack(">H", body[off : off + 2])[0]
                off += 2
                end = off + ext_len
                while off + 4 <= end and off + 4 <= len(body):
                    etype = struct.unpack(">H", body[off : off + 2])[0]
                    elen = struct.unpack(">H", body[off + 2 : off + 4])[0]
                    extensions.append(etype)
                    if etype == 0x10 and off + 4 + elen <= len(body):
                        data = body[off + 4 : off + 4 + elen]
                        if data:
                            slen = data[0]
                            if len(data) >= 1 + slen:
                                alpn = data[1 : 1 + slen].decode("ascii", errors="ignore")
                    off += 4 + elen
    ciphers.sort()
    extensions.sort()
    ext_hash = hashlib.sha256(b"".join(struct.pack(">H", e) for e in extensions)).hexdigest()[:12]
    ver = f"{tls_version & 0xFF:02x}"
    cc = f"{min(len(ciphers), 255):02x}"
    alpn_pref = alpn[:2] if alpn else "00"
    return f"t{ver}d{cc}h{ext_hash}_{alpn_pref}"


def parity_session_index(caps: Path) -> dict:
    """Build the independent reference index from raw capsule bytes."""
    frames = read_capsules(caps)
    sessions: dict[bytes, list[dict]] = {}
    for f in frames:
        sessions.setdefault(f["quad"], []).append(f)
    rows = []
    total_retrans = 0
    for quad in sorted(sessions.keys()):
        raw = sessions[quad]
        sess = dedupe_frames(raw)
        hs = b"".join(f["payload"] for f in sess)
        roles = role_map_for_quad(quad, raw)
        retrans = sum(1 for f in raw if f["retrans"])
        total_retrans += retrans
        seqs = sorted({f["seq"] for f in sess})
        gap = 0
        for a, b in zip(seqs, seqs[1:]):
            if b > a + 1:
                gap += b - a - 1
        if gap > 0:
            gap = max(0, gap - 1)
        rows.append(
            {
                "session_id": quad.hex(),
                "role_map": roles,
                "ja4": parity_ja4_from_handshake(hs),
                "frame_count": len(raw),
                "unique_frames": len(sess),
                "anomalies": {"fragment_gap": gap, "role_flip": 0, "retransmit": retrans},
            }
        )
    rows.sort(key=lambda r: r["session_id"])
    return {
        "sessions": rows,
        "totals": {"session_count": len(rows), "anomaly_frames": total_retrans},
    }


def parity_capsule_session_index(capsules: Path | None = None) -> dict:
    return parity_session_index(capsules or capsule_dir())


def reference_session_index(caps: Path) -> dict:
    """Alias retained for contract naming in the validation suite."""
    return parity_session_index(caps)


def reference_capsule_session_index(capsules: Path | None = None) -> dict:
    """Alias retained for contract naming in the validation suite."""
    return parity_capsule_session_index(capsules)


def test_ja4idx_release_binary_rebuilds():
    """Rebuild must produce the ja4idx release binary before subprocess validation runs."""
    rebuild()
    assert BIN.is_file()


def test_ingest_export_pipeline_writes_index():
    """Ingest plus export must write /app/state/session_ledger.jsonl and /app/output/session_index.json"""
    rebuild()
    pipeline()
    assert OUT.is_file()
    assert STATE.is_file()


def test_session_index_json_has_totals_block():
    """The emitted session index JSON must expose sessions and totals top-level keys."""
    rebuild()
    pipeline()
    data = load_index()
    assert "sessions" in data and "totals" in data


def test_totals_session_count_matches_rows():
    """totals.session_count must equal the number of emitted session rows."""
    rebuild()
    pipeline()
    data = load_index()
    assert data["totals"]["session_count"] == len(data["sessions"])


def test_sessions_sorted_lexicographically():
    """Exported sessions must be sorted lexicographically by session_id."""
    rebuild()
    pipeline()
    ids = [s["session_id"] for s in load_index()["sessions"]]
    assert ids == sorted(ids)


def test_alpha_capsule_quad_in_index():
    """The bundled alpha capsule quad must be preserved as session_id 0a0000010a000002."""
    rebuild()
    pipeline()
    data = load_index()
    assert any(s["session_id"] == "0a0000010a000002" for s in data["sessions"])


def test_bravo_capsule_quad_in_index():
    """The bundled bravo capsule quad must be preserved as session_id c0a80105c0a80109."""
    rebuild()
    pipeline()
    data = load_index()
    assert any(s["session_id"] == "c0a80105c0a80109" for s in data["sessions"])


def test_alpha_role_map_client_server():
    """The alpha session role_map must mark 10.0.0.1 as client and 10.0.0.2 as server."""
    rebuild()
    pipeline()
    alpha = next(s for s in load_index()["sessions"] if s["session_id"] == "0a0000010a000002")
    assert alpha["role_map"].get("10.0.0.1") == "client"
    assert alpha["role_map"].get("10.0.0.2") == "server"


def test_ja4_string_shape_per_session():
    """Each emitted session must carry a normalized JA4-style fingerprint string."""
    rebuild()
    pipeline()
    for s in load_index()["sessions"]:
        assert s["ja4"].startswith("t")
        assert "h" in s["ja4"]


def test_alpha_retransmit_anomaly_count():
    """The alpha session must report at least one retransmit anomaly from the bundled fixtures."""
    rebuild()
    pipeline()
    alpha = next(s for s in load_index()["sessions"] if s["session_id"] == "0a0000010a000002")
    assert alpha["anomalies"]["retransmit"] >= 1


def test_unique_frames_never_exceed_frame_count():
    """unique_frames must never exceed frame_count for any emitted session."""
    rebuild()
    pipeline()
    for s in load_index()["sessions"]:
        assert s["unique_frames"] <= s["frame_count"]


def test_unique_frames_matches_parity():
    """unique_frames must equal the independent parity post-dedupe frame count per session."""
    rebuild()
    pipeline()
    got = {s["session_id"]: s for s in load_index()["sessions"]}
    ref = {s["session_id"]: s for s in parity_session_index(capsule_dir())["sessions"]}
    for sid, row in ref.items():
        assert got[sid]["unique_frames"] == row["unique_frames"]


def test_staging_jsonl_created_on_ingest():
    """Intake must create /app/state/session_ledger.jsonl with one or more staged session rows."""
    rebuild()
    pipeline()
    assert STATE.is_file()
    lines = [ln for ln in STATE.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) >= 2


def test_staging_rows_sorted_by_session_id():
    """The staged JSONL rows must be sorted by session_id before export reads them back."""
    rebuild()
    pipeline()
    ids = [json.loads(ln)["session_id"] for ln in STATE.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert ids == sorted(ids)


def test_full_index_matches_parity_session_index():
    """The emitted sessions and totals must match the independent parity session index."""
    rebuild()
    pipeline()
    got = load_index()
    ref = parity_session_index(capsule_dir())
    assert got["totals"]["session_count"] == ref["totals"]["session_count"]
    for g, r in zip(got["sessions"], ref["sessions"]):
        assert g["session_id"] == r["session_id"]
        assert g["role_map"] == r["role_map"]
        assert g["frame_count"] == r["frame_count"]
        assert g["unique_frames"] == r["unique_frames"]
        assert g["anomalies"]["retransmit"] == r["anomalies"]["retransmit"]
        assert g["anomalies"]["fragment_gap"] == r["anomalies"]["fragment_gap"]


def test_per_session_ja4_matches_parity():
    """Each emitted JA4 value must match the independent parity implementation per session."""
    rebuild()
    pipeline()
    got = {s["session_id"]: s for s in load_index()["sessions"]}
    ref = {s["session_id"]: s for s in parity_session_index(capsule_dir())["sessions"]}
    for sid in ref:
        assert got[sid]["ja4"] == ref[sid]["ja4"]


def test_export_is_byte_identical_on_repeat():
    """Repeated export runs must produce byte-identical /app/output/session_index.json output."""
    rebuild()
    pipeline()
    first = OUT.read_bytes()
    pipeline()
    second = OUT.read_bytes()
    assert first == second


def test_split_cli_ingest_then_export():
    """The intake and emit subcommands must work when invoked separately against the ledger file."""
    rebuild()
    caps = capsule_dir()
    if STATE.exists():
        STATE.unlink()
    run([str(BIN), "intake", "--capsules-dir", str(caps), "--ledger", str(STATE)])
    run([str(BIN), "emit", "--ledger", str(STATE), "--out", str(OUT)])
    assert load_index()["totals"]["session_count"] >= 2


def test_bravo_fragment_gap_matches_parity():
    """The bravo session fragment_gap anomaly count must match the parity calculation."""
    rebuild()
    pipeline()
    bravo = next(s for s in load_index()["sessions"] if s["session_id"] == "c0a80105c0a80109")
    ref = next(
        s for s in parity_session_index(capsule_dir())["sessions"] if s["session_id"] == "c0a80105c0a80109"
    )
    assert bravo["anomalies"]["fragment_gap"] == ref["anomalies"]["fragment_gap"]


def test_totals_anomaly_frames_equals_retransmit_sum():
    """totals.anomaly_frames must equal the sum of per-session retransmit anomaly counters."""
    rebuild()
    pipeline()
    data = load_index()
    summed = sum(s["anomalies"]["retransmit"] for s in data["sessions"])
    assert data["totals"]["anomaly_frames"] == summed


def test_tb3_hidden_capsule_index_matches_parity():
    """Hidden capsule fixtures under /tests must fingerprint independently of bundled capsules."""
    if not HIDDEN_CAPS.is_dir():
        return
    rebuild()
    pipeline(HIDDEN_CAPS)
    data = load_index()
    ref = parity_session_index(HIDDEN_CAPS)
    assert data["totals"]["session_count"] == ref["totals"]["session_count"]
    assert data["totals"]["anomaly_frames"] == ref["totals"]["anomaly_frames"]
    assert len(data["sessions"]) == len(ref["sessions"])
    for g, r in zip(data["sessions"], ref["sessions"]):
        assert g["session_id"] == r["session_id"]
        assert g["role_map"] == r["role_map"]
        assert g["ja4"] == r["ja4"]
        assert g["frame_count"] == r["frame_count"]
        assert g["unique_frames"] == r["unique_frames"]
        assert g["anomalies"] == r["anomalies"]


def test_tb3_hidden_capsule_staging_row_count():
    """Hidden capsule fixtures under /tests must stage one JSONL row per hidden session."""
    if not HIDDEN_CAPS.is_dir():
        return
    rebuild()
    pipeline(HIDDEN_CAPS)
    rows = STATE.read_text(encoding="utf-8").strip().splitlines()
    ref = parity_session_index(HIDDEN_CAPS)
    assert len(rows) == ref["totals"]["session_count"]


def test_decoy_telemetry_crate_absent_from_export():
    """The decoy telemetry crate must not leak wrap_latency fields into exported JSON."""
    rebuild()
    pipeline()
    raw = OUT.read_text(encoding="utf-8")
    assert "wrap_latency" not in raw


def test_subprocess_alt_staging_export_path():
    """The CLI must support alternate ledger and emit paths during subprocess verification."""
    rebuild()
    caps = capsule_dir()
    ledger = APP / "state" / "alt_ledger.jsonl"
    out = APP / "output" / "alt_index.json"
    run([str(BIN), "intake", "--capsules-dir", str(caps), "--ledger", str(ledger)])
    run([str(BIN), "emit", "--ledger", str(ledger), "--out", str(out)])
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["totals"]["session_count"] >= 2


def test_parity_helper_smoke_totals():
    """The validation suite must expose an independent parity helper for bundled capsules."""
    rebuild()
    pipeline()
    got = load_index()
    ref = parity_capsule_session_index()
    assert got["totals"]["session_count"] == ref["totals"]["session_count"]


def test_entrypoint_writes_session_index_output_path():
    """Validation must write /app/output/session_index.json after the ingest export pipeline."""
    rebuild()
    pipeline()
    assert Path("/app/output/session_index.json").is_file()


def test_entrypoint_writes_staging_ledger_path():
    """Validation must write /app/state/session_ledger.jsonl after the ingest export pipeline."""
    rebuild()
    pipeline()
    assert Path("/app/state/session_ledger.jsonl").is_file()
