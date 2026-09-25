"""
Verifier for binlim limited BLIM decoder.

Independent reference encoder/decoder implements /app/docs contracts.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

APP = Path("/app")
FIXTURES = APP / "fixtures" / "bin"
TEST_DIR = Path(os.environ.get("TEST_DIR", "/tests"))
HIDDEN = TEST_DIR / "hidden_fixtures" / "binlim"
REPORT = APP / "output" / "decode-report.json"
HEADER = b"BLIM\x01"


def _reset() -> None:
    subprocess.run(["bash", str(APP / "scripts" / "reset-state.sh")], check=True)


def _write_varint(value: int) -> bytes:
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            byte |= 0x80
        out.append(byte)
        if not value:
            break
    return bytes(out)


def _is_canonical_varint(raw: bytes, value: int) -> bool:
    return raw == _write_varint(value)


class RefLimit:
    def __init__(self, max_depth: int, max_bytes: int) -> None:
        self.max_bytes = max_bytes
        self.remaining_depth = max_depth
        self.remaining_bytes = max_bytes
        self.frames: list[int] = []

    def consumed(self) -> int:
        return self.max_bytes - self.remaining_bytes

    def enter_composite(self) -> str | None:
        if self.remaining_depth == 0:
            return "limit_exceeded:depth"
        self.frames.append(self.remaining_depth)
        self.remaining_depth -= 1
        return None

    def leave_composite(self) -> None:
        if self.frames:
            self.remaining_depth = self.frames.pop()

    def charge(self, n: int = 1) -> str | None:
        if self.remaining_bytes < n:
            return "limit_exceeded:bytes"
        self.remaining_bytes -= n
        return None


class RefReader:
    def __init__(self, data: bytes, limits: RefLimit) -> None:
        self.data = data
        self.pos = 0
        self.limits = limits

    def read_byte(self) -> tuple[int | None, str | None]:
        if self.pos >= len(self.data):
            return None, "unexpected_eof"
        err = self.limits.charge(1)
        if err:
            return None, err
        b = self.data[self.pos]
        self.pos += 1
        return b, None

    def read_varint(self) -> tuple[int | None, str | None]:
        value = 0
        shift = 0
        raw = bytearray()
        while True:
            b, err = self.read_byte()
            if err:
                return None, err
            assert b is not None
            raw.append(b)
            value |= (b & 0x7F) << shift
            if b & 0x80 == 0:
                if not _is_canonical_varint(bytes(raw), value):
                    return None, "invalid_varint"
                return value, None
            shift += 7
            if shift > 28:
                return None, "invalid_varint"

    def read_exact(self, n: int) -> tuple[bytes | None, str | None]:
        if self.pos + n > len(self.data):
            return None, "unexpected_eof"
        start = self.pos
        for _ in range(n):
            err = self.limits.charge(1)
            if err:
                return None, err
        chunk = self.data[start : start + n]
        self.pos = start + n
        return chunk, None


def _ref_decode_value(reader: RefReader) -> tuple[Any | None, str | None]:
    tag, err = reader.read_byte()
    if err:
        return None, err
    assert tag is not None
    if tag == 0:
        return None, None
    if tag == 1:
        b, err = reader.read_byte()
        if err:
            return None, err
        return {"kind": "bool", "value": bool(b)}, None
    if tag == 2:
        v, err = reader.read_varint()
        if err:
            return None, err
        return {"kind": "u32", "value": v}, None
    if tag == 3:
        ln, err = reader.read_varint()
        if err:
            return None, err
        raw, err = reader.read_exact(ln)
        if err:
            return None, err
        try:
            s = raw.decode("utf-8")
        except UnicodeDecodeError:
            return None, "invalid_tag"
        return {"kind": "string", "value": s}, None
    if tag == 4:
        count, err = reader.read_varint()
        if err:
            return None, err
        err = reader.limits.enter_composite()
        if err:
            return None, err
        items: list[Any] = []
        for _ in range(count):
            item, err = _ref_decode_value(reader)
            if err:
                return None, err
            items.append(item)
        reader.limits.leave_composite()
        return {"kind": "vec", "items": items}, None
    if tag == 5:
        variant, err = reader.read_varint()
        if err:
            return None, err
        err = reader.limits.enter_composite()
        if err:
            return None, err
        payload, err = _ref_decode_value(reader)
        if err:
            return None, err
        reader.limits.leave_composite()
        return {"kind": "enum", "tag": variant, "payload": payload}, None
    if tag == 6:
        outer, err = reader.read_byte()
        if err:
            return None, err
        if outer == 0:
            return {"kind": "double_option", "value": None}, None
        err = reader.limits.enter_composite()
        if err:
            return None, err
        inner, err = reader.read_byte()
        if err:
            return None, err
        if inner == 0:
            reader.limits.leave_composite()
            return {"kind": "double_option", "value": {"inner": None}}, None
        nested, err = _ref_decode_value(reader)
        if err:
            return None, err
        reader.limits.leave_composite()
        return {"kind": "double_option", "value": {"inner": nested}}, None
    return None, "invalid_tag"


def reference_decode(
    blob: bytes, max_depth: int, max_bytes: int
) -> dict[str, Any]:
    if blob[: len(HEADER)] != HEADER:
        return {
            "status": "error",
            "error_code": "invalid_tag",
            "limit_kind": None,
            "value": None,
            "bytes_consumed": 0,
        }
    limits = RefLimit(max_depth, max_bytes)
    reader = RefReader(blob[len(HEADER) :], limits)
    value, err = _ref_decode_value(reader)
    if err:
        if err.startswith("limit_exceeded"):
            kind = err.split(":", 1)[1]
            return {
                "status": "error",
                "error_code": "limit_exceeded",
                "limit_kind": kind,
                "value": None,
                "bytes_consumed": limits.consumed(),
            }
        code = err
        if code == "invalid_tag":
            code = "invalid_tag"
        return {
            "status": "error",
            "error_code": code,
            "limit_kind": None,
            "value": None,
            "bytes_consumed": limits.consumed(),
        }
    return {
        "status": "ok",
        "error_code": None,
        "limit_kind": None,
        "value": value,
        "bytes_consumed": limits.consumed(),
    }


def _run_decode(
    input_path: Path,
    max_depth: int = 8,
    max_bytes: int = 4096,
    output_path: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    out = output_path or REPORT
    return subprocess.run(
        [
            "binlim",
            "decode",
            "--input",
            str(input_path),
            "--output",
            str(out),
            "--max-depth",
            str(max_depth),
            "--max-bytes",
            str(max_bytes),
        ],
        cwd=APP,
        capture_output=True,
        text=True,
        check=False,
    )


def _load_report(path: Path = REPORT) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_matches_reference(
    blob: bytes, max_depth: int, max_bytes: int, proc: subprocess.CompletedProcess[str]
) -> dict:
    assert proc.returncode in (0, 2, 3, 4), proc.stderr
    report = _load_report()
    expected = reference_decode(blob, max_depth, max_bytes)
    assert report["status"] == expected["status"], report
    assert report.get("error_code") == expected.get("error_code"), report
    assert report.get("limit_kind") == expected.get("limit_kind"), report
    if expected["status"] == "ok":
        assert report["value"] == expected["value"], report
    assert report["bytes_consumed"] == expected["bytes_consumed"], report
    if expected["status"] == "error":
        if expected["error_code"] == "limit_exceeded":
            assert proc.returncode == 2
        elif expected["error_code"] in ("invalid_varint", "invalid_tag"):
            assert proc.returncode == 3
        else:
            assert proc.returncode == 4
    else:
        assert proc.returncode == 0
    return report


def test_null_fixture_decodes_ok() -> None:
    """Bundled null payload decodes successfully with generous limits."""
    _reset()
    blob = (FIXTURES / "001-null.blim").read_bytes()
    proc = _run_decode(FIXTURES / "001-null.blim")
    _assert_matches_reference(blob, 8, 4096, proc)


def test_u32_seven_canonical_ok() -> None:
    """Canonical u32 value 7 decodes to documented JSON shape."""
    _reset()
    blob = (FIXTURES / "002-u32-seven.blim").read_bytes()
    proc = _run_decode(FIXTURES / "002-u32-seven.blim")
    report = _assert_matches_reference(blob, 8, 4096, proc)
    assert report["value"] == {"kind": "u32", "value": 7}


def test_redundant_varint_rejected() -> None:
    """Non-minimal varint encoding must return invalid_varint."""
    _reset()
    blob = (FIXTURES / "003-redundant-zero-u32.blim").read_bytes()
    proc = _run_decode(FIXTURES / "003-redundant-zero-u32.blim")
    report = _assert_matches_reference(blob, 8, 4096, proc)
    assert report["error_code"] == "invalid_varint"


def test_string_byte_budget_counts_length_prefix() -> None:
    """Byte limit must include varint length-prefix bytes for strings."""
    _reset()
    path = HIDDEN / "hidden-tight-string.blim"
    blob = path.read_bytes()
    # tag(1) + len varint(1) + 2 payload bytes charged before byte limit — budget 4
    proc = _run_decode(path, max_depth=4, max_bytes=4)
    report = _assert_matches_reference(blob, 4, 4, proc)
    assert report["error_code"] == "limit_exceeded"
    assert report["limit_kind"] == "bytes"


def test_enum_depth_limit_reports_limit_exceeded() -> None:
    """Depth budget exhaustion on nested enums returns limit_exceeded depth."""
    _reset()
    path = FIXTURES / "005-enum-depth4.blim"
    blob = path.read_bytes()
    proc = _run_decode(path, max_depth=2, max_bytes=512)
    report = _assert_matches_reference(blob, 2, 512, proc)
    assert report["error_code"] == "limit_exceeded"
    assert report["limit_kind"] == "depth"


def test_double_option_uses_single_depth_frame() -> None:
    """Some(Some(null)) must succeed at max_depth 1 per limit contract."""
    _reset()
    path = FIXTURES / "006-double-option-inner-null.blim"
    blob = path.read_bytes()
    proc = _run_decode(path, max_depth=1, max_bytes=256)
    report = _assert_matches_reference(blob, 1, 256, proc)
    assert report["status"] == "ok"


def test_limit_breach_not_mapped_to_unexpected_eof() -> None:
    """LimitExceeded must surface as limit_exceeded, never unexpected_eof."""
    _reset()
    path = FIXTURES / "005-enum-depth4.blim"
    blob = path.read_bytes()
    proc = _run_decode(path, max_depth=1, max_bytes=512)
    report = _assert_matches_reference(blob, 1, 512, proc)
    assert report["error_code"] == "limit_exceeded"
    assert report["error_code"] != "unexpected_eof"


def test_truncated_payload_is_unexpected_eof() -> None:
    """Truncated input with remaining byte budget maps to unexpected_eof."""
    _reset()
    blob = HEADER + bytes([0x02])  # u32 tag without varint body
    with tempfile.NamedTemporaryFile("wb", suffix=".blim", delete=False) as tmp:
        tmp.write(blob)
        tmp_path = Path(tmp.name)
    try:
        proc = _run_decode(tmp_path, max_depth=4, max_bytes=64)
        report = _assert_matches_reference(blob, 4, 64, proc)
        assert report["error_code"] == "unexpected_eof"
    finally:
        tmp_path.unlink(missing_ok=True)


def test_hidden_depth_bomb_seed_profile() -> None:
    """Hidden six-high enum chain fails depth at profile max_depth 3."""
    _reset()
    seed = int(os.environ.get("VERIFIER_SEED", "11"))
    max_depth = 3 + (seed % 2)
    path = HIDDEN / "hidden-enum-depth6.blim"
    blob = path.read_bytes()
    proc = _run_decode(path, max_depth=max_depth, max_bytes=1024)
    report = _assert_matches_reference(blob, max_depth, 1024, proc)
    assert report["error_code"] == "limit_exceeded"
    assert report["limit_kind"] == "depth"


def test_hidden_redundant_varint_long_form() -> None:
    """Hidden triple-byte redundant zero varint is rejected."""
    _reset()
    path = HIDDEN / "hidden-redundant-varint.blim"
    blob = path.read_bytes()
    proc = _run_decode(path, max_depth=6, max_bytes=512)
    report = _assert_matches_reference(blob, 6, 512, proc)
    assert report["error_code"] == "invalid_varint"


def test_short_string_fixture_ok() -> None:
    """Bundled short string decodes with correct byte accounting."""
    _reset()
    path = FIXTURES / "004-short-string.blim"
    blob = path.read_bytes()
    proc = _run_decode(path, max_depth=4, max_bytes=32)
    report = _assert_matches_reference(blob, 4, 32, proc)
    assert report["value"]["value"] == "hey"


def test_generated_depth_bomb_unique_seed() -> None:
    """Runtime-generated enum tower must hit depth limit under independent reference."""
    _reset()
    seed = int(os.environ.get("VERIFIER_SEED", "11"))
    depth = 5 + (seed % 3)
    body = bytes([0x00])
    for i in range(depth):
        body = bytes([0x05]) + _write_varint(i + seed) + body
    blob = HEADER + body
    with tempfile.NamedTemporaryFile("wb", suffix=".blim", delete=False) as tmp:
        tmp.write(blob)
        tmp_path = Path(tmp.name)
    try:
        max_depth = 2
        proc = _run_decode(tmp_path, max_depth=max_depth, max_bytes=2048)
        report = _assert_matches_reference(blob, max_depth, 2048, proc)
        assert report["error_code"] == "limit_exceeded"
    finally:
        tmp_path.unlink(missing_ok=True)
