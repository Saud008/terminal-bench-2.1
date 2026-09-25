"""Behavioral tests for fbctl wire-buffer relayout governor."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from reference_wire import (
    LEDGER_MAGIC,
    reference_relayout,
    reference_roots_for_wire,
    reference_seal,
    parse_ledger,
    scan_gaps,
)

FBCTL = "/app/bin/fbctl"
LEDGER = Path("/app/state/vtable-ledger.bin")
RELAYOUT = Path("/app/output/relayout.wire")
SEAL = Path("/app/output/wire-seal.txt")
BUNDLED = Path("/app/data/wires")
TB3_SRC = Path("/opt/verifier-fixtures/tb3-wires")


def _run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=check, capture_output=True, text=True)


def _fresh() -> None:
    for p in (LEDGER, RELAYOUT, SEAL):
        if p.exists():
            p.unlink()


def _ingest(wires_dir: Path) -> None:
    _run([FBCTL, "ingest", str(wires_dir)])


def _export() -> None:
    _run([FBCTL, "relayout", "export"])


def _pipeline(wires_dir: Path) -> None:
    _fresh()
    _ingest(wires_dir)
    _export()


@pytest.fixture(autouse=True)
def clean_state():
    _fresh()
    yield
    _fresh()


def test_fbctl_binary_exists():
    """Instruction requires /app/bin/fbctl built from workspace."""
    assert Path(FBCTL).is_file()


def test_bundled_wires_directory_exists():
    """Instruction cites bundled fixtures under /app/data/wires/."""
    assert BUNDLED.is_dir()
    assert (BUNDLED / "scene_a.wire").is_file()
    assert (BUNDLED / "scene_b.wire").is_file()


def test_ingest_writes_ledger_snapshot():
    """Ingest must write binary ledger at /app/state/vtable-ledger.bin."""
    _ingest(BUNDLED)
    assert LEDGER.is_file()
    assert LEDGER.read_bytes()[:4] == LEDGER_MAGIC


def test_ledger_lists_entries_in_sorted_order():
    """Ledger entries follow sorted source filename order."""
    _ingest(BUNDLED)
    ledger = parse_ledger(LEDGER)
    names = [e["name"] for e in ledger["entries"]]
    assert names == ["scene_a.wire", "scene_b.wire"]


def test_ingest_seq_monotonic():
    """Ingest increments ingest_seq on each ingest call."""
    _ingest(BUNDLED)
    first = parse_ledger(LEDGER)["ingest_seq"]
    _ingest(BUNDLED)
    second = parse_ledger(LEDGER)["ingest_seq"]
    assert second == first + 1


def test_scene_a_gap_span_recorded():
    """scene_a wire skip-gap span is captured in the ledger."""
    _ingest(BUNDLED)
    entry = parse_ledger(LEDGER)["entries"][0]
    gaps = entry["gaps"]
    assert len(gaps) == 1
    assert gaps[0]["start"] == 0
    assert entry["wire"][0:4] == b"GAPS"


def test_vtable_slot_decoded_little_endian_scene_a():
    """vtable-decode-contract requires slot zero equals eight for scene_a."""
    _ingest(BUNDLED)
    roots = parse_ledger(LEDGER)["entries"][0]["roots"]
    assert len(roots) == 1
    assert roots[0]["slots"][0] == 8


def test_scene_b_vtable_object_size():
    """Ledger stores object_size from scene_b vtable header."""
    _ingest(BUNDLED)
    entry = parse_ledger(LEDGER)["entries"][1]
    assert entry["roots"][0]["object_size"] == 8


def test_relayout_export_creates_artifacts():
    """relayout export writes relayout.wire and wire-seal.txt."""
    _pipeline(BUNDLED)
    assert RELAYOUT.is_file()
    assert SEAL.is_file()


def test_relayout_preserves_wire_length_scene_a():
    """relayout-padding.md forbids footer corruption for bundled scene_a."""
    _pipeline(BUNDLED)
    src = (BUNDLED / "scene_a.wire").read_bytes()
    got = RELAYOUT.read_bytes()
    assert len(got) == len(src)


def test_relayout_preserves_gap_magic_at_offset_zero():
    """skip-gap-preservation.md requires GAPS magic at offset zero."""
    _pipeline(BUNDLED)
    got = RELAYOUT.read_bytes()
    assert got[0:4] == b"GAPS"


def test_gap_bytes_preserved_byte_for_byte():
    """Gap span bytes must match the ingested scene_a source wire."""
    _pipeline(BUNDLED)
    src = (BUNDLED / "scene_a.wire").read_bytes()
    got = RELAYOUT.read_bytes()
    gaps = scan_gaps(src)
    for gap in gaps:
        start = gap["start"]
        end = start + gap["length"]
        assert got[start:end] == src[start:end]


def test_wire_seal_matches_relayout_file():
    """wire-seal-export.md digest must match on-disk relayout.wire bytes."""
    _pipeline(BUNDLED)
    wire = RELAYOUT.read_bytes()
    seal = SEAL.read_text(encoding="utf-8").strip()
    assert seal == reference_seal(wire)


def test_wire_seal_matches_reference_layout():
    """Independent reference seal matches export for scene_a."""
    _pipeline(BUNDLED)
    src = (BUNDLED / "scene_a.wire").read_bytes()
    expected = reference_seal(reference_relayout(src))
    assert SEAL.read_text(encoding="utf-8").strip() == expected


def test_root_footer_unchanged_after_export():
    """Root footer bytes must remain identical for scene_a relayout."""
    _pipeline(BUNDLED)
    src = (BUNDLED / "scene_a.wire").read_bytes()
    got = RELAYOUT.read_bytes()
    assert got[-4:] == src[-4:]


def test_reference_subprocess_cli_roundtrip():
    """Independent reference validates ingest plus export via subprocess CLI."""
    _pipeline(BUNDLED)
    src = (BUNDLED / "scene_a.wire").read_bytes()
    ref = reference_relayout(src)
    assert RELAYOUT.read_bytes() == ref


def test_tb3_fixture_directory_available():
    """Hidden verifier fixtures directory is mounted for TB3 probes."""
    assert TB3_SRC.is_dir()
    assert (TB3_SRC / "scene_gamma.wire").is_file()


def test_tb3_multi_root_ledger_records_two_roots():
    """MR2R footer wires must record two roots in the ledger."""
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        shutil.copy(TB3_SRC / "scene_gamma.wire", work / "scene_gamma.wire")
        _ingest(work)
        entry = parse_ledger(LEDGER)["entries"][0]
        assert len(entry["roots"]) == 2


def test_tb3_multi_root_export_preserves_both_footers():
    """Hidden gamma wire export preserves MR2R footer and both root bodies."""
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        shutil.copy(TB3_SRC / "scene_gamma.wire", work / "scene_gamma.wire")
        _pipeline(work)
        src = (work / "scene_gamma.wire").read_bytes()
        got = RELAYOUT.read_bytes()
        assert got[-12:-8] == b"MR2R"
        assert len(got) == len(src)


def test_tb3_hidden_seal_matches_reference():
    """TB3 gamma relayout seal must match independent reference digest."""
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        shutil.copy(TB3_SRC / "scene_gamma.wire", work / "scene_gamma.wire")
        _pipeline(work)
        src = (work / "scene_gamma.wire").read_bytes()
        ref = reference_seal(reference_relayout(src))
        assert SEAL.read_text(encoding="utf-8").strip() == ref


def test_tb3_secondary_root_slot_decoded():
    """Second root in gamma wire must decode slot eight little-endian."""
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        shutil.copy(TB3_SRC / "scene_gamma.wire", work / "scene_gamma.wire")
        _ingest(work)
        roots = parse_ledger(LEDGER)["entries"][0]["roots"]
        assert roots[1]["slots"][0] == 8


def test_export_reads_ledger_not_source_dir(tmp_path: Path):
    """relayout export must read ledger only; mutating source must not change output."""
    _ingest(BUNDLED)
    shutil.copy(BUNDLED / "scene_a.wire", tmp_path / "mutated.wire")
    _export()
    first = RELAYOUT.read_bytes()
    (tmp_path / "mutated.wire").write_bytes(b"\x00" * 20)
    _export()
    second = RELAYOUT.read_bytes()
    assert first == second


def test_scene_a_reference_root_table_offset():
    """Independent reference root discovery matches ledger table_off."""
    _ingest(BUNDLED)
    roots = parse_ledger(LEDGER)["entries"][0]["roots"]
    ref_roots = reference_roots_for_wire(BUNDLED / "scene_a.wire")
    assert roots[0]["table_off"] == ref_roots[0]["table_off"]
