"""Behavioral tests for component-gov package admission and sealed audit export."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest
from reference_component_sections import (
    canonical_imports,
    decode_exports_guarded,
    import_reorder_digest,
    parse_cwrc,
    reference_attest_component,
    resolve_surfaces,
    resolve_type_index,
)

GOV = "/app/bin/component-gov"
LEDGER = Path("/app/state/import-alias.bin")
EXPORT = Path("/app/output/component-attestation.json")
BUNDLED = Path("/app/data/components")
TB3 = Path(__file__).resolve().parent / "data"


def _run(
    cmd: list[str], *, env: dict | None = None, check: bool = True
) -> subprocess.CompletedProcess:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(cmd, check=check, capture_output=True, text=True, env=merged)


def _fresh() -> None:
    for p in (LEDGER, EXPORT):
        if p.exists():
            p.unlink()


def _load(components_dir: Path) -> None:
    _run([GOV, "load", str(components_dir)])


def _attest() -> None:
    _run([GOV, "attest", "export"])


def _pipeline(components_dir: Path) -> None:
    _fresh()
    _load(components_dir)
    _attest()


@pytest.fixture(autouse=True)
def clean_state():
    _fresh()
    yield
    _fresh()


def test_component_gov_binary_exists():
    """Instruction requires /app/bin/component-gov built from workspace."""
    assert Path(GOV).is_file()


def test_bundled_components_exist():
    """Instruction cites bundled fixtures under /app/data/components/."""
    assert BUNDLED.is_dir()
    assert (BUNDLED / "tuple_order.cwasm").is_file()
    assert (BUNDLED / "alias_basic.cwasm").is_file()
    assert (BUNDLED / "chain_surface.cwasm").is_file()


def test_load_writes_binary_ledger():
    """Load writes ledger only; it must not publish attestation JSON."""
    _load(BUNDLED)
    assert LEDGER.is_file()
    assert LEDGER.read_bytes()[:4] == b"IAL1"
    assert not EXPORT.exists()


def test_ledger_snapshot_has_components():
    """Ledger must capture bundled component filenames."""
    _load(BUNDLED)
    raw = LEDGER.read_bytes()
    assert b"tuple_order.cwasm" in raw
    assert b"alias_basic.cwasm" in raw


def test_load_ingest_seq_monotonic():
    """Load increments ingest_seq on each load call."""
    _load(BUNDLED)
    _attest()
    seq1 = json.loads(EXPORT.read_text(encoding="utf-8"))["ingest_seq"]
    _load(BUNDLED)
    _attest()
    seq2 = json.loads(EXPORT.read_text(encoding="utf-8"))["ingest_seq"]
    assert seq2 == seq1 + 1


def test_attest_export_creates_json():
    """attest export writes /app/output/component-attestation.json."""
    _pipeline(BUNDLED)
    assert EXPORT.is_file()
    doc = json.loads(EXPORT.read_text(encoding="utf-8"))
    assert "components" in doc


def test_attest_reads_ledger_only():
    """attest export must not re-read bundled component directory."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        for name in ("tuple_order.cwasm", "alias_basic.cwasm"):
            shutil.copy(BUNDLED / name, tmp_path / name)
        _load(tmp_path)
        shutil.rmtree(tmp_path)
        _attest()
        doc = json.loads(EXPORT.read_text(encoding="utf-8"))
        assert len(doc["components"]) == 2


def test_tuple_order_canonical_rank():
    """import-tuple-rank.md module-name tuple ordering."""
    raw = (BUNDLED / "tuple_order.cwasm").read_bytes()
    ref = reference_attest_component("tuple_order.cwasm", raw)
    _pipeline(BUNDLED)
    got = json.loads(EXPORT.read_text(encoding="utf-8"))
    comp = next(c for c in got["components"] if c["name"] == "tuple_order.cwasm")
    assert comp["imports"] == ref["imports"]
    modules = [r["module"] for r in comp["imports"]]
    assert modules == ["aa", "b"]


