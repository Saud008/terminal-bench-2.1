"""
Verifier for minizdecode zlib decompressor — independent zlib/adler reference.
"""

from __future__ import annotations

import json
import os
import struct
import subprocess
import zlib
from pathlib import Path

APP = Path("/app")
FIXTURES = APP / "fixtures" / "streams"
VERIFIER_FIXTURES = Path("/opt/verifier-fixtures/streams")
OUTPUT = APP / "output"
STATE = APP / "state"
REPORT = OUTPUT / "decompress-report.json"
STAGING = STATE / "decode-stage.json"
HIDDEN = Path("/tmp/miniz_hidden_streams")
SEED = int(os.environ.get("VERIFIER_SEED", "11"))
TB3_BLOCK_SEED = int(os.environ.get("TB3_BLOCK_SEED", "29"))


def reference_inflate_zlib(blob: bytes) -> bytes:
    """Independent zlib reference used by every roundtrip assertion."""
    return zlib.decompress(blob)


def reference_adler32(data: bytes) -> int:
    return zlib.adler32(data) & 0xFFFFFFFF


def _adler32(data: bytes) -> int:
    return reference_adler32(data)


def _reset() -> None:
    subprocess.run(["bash", str(APP / "scripts" / "reset-state.sh")], check=True)


def _stored_payload_checksum(payload: bytes) -> int:
    return sum(payload) & 0xFFFF


def _decompress_cli(input_path: Path, out_name: str) -> subprocess.CompletedProcess[str]:
    out_path = OUTPUT / out_name
    return subprocess.run(
        [
            "minizdecode",
            "decompress",
            "--input",
            str(input_path),
            "--output",
            str(out_path),
            "--report",
            str(REPORT),
            "--staging",
            str(STAGING),
        ],
        cwd=APP,
        capture_output=True,
        text=True,
        check=False,
    )


def _build_multiblock_stored(parts: list[bytes]) -> bytes:
    """Build zlib-wrapped stored-only multiblock stream."""
    bw_acc = 0
    bw_nbits = 0
    raw = bytearray()

    def write_bits(value: int, count: int) -> None:
        nonlocal bw_acc, bw_nbits
        bw_acc |= (value & ((1 << count) - 1)) << bw_nbits
        bw_nbits += count
        while bw_nbits >= 8:
            raw.append(bw_acc & 0xFF)
            bw_acc >>= 8
            bw_nbits -= 8

    def align() -> None:
        nonlocal bw_acc, bw_nbits
        if bw_nbits:
            raw.append(bw_acc & 0xFF)
            bw_acc = 0
            bw_nbits = 0

    for idx, chunk in enumerate(parts):
        final = 1 if idx == len(parts) - 1 else 0
        write_bits(final, 1)
        write_bits(0, 2)
        align()
        ln = len(chunk)
        raw.extend(struct.pack("<HH", ln, 0xFFFF ^ ln))
        raw.extend(chunk)

    payload = b"".join(parts)
    adler = _adler32(payload)
    cmf, flg = 0x78, 0x01
    while ((cmf << 8) + flg) % 31 != 0:
        flg += 1
    return bytes([cmf, flg]) + bytes(raw) + struct.pack(">I", adler)


def _assert_report_contract(
    report: dict,
    *,
    input_path: Path,
    output_path: Path,
    staging: dict | None = None,
) -> None:
    assert report["input_path"] == str(input_path)
    assert report["output_path"] == str(output_path)
    assert isinstance(report["block_count"], int)
    assert report["block_count"] >= 1
    if staging is not None:
        assert report["block_count"] == staging["block_count"]


