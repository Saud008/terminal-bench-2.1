"""Behavioral verifier for mdtable export CLI."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from reference_parser import (
    build_seed_table,
    parse_html_rows,
    parse_html_td_cells,
    reference_export,
)

APP = Path("/app")
CLI = Path("/usr/local/bin/mdtable")
TABLES = APP / "fixtures/tables"
MANIFEST = APP / "fixtures/manifest.json"
OUTPUT = APP / "output"
SNAPSHOT = APP / "state/grid.snapshot.json"
RESET = APP / "scripts/reset-state.sh"
BUILD_SEED = os.environ.get("VERIFIER_SEED", "markdown-table-colspan-span-export-repair")
TEST_ROOT = Path(os.environ.get("TEST_DIR", "/tests"))
VERIFIER_FIXTURES = Path(
    os.environ.get("VERIFIER_FIXTURES", str(TEST_ROOT / "verifier-fixtures"))
)

FIXTURE_NAMES = [
    "001-basic",
    "002-colspan",
    "003-rowspan",
    "004-escaped-pipe",
    "005-alignment-variants",
    "006-mixed-grid",
]

PROTECTED_SHA256: dict[str, str] = {
    "manifest.json": "62ef3b195e4b486ea8f09d6ba9d682f01a9c3da92764dbf4e53f4f886505b476",
    "tables/001-basic.md": "5563f02d1b5b6df7a461fbcdc4fe8db1bd7d898ea773ce6ca25985acf7da402f",
    "tables/002-colspan.md": "dc1203b25c6acebad5f479c60bb3277b2a46a03f3b0fcef987a1d6d3d85ccb21",
    "tables/003-rowspan.md": "9604c6bc6e6c5d4acafc8eb1a9072b7b0397ed536a8a4676f1774cf2ecfd2c9f",
    "tables/004-escaped-pipe.md": "5f3e41c84f4327fd76b19b6984fe7c3be281bc0ade597ff022fd07f354fb5cf8",
    "tables/005-alignment-variants.md": "0b32bf266fff48878e4e3f1236b626d205a99c647ea309b28db7018da3e84655",
    "tables/006-mixed-grid.md": "8e315f6d5ec6e16b9a22da38a13a0dd5f2e4a89eb338783cd33d94f2d53bdf3a",
}

EXPECTED_MANIFEST_ENTRIES = {
    key: value for key, value in PROTECTED_SHA256.items() if key != "manifest.json"
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(cmd: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd or APP),
        capture_output=True,
        text=True,
        check=False,
    )


def reset() -> None:
    proc = run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def build_install() -> None:
    proc = run(["cargo", "build", "--release", "--locked", "--offline", "-p", "mdtable"])
    assert proc.returncode == 0, proc.stderr
    run(["install", "-m", "0755", str(APP / "target/release/mdtable"), str(CLI)])


def export_json(src: Path, out: Path) -> subprocess.CompletedProcess[str]:
    out.parent.mkdir(parents=True, exist_ok=True)
    return run([str(CLI), "export", "--input", str(src), "--export", str(out), "--format", "json"])


def export_html(src: Path, out: Path) -> subprocess.CompletedProcess[str]:
    out.parent.mkdir(parents=True, exist_ok=True)
    return run([str(CLI), "export", "--input", str(src), "--export", str(out), "--format", "html"])


def publish_json(out: Path) -> subprocess.CompletedProcess[str]:
    out.parent.mkdir(parents=True, exist_ok=True)
    return run([str(CLI), "publish", "--export", str(out), "--format", "json"])


def publish_html(out: Path) -> subprocess.CompletedProcess[str]:
    out.parent.mkdir(parents=True, exist_ok=True)
    return run([str(CLI), "publish", "--export", str(out), "--format", "html"])


def assert_html_matches_reference(got_html: str, source: Path) -> None:
    """Compare parsed HTML table semantics against the reference grid model."""
    expect_doc = reference_export(source)
    rows = parse_html_rows(got_html)
    assert len(rows) == len(expect_doc["rows"])
    for row_html, expect_row in zip(rows, expect_doc["rows"]):
        parsed = parse_html_td_cells(row_html)
        assert len(parsed) == len(expect_row["cells"])
        for td, expect_cell in zip(parsed, expect_row["cells"]):
            assert td["text"] == expect_cell["text"]
            assert td["colspan"] == expect_cell["colspan"]
            assert td["rowspan"] == expect_cell["rowspan"]


class TestMdTableExport:
    """mdtable export requirements."""

    def setup_method(self) -> None:
        reset()
        build_install()

    def test_fixture_integrity(self) -> None:
        """Bundled fixtures and manifest must match pinned build digests."""
        for rel, digest in PROTECTED_SHA256.items():
            path = APP / "fixtures" / rel
            assert path.is_file(), rel
            assert sha256_file(path) == digest, rel
        on_disk = json.loads(MANIFEST.read_text(encoding="utf-8"))
        assert on_disk == EXPECTED_MANIFEST_ENTRIES

    def test_hidden_fixture_not_baked_into_image(self) -> None:
        """Verifier-only tables must not ship in the agent image or fixture seed."""
        hidden = APP / "fixtures" / "tables" / "007-duplicate-text.md"
        assert not hidden.is_file(), "hidden fixture must not live under /app/fixtures"
        seed_hidden = Path("/opt/fixture-seed/tables/007-duplicate-text.md")
        assert not seed_hidden.is_file(), "hidden fixture must not be copied into /opt/fixture-seed"
        verifier_copy = VERIFIER_FIXTURES / "tables" / "007-duplicate-text.md"
        assert verifier_copy.is_file(), "verifier fixture mount missing"

    @pytest.mark.parametrize("name", FIXTURE_NAMES)
    def test_json_matches_reference(self, name: str) -> None:
        """Each catalog table JSON export must match the independent reference parser."""
        src = TABLES / f"{name}.md"
        out = OUTPUT / f"{name}.json"
        proc = export_json(src, out)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        got = json.loads(out.read_text(encoding="utf-8"))
        expect = reference_export(src)
        expect["source"] = got["source"]
        assert got == expect

    def test_alignment_row_not_exported(self) -> None:
        """Alignment row must not appear as a body row in JSON export."""
        src = TABLES / "001-basic.md"
        out = OUTPUT / "align-check.json"
        assert export_json(src, out).returncode == 0
        data = json.loads(out.read_text(encoding="utf-8"))
        texts = {c["text"] for row in data["rows"] for c in row["cells"]}
        assert "---" not in texts
        assert len(data["rows"]) == 3

    def test_colspan_grid_width(self) -> None:
        """Colspan must expand column_count beyond raw cell count."""
        src = TABLES / "002-colspan.md"
        out = OUTPUT / "colspan-check.json"
        assert export_json(src, out).returncode == 0
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["column_count"] == 4
        merged = next(c for row in data["rows"] for c in row["cells"] if c["text"] == "Merged")
        assert merged["colspan"] == 2

    def test_rowspan_skips_occupied_slot(self) -> None:
        """Rowspan must leave the anchored column occupied on the next row."""
        src = TABLES / "003-rowspan.md"
        out = OUTPUT / "rowspan-check.json"
        assert export_json(src, out).returncode == 0
        data = json.loads(out.read_text(encoding="utf-8"))
        row2 = data["rows"][2]
        cols = {c["col"] for c in row2["cells"]}
        assert 0 not in cols
        assert data["rows"][1]["cells"][0]["rowspan"] == 2

    def test_escaped_pipe_single_cell(self) -> None:
        """Escaped pipe must not split a cell into two columns."""
        src = TABLES / "004-escaped-pipe.md"
        out = OUTPUT / "pipe-check.json"
        assert export_json(src, out).returncode == 0
        data = json.loads(out.read_text(encoding="utf-8"))
        body = data["rows"][1]
        assert len(body["cells"]) == 2
        assert body["cells"][0]["text"] == "a|b"

    def test_html_structure_matches_reference(self) -> None:
        """HTML export must match reference grid structure, not only internal JSON pairing."""
        src = TABLES / "006-mixed-grid.md"
        json_out = OUTPUT / "mixed.json"
        html_out = OUTPUT / "mixed.html"
        assert export_json(src, json_out).returncode == 0
        assert export_html(src, html_out).returncode == 0
        got_html = html_out.read_text(encoding="utf-8")
        assert_html_matches_reference(got_html, src)
        got_doc = json.loads(json_out.read_text(encoding="utf-8"))
        rows = parse_html_rows(got_html)
        for row_html, got_row in zip(rows, got_doc["rows"]):
            parsed = parse_html_td_cells(row_html)
            assert len(parsed) == len(got_row["cells"])

    def test_html_colspan_fixture_matches_reference(self) -> None:
        """Colspan fixture HTML must match reference structure and strip span markers."""
        src = TABLES / "002-colspan.md"
        html_out = OUTPUT / "colspan.html"
        assert export_html(src, html_out).returncode == 0
        got_html = html_out.read_text(encoding="utf-8")
        assert_html_matches_reference(got_html, src)
        merged = next(
            cell
            for row in parse_html_rows(got_html)
            for cell in parse_html_td_cells(row)
            if cell["text"] == "Merged"
        )
        assert merged["colspan"] == 2
        assert ">2<" not in got_html

    def test_duplicate_text_distinct_spans(self) -> None:
        """Duplicate cell text with different spans must export distinct grid positions."""
        src = VERIFIER_FIXTURES / "tables" / "007-duplicate-text.md"
        out = OUTPUT / "dupe.json"
        assert export_json(src, out).returncode == 0
        got = json.loads(out.read_text(encoding="utf-8"))
        expect = reference_export(src)
        expect["source"] = got["source"]
        assert got == expect
        wide = next(c for row in got["rows"] for c in row["cells"] if c["colspan"] == 2)
        assert wide["text"] == "same"

    def test_seed_dynamic_table(self, tmp_path: Path) -> None:
        """VERIFIER_SEED builds a fresh table with colspan variation."""
        table, _ = build_seed_table(BUILD_SEED)
        out = tmp_path / "seed.json"
        proc = export_json(table, out)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = json.loads(out.read_text(encoding="utf-8"))
        expect = reference_export(table)
        expect["source"] = got["source"]
        assert got == expect

    def test_isolated_copy_matches_reference(self, tmp_path: Path) -> None:
        """Export from an isolated copy must match reference."""
        copied = tmp_path / "001-basic.md"
        shutil.copy2(TABLES / "001-basic.md", copied)
        out = tmp_path / "out.json"
        proc = export_json(copied, out)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = json.loads(out.read_text(encoding="utf-8"))
        expect = reference_export(copied)
        expect["source"] = got["source"]
        assert got == expect

    def test_idempotent_json_export(self) -> None:
        """Repeated export must write byte-identical JSON."""
        src = TABLES / "001-basic.md"
        out = OUTPUT / "idem.json"
        assert export_json(src, out).returncode == 0
        first = out.read_text(encoding="utf-8")
        assert export_json(src, out).returncode == 0
        assert out.read_text(encoding="utf-8") == first

    def test_missing_input_fails(self) -> None:
        """Missing input file must exit non-zero."""
        out = OUTPUT / "missing.json"
        proc = export_json(TABLES / "no-such-table.md", out)
        assert proc.returncode != 0

    def test_packages_order_trap_column_count(self) -> None:
        """Mixed grid column_count must reflect colspan occupancy not raw counts."""
        src = TABLES / "006-mixed-grid.md"
        out = OUTPUT / "grid-width.json"
        assert export_json(src, out).returncode == 0
        data = json.loads(out.read_text(encoding="utf-8"))
        expect = reference_export(src)
        assert data["column_count"] == expect["column_count"]
        assert data["column_count"] == 5

    def test_export_writes_grid_snapshot(self) -> None:
        """Successful export must persist the grid snapshot before publish."""
        src = TABLES / "001-basic.md"
        out = OUTPUT / "snapshot-check.json"
        assert export_json(src, out).returncode == 0
        assert SNAPSHOT.is_file(), "grid.snapshot.json missing"
        snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        assert snap.get("version") == 1
        assert isinstance(snap.get("export", {}).get("rows"), list)

    def test_publish_reads_snapshot_only(self) -> None:
        """Publish must reflect mutated snapshot bytes, not recomputed grid width."""
        src = TABLES / "006-mixed-grid.md"
        out = OUTPUT / "mixed-publish.json"
        assert export_json(src, out).returncode == 0
        snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        snap["export"]["column_count"] = 99
        SNAPSHOT.write_text(json.dumps(snap, indent=2) + "\n", encoding="utf-8")
        mutated = OUTPUT / "mixed-mutated.json"
        assert publish_json(mutated).returncode == 0
        data = json.loads(mutated.read_text(encoding="utf-8"))
        assert data["column_count"] == 99

    def test_publish_without_snapshot_fails(self) -> None:
        """Publish must fail when no grid snapshot exists."""
        src = TABLES / "001-basic.md"
        assert export_json(src, OUTPUT / "pre-snapshot.json").returncode == 0
        SNAPSHOT.unlink()
        proc = publish_json(OUTPUT / "no-snapshot.json")
        assert proc.returncode != 0