def test_tuple_order_digest_matches_reference():
    """attestation-digest.md canonical import reorder digest."""
    raw = (BUNDLED / "tuple_order.cwasm").read_bytes()
    ref_digest = reference_attest_component("tuple_order.cwasm", raw)[
        "import_reorder_digest"
    ]
    _pipeline(BUNDLED)
    got = json.loads(EXPORT.read_text(encoding="utf-8"))
    comp = next(c for c in got["components"] if c["name"] == "tuple_order.cwasm")
    assert comp["import_reorder_digest"] == ref_digest


def test_alias_type_index_resolution():
    """component-type-alias-index.md module-type indices."""
    raw = (BUNDLED / "alias_basic.cwasm").read_bytes()
    ref = reference_attest_component("alias_basic.cwasm", raw)
    _pipeline(BUNDLED)
    got = json.loads(EXPORT.read_text(encoding="utf-8"))
    comp = next(c for c in got["components"] if c["name"] == "alias_basic.cwasm")
    assert comp["imports"][0]["type_index"] == ref["imports"][0]["type_index"] == 99


def test_export_leb128_guard_reference():
    """export-span-authenticity.md rejects overstated export section spans."""
    payload = bytes([1, 4]) + b"term"
    with pytest.raises(ValueError, match="leb128 span"):
        decode_exports_guarded(payload, declared_len=99)


def test_export_span_overstated_rejected_by_cli():
    """export-span-authenticity.md: span past remaining bytes must be rejected before kind tags."""
    assert (TB3 / "tb3_span_overstated.cwasm").is_file()
    with tempfile.TemporaryDirectory() as tmp:
        shutil.copy(
            TB3 / "tb3_span_overstated.cwasm", Path(tmp) / "tb3_span_overstated.cwasm"
        )
        proc = _run([GOV, "load", tmp], check=False)
        assert proc.returncode != 0
        assert "export section" in proc.stderr
        assert not LEDGER.exists()


def test_export_span_overstated_rejected_by_reference():
    """Reference parser agrees the overstated export span is inadmissible."""
    raw = (TB3 / "tb3_span_overstated.cwasm").read_bytes()
    with pytest.raises(ValueError, match="export section length exceeds file"):
        parse_cwrc(raw)


def test_chain_surface_transitive_resolution():
    """instance-reexport-closure.md transitive instance export closure."""
    raw = (BUNDLED / "chain_surface.cwasm").read_bytes()
    ref = reference_attest_component("chain_surface.cwasm", raw)
    _pipeline(BUNDLED)
    got = json.loads(EXPORT.read_text(encoding="utf-8"))
    comp = next(c for c in got["components"] if c["name"] == "chain_surface.cwasm")
    assert comp["surface_exports"] == ref["surface_exports"]
    assert comp["surface_exports"][0]["resolved_leaf"] == "leaf"


def test_reference_parser_subprocess_agrees_tuple_order():
    """Independent reference parser agrees on canonical import tuple rank."""
    raw = (BUNDLED / "tuple_order.cwasm").read_bytes()
    parsed = parse_cwrc(raw)
    ordered = canonical_imports(parsed["imports"])
    assert ordered[0]["module"] == "aa"


def test_byte_level_import_order_assertion():
    """Byte-level module bytes precede name bytes in canonical rank."""
    raw = (BUNDLED / "tuple_order.cwasm").read_bytes()
    parsed = parse_cwrc(raw)
    ordered = canonical_imports(parsed["imports"])
    key0 = (ordered[0]["module"].encode(), ordered[0]["name"].encode())
    key1 = (ordered[1]["module"].encode(), ordered[1]["name"].encode())
    assert key0 < key1


def test_tb3_alias_heavy_hidden_fixture():
    """Hidden verifier fixture with alias-heavy imports."""
    assert (TB3 / "tb3_alias_heavy.cwasm").is_file()
    with tempfile.TemporaryDirectory() as tmp:
        for name in ("tuple_order.cwasm", "tb3_alias_heavy.cwasm"):
            shutil.copy(
                TB3 / name if name.startswith("tb3") else BUNDLED / name,
                Path(tmp) / name,
            )
        raw = (Path(tmp) / "tb3_alias_heavy.cwasm").read_bytes()
        ref = reference_attest_component("tb3_alias_heavy.cwasm", raw)
        _pipeline(Path(tmp))
        got = json.loads(EXPORT.read_text(encoding="utf-8"))
        comp = next(
            c for c in got["components"] if c["name"] == "tb3_alias_heavy.cwasm"
        )
        assert comp["imports"] == ref["imports"]