def _assert_staging_schema(
    staging: dict,
    *,
    input_path: Path,
    stored_payloads: list[bytes] | None = None,
) -> None:
    assert staging["input_path"] == str(input_path)
    blocks = staging["blocks"]
    assert len(blocks) == staging["block_count"]
    for i, block in enumerate(blocks):
        assert block["index"] == i
        assert block["final"] is (i == len(blocks) - 1)
        if block["block_type"] in ("fixed", "dynamic"):
            assert block["block_checksum"] == 0
    if stored_payloads is not None:
        stored = [b for b in blocks if b["block_type"] == "stored"]
        assert len(stored) == len(stored_payloads)
        for block, payload in zip(stored, stored_payloads):
            assert block["uncompressed_len"] == len(payload)
            assert block["block_checksum"] == _stored_payload_checksum(payload)


def test_public_hello_roundtrip() -> None:
    """Public hello.zlib inflates to zlib reference bytes and report ok."""
    _reset()
    src = FIXTURES / "hello.zlib"
    out_path = OUTPUT / "hello.bin"
    expected = reference_inflate_zlib(src.read_bytes())
    proc = _decompress_cli(src, "hello.bin")
    assert proc.returncode == 0, proc.stderr
    got = out_path.read_bytes()
    assert got == expected
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    staging = json.loads(STAGING.read_text(encoding="utf-8"))
    assert report["ok"] is True
    assert report["uncompressed_len"] == len(expected)
    _assert_report_contract(report, input_path=src, output_path=out_path, staging=staging)


def test_public_bytes256_adler() -> None:
    """bytes256 fixture matches reference length and Adler-32."""
    _reset()
    src = FIXTURES / "bytes256.zlib"
    expected = reference_inflate_zlib(src.read_bytes())
    proc = _decompress_cli(src, "bytes256.bin")
    assert proc.returncode == 0, proc.stderr
    got = (OUTPUT / "bytes256.bin").read_bytes()
    assert got == expected
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["computed_adler32"] == _adler32(got)
    assert report["adler32"] == report["computed_adler32"]


def test_window_repeat_backreference() -> None:
    """window_repeat uses Huffman blocks with LZ77 backreferences across the sliding window."""
    _reset()
    src = FIXTURES / "window_repeat.zlib"
    expected = reference_inflate_zlib(src.read_bytes())
    proc = _decompress_cli(src, "window_repeat.bin")
    assert proc.returncode == 0, proc.stderr
    assert (OUTPUT / "window_repeat.bin").read_bytes() == expected
    staging = json.loads(STAGING.read_text(encoding="utf-8"))
    block_types = {b["block_type"] for b in staging["blocks"]}
    assert block_types & {"fixed", "dynamic"}


def test_huffman_compressed_roundtrip() -> None:
    """huffman_bytes256 fixture uses fixed Huffman DEFLATE blocks with LZ literals."""
    _reset()
    src = FIXTURES / "huffman_bytes256.zlib"
    expected = reference_inflate_zlib(src.read_bytes())
    proc = _decompress_cli(src, "huffman_bytes256.bin")
    assert proc.returncode == 0, proc.stderr
    got = (OUTPUT / "huffman_bytes256.bin").read_bytes()
    assert got == expected
    staging = json.loads(STAGING.read_text(encoding="utf-8"))
    assert any(b["block_type"] == "fixed" for b in staging["blocks"])


def test_dynamic_huffman_tree_roundtrip() -> None:
    """dynamic_tree fixture uses DEFLATE type-2 blocks; staging must record dynamic Huffman."""
    _reset()
    src = FIXTURES / "dynamic_tree.zlib"
    expected = reference_inflate_zlib(src.read_bytes())
    proc = _decompress_cli(src, "dynamic_tree.bin")
    assert proc.returncode == 0, proc.stderr
    assert (OUTPUT / "dynamic_tree.bin").read_bytes() == expected
    staging = json.loads(STAGING.read_text(encoding="utf-8"))
    assert any(b["block_type"] == "dynamic" for b in staging["blocks"])