def test_tb3_type_alias_offset_env():
    """TB3_TYPE_ALIAS_OFFSET mutates module-type indices at runtime."""
    with tempfile.TemporaryDirectory() as tmp:
        shutil.copy(BUNDLED / "alias_basic.cwasm", Path(tmp) / "alias_basic.cwasm")
        _fresh()
        _run([GOV, "load", tmp], env={"TB3_TYPE_ALIAS_OFFSET": "3"})
        _run([GOV, "attest", "export"], env={"TB3_TYPE_ALIAS_OFFSET": "3"})
        got = json.loads(EXPORT.read_text(encoding="utf-8"))
        comp = got["components"][0]
        assert comp["imports"][0]["type_index"] == 102


def test_tb3_chain_deep_hidden_surface():
    """Hidden chain fixture requires transitive re-export closure."""
    assert (TB3 / "tb3_chain_deep.cwasm").is_file()
    with tempfile.TemporaryDirectory() as tmp:
        shutil.copy(TB3 / "tb3_chain_deep.cwasm", Path(tmp) / "tb3_chain_deep.cwasm")
        raw = (TB3 / "tb3_chain_deep.cwasm").read_bytes()
        ref = reference_attest_component("tb3_chain_deep.cwasm", raw)
        _pipeline(Path(tmp))
        got = json.loads(EXPORT.read_text(encoding="utf-8"))
        comp = got["components"][0]
        assert comp["surface_exports"] == ref["surface_exports"]


def test_full_bundled_attestation_matches_reference():
    """Full bundled set matches independent reference attestation."""
    _pipeline(BUNDLED)
    got = json.loads(EXPORT.read_text(encoding="utf-8"))
    for name in ("tuple_order.cwasm", "alias_basic.cwasm", "chain_surface.cwasm"):
        raw = (BUNDLED / name).read_bytes()
        ref = reference_attest_component(name, raw)
        comp = next(c for c in got["components"] if c["name"] == name)
        assert comp["imports"] == ref["imports"]
        assert comp["import_reorder_digest"] == ref["import_reorder_digest"]
        assert comp["surface_exports"] == ref["surface_exports"]


def test_resolve_surfaces_helper_matches_reference():
    """Reference surface resolver returns leaf for chain fixture."""
    raw = (BUNDLED / "chain_surface.cwasm").read_bytes()
    parsed = parse_cwrc(raw)
    surfaces = resolve_surfaces(parsed)
    assert surfaces[0]["outer"] == "surface"
    assert surfaces[0]["resolved_leaf"] == "leaf"


def test_type_index_helper_alias_lookup():
    """Reference alias lookup maps local 5 to module-type 99."""
    aliases = [{"local": 5, "module_type": 99}]
    assert resolve_type_index(5, aliases) == 99
    assert resolve_type_index(1, aliases) == 1


def test_import_digest_differs_from_raw_wire_hash():
    """Digest must not equal hashing raw wire bytes only."""
    import hashlib

    raw = (BUNDLED / "tuple_order.cwasm").read_bytes()
    wrong = hashlib.sha256(raw).hexdigest()
    ref = import_reorder_digest(parse_cwrc(raw)["imports"], parse_cwrc(raw)["aliases"])
    assert ref != wrong


def test_staging_ledger_binary_not_json():
    """Staging artifact is binary import-alias ledger."""
    _load(BUNDLED)
    data = LEDGER.read_bytes()
    assert not data.startswith(b"{")


def test_component_gov_cli_subcommands():
    """CLI exposes load and attest export subcommands."""
    proc = _run([GOV], check=False)
    assert proc.returncode == 2
    assert "load" in proc.stderr or "usage" in proc.stderr