def test_lz77_ring_buffer_fixture() -> None:
    """lz77_ring fixture requires ring-buffer copy semantics for long LZ77 runs."""
    _reset()
    src = FIXTURES / "lz77_ring.zlib"
    expected = reference_inflate_zlib(src.read_bytes())
    proc = _decompress_cli(src, "lz77_ring.bin")
    assert proc.returncode == 0, proc.stderr
    assert (OUTPUT / "lz77_ring.bin").read_bytes() == expected


def test_staging_snapshot_block_metadata() -> None:
    """Staging JSON matches staging-schema.md: paths, indexes, final, checksums."""
    _reset()
    src = FIXTURES / "twopart.zlib"
    chunks = [b"alpha-", b"beta-", b"gamma"]
    expected = b"".join(chunks)
    proc = _decompress_cli(src, "twopart-staging.bin")
    assert proc.returncode == 0, proc.stderr
    staging = json.loads(STAGING.read_text(encoding="utf-8"))
    assert staging["block_count"] == 3
    assert staging["window_size"] == 32768
    assert staging["staging_adler"] == _adler32(expected)
    _assert_staging_schema(staging, input_path=src, stored_payloads=chunks)

    _reset()
    src_huff = FIXTURES / "huffman_bytes256.zlib"
    expected_huff = reference_inflate_zlib(src_huff.read_bytes())
    proc_huff = _decompress_cli(src_huff, "huff-staging.bin")
    assert proc_huff.returncode == 0, proc_huff.stderr
    staging_huff = json.loads(STAGING.read_text(encoding="utf-8"))
    assert staging_huff["staging_adler"] == _adler32(expected_huff)
    _assert_staging_schema(staging_huff, input_path=src_huff)
    assert any(b["block_type"] == "fixed" for b in staging_huff["blocks"])


def test_instruction_output_paths_written() -> None:
    """Instruction paths /app/output/decompress-report.json and /app/state/decode-stage.json."""
    _reset()
    assert str(REPORT) == "/app/output/decompress-report.json"
    assert str(STAGING) == "/app/state/decode-stage.json"
    src = FIXTURES / "hello.zlib"
    proc = _decompress_cli(src, "hello-paths.bin")
    assert proc.returncode == 0, proc.stderr
    assert REPORT.is_file(), "decompress-report.json must exist"
    assert STAGING.is_file(), "decode-stage.json must exist"
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    staging = json.loads(STAGING.read_text(encoding="utf-8"))
    assert report["output_path"] == str(OUTPUT / "hello-paths.bin")
    assert staging["input_path"] == str(src)
    assert report["computed_adler32"] == staging["staging_adler"]


def _build_zlib_header() -> bytes:
    """Return a valid two-byte zlib CMF/FLG header."""
    cmf, flg = 0x78, 0x01
    while ((cmf << 8) + flg) % 31 != 0:
        flg += 1
    return bytes([cmf, flg])


def _build_reserved_block_type_zlib() -> bytes:
    """Zlib file whose first DEFLATE block uses reserved BTYPE=3."""
    # BFINAL=1 and BTYPE=3 => 3-bit block header 0b111.
    return _build_zlib_header() + bytes([0x07]) + b"\x00\x00\x00\x00"


def test_cli_io_and_format_errors_exit_one() -> None:
    """cli.md: I/O and format failures exit 1 (not checksum mismatch 2)."""
    _reset()
    HIDDEN.mkdir(parents=True, exist_ok=True)

    cases: list[tuple[str, Path | None, bytes | None]] = [
        ("missing_input", HIDDEN / "no-such-stream.zlib", None),
        ("truncated_stream", HIDDEN / "truncated.zlib", _build_zlib_header()),
        ("invalid_header_check", HIDDEN / "bad-header.zlib", bytes([0x78, 0x02, 0x00, 0x00, 0x00, 0x00])),
        ("reserved_block_type", HIDDEN / "bad-block-type.zlib", _build_reserved_block_type_zlib()),
        (
            "truncated_stored_block",
            HIDDEN / "truncated-stored.zlib",
            _build_zlib_header() + bytes([0x01, 0x04, 0x00, 0xFB, 0xFF]) + b"\x00\x00\x00\x00",
        ),
    ]

    for label, path, blob in cases:
        if blob is not None:
            assert path is not None
            path.write_bytes(blob)
        proc = _decompress_cli(path, f"fmt-err-{label}.bin")
        assert proc.returncode == 1, f"{label}: expected exit 1, got {proc.returncode}: {proc.stderr}"


def test_checksum_mismatch_exits_two() -> None:
    """CLI exits 2 when zlib trailer Adler-32 does not match decoded bytes."""
    _reset()
    HIDDEN.mkdir(parents=True, exist_ok=True)
    payload = b"checksum-mismatch-trap"
    blob = _build_multiblock_stored([payload])
    bad_adler = struct.pack(">I", (_adler32(payload) ^ 0xA5A5A5A5) & 0xFFFFFFFF)
    corrupt = blob[:-4] + bad_adler
    hidden_path = HIDDEN / "bad-adler.zlib"
    hidden_path.write_bytes(corrupt)
    proc = _decompress_cli(hidden_path, "bad-adler.bin")
    assert proc.returncode == 2, proc.stderr
    got = (OUTPUT / "bad-adler.bin").read_bytes()
    assert got == payload
    assert got == reference_inflate_zlib(blob[:-4] + struct.pack(">I", _adler32(payload)))


def test_idempotent_rerun() -> None:
    """Second decompress on same input yields identical output and report bytes."""
    _reset()
    src = FIXTURES / "hello.zlib"
    out_path = OUTPUT / "hello.bin"
    proc1 = _decompress_cli(src, "hello.bin")
    assert proc1.returncode == 0
    first_out = out_path.read_bytes()
    first_report = REPORT.read_bytes()
    proc2 = _decompress_cli(src, "hello.bin")
    assert proc2.returncode == 0
    assert out_path.read_bytes() == first_out
    assert REPORT.read_bytes() == first_report


def test_hidden_chained_blocks_with_flush() -> None:
    """/opt/verifier-fixtures TB3 chain must decode including empty middle block."""
    _reset()
    hidden_path = VERIFIER_FIXTURES / "tb3_chain.zlib"
    assert hidden_path.is_file(), "verifier-fixtures tb3_chain.zlib missing"
    part_a = bytes([(TB3_BLOCK_SEED + i) % 256 for i in range(120)])
    part_b = bytes([(TB3_BLOCK_SEED * 3 + i) % 256 for i in range(180)])
    payload = part_a + part_b
    expected = reference_inflate_zlib(hidden_path.read_bytes())
    proc = _decompress_cli(hidden_path, "chain.bin")
    assert proc.returncode == 0, proc.stderr
    assert (OUTPUT / "chain.bin").read_bytes() == payload
    assert (OUTPUT / "chain.bin").read_bytes() == expected
    staging = json.loads(STAGING.read_text(encoding="utf-8"))
    assert staging["block_count"] >= 3


def test_report_staging_adler_alignment() -> None:
    """Report computed_adler32 equals staging_adler for the same run."""
    _reset()
    src = FIXTURES / "bytes256.zlib"
    out_path = OUTPUT / "bytes256-2.bin"
    proc = _decompress_cli(src, "bytes256-2.bin")
    assert proc.returncode == 0, proc.stderr
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    staging = json.loads(STAGING.read_text(encoding="utf-8"))
    assert report["computed_adler32"] == staging["staging_adler"]
    _assert_report_contract(report, input_path=src, output_path=out_path, staging=staging)


def test_multiblock_stored_chain() -> None:
    """twopart.zlib chains three stored blocks; staging must list each boundary."""
    _reset()
    src = FIXTURES / "twopart.zlib"
    out_path = OUTPUT / "twopart.bin"
    expected = b"alpha-" + b"beta-" + b"gamma"
    proc = _decompress_cli(src, "twopart.bin")
    assert proc.returncode == 0, proc.stderr
    assert out_path.read_bytes() == expected
    staging = json.loads(STAGING.read_text(encoding="utf-8"))
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert staging["block_count"] == 3
    _assert_report_contract(report, input_path=src, output_path=out_path, staging=staging)
    stored = [b for b in staging["blocks"] if b["block_type"] == "stored"]
    assert len(stored) == 3
    assert sum(b["uncompressed_len"] for b in stored) == len(expected)


def test_hidden_compressed_lz77_chain() -> None:
    """/opt/verifier-fixtures TB3 lz77 hidden trap must decode via Huffman + window."""
    _reset()
    hidden_path = VERIFIER_FIXTURES / "tb3_lz77.zlib"
    assert hidden_path.is_file(), "verifier-fixtures tb3_lz77.zlib missing"
    seed = TB3_BLOCK_SEED + 7
    head = bytes([(seed + i) % 256 for i in range(64)])
    tail = head + (b"LZ" * 4096) + head
    expected = reference_inflate_zlib(hidden_path.read_bytes())
    proc = _decompress_cli(hidden_path, "lz77_hidden.bin")
    assert proc.returncode == 0, proc.stderr
    assert (OUTPUT / "lz77_hidden.bin").read_bytes() == tail
    assert (OUTPUT / "lz77_hidden.bin").read_bytes() == expected
    staging = json.loads(STAGING.read_text(encoding="utf-8"))
    assert any(b["block_type"] == "dynamic" for b in staging["blocks"])


def test_empty_middle_block_fixture() -> None:
    """empty_mid.zlib includes a zero-length stored block between payload chunks."""
    _reset()
    src = FIXTURES / "empty_mid.zlib"
    expected = b"part-a" + b"part-b"
    proc = _decompress_cli(src, "empty_mid.bin")
    assert proc.returncode == 0, proc.stderr
    assert (OUTPUT / "empty_mid.bin").read_bytes() == expected
    staging = json.loads(STAGING.read_text(encoding="utf-8"))
    assert staging["block_count"] >= 3


def test_reference_inflate_matches_all_public_streams() -> None:
    """reference_inflate_zlib agrees with bundled fixtures before CLI decode."""
    for name in (
        "hello.zlib",
        "bytes256.zlib",
        "tiny.zlib",
        "twopart.zlib",
        "empty_mid.zlib",
        "window_repeat.zlib",
        "huffman_bytes256.zlib",
        "dynamic_tree.zlib",
        "lz77_ring.zlib",
    ):
        src = FIXTURES / name
        assert reference_inflate_zlib(src.read_bytes())


def test_tb3_verifier_fixture_chain_seed_contract() -> None:
    """TB3_BLOCK_SEED drives /opt/verifier-fixtures chain payload bytes."""
    hidden_path = VERIFIER_FIXTURES / "tb3_chain.zlib"
    assert hidden_path.is_file()
    part_a = bytes([(TB3_BLOCK_SEED + i) % 256 for i in range(120)])
    part_b = bytes([(TB3_BLOCK_SEED * 3 + i) % 256 for i in range(180)])
    assert reference_inflate_zlib(hidden_path.read_bytes()) == part_a + part_b


def test_tb3_verifier_fixture_lz77_reference_roundtrip() -> None:
    """TB3 lz77 verifier stream inflates to reference bytes via subprocess CLI."""
    _reset()
    hidden_path = VERIFIER_FIXTURES / "tb3_lz77.zlib"
    assert hidden_path.is_file()
    expected = reference_inflate_zlib(hidden_path.read_bytes())
    proc = _decompress_cli(hidden_path, "tb3-lz77-ref.bin")
    assert proc.returncode == 0, proc.stderr
    assert (OUTPUT / "tb3-lz77-ref.bin").read_bytes() == expected
