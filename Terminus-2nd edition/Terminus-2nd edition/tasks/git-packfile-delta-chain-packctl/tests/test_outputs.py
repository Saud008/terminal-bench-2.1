"""Behavioral tests for packctl pack delta-chain resolver."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from reference_pack import read_pack_object, reference_delta_only, reference_export, tb3_salt

PACKCTL = "/app/bin/packctl"
STAGE = Path("/app/state/pack-stage.json")
EXPORT = Path("/app/output/pack-object-export.json")
SHALLOW = Path("/app/data/packs/shallow")
TB3 = Path("/opt/verifier-fixtures/pack-bundles/deep4")


def _run(cmd: list[str], *, env: dict | None = None, check: bool = True) -> subprocess.CompletedProcess:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(cmd, check=check, capture_output=True, text=True, env=merged)


def _fresh() -> None:
    for p in (STAGE, EXPORT):
        if p.exists():
            p.unlink()


def _ingest(pack_dir: Path) -> None:
    _run([PACKCTL, "ingest", str(pack_dir)])


def _export() -> None:
    _run([PACKCTL, "resolve", "export"])


def _pipeline(pack_dir: Path) -> None:
    _fresh()
    _ingest(pack_dir)
    _export()


@pytest.fixture(autouse=True)
def clean_state():
    _fresh()
    yield
    _fresh()


def test_packctl_binary_exists():
    """Instruction requires /app/bin/packctl built from workspace."""
    assert Path(PACKCTL).is_file()


def test_shallow_pack_bundle_exists():
    """Instruction cites bundled fixtures under /app/data/packs/shallow/."""
    assert SHALLOW.is_dir()
    assert (SHALLOW / "catalog.json").is_file()
    assert (SHALLOW / "pack.stream").is_file()


def test_ingest_writes_staging_snapshot():
    """Ingest must write normalized staging at /app/state/pack-stage.json."""
    _ingest(SHALLOW)
    assert STAGE.is_file()
    data = json.loads(STAGE.read_text(encoding="utf-8"))
    assert data["pack_id"] == "shallow"
    assert len(data["objects"]) == 2


def test_staging_preserves_catalog_order():
    """Staging lists objects in catalog order per instruction."""
    _ingest(SHALLOW)
    data = json.loads(STAGE.read_text(encoding="utf-8"))
    kinds = [o["kind"] for o in data["objects"]]
    assert kinds == ["blob", "ref_delta"]


def test_ingest_seq_monotonic():
    """Ingest increments ingest_seq on each ingest call."""
    _ingest(SHALLOW)
    first = json.loads(STAGE.read_text(encoding="utf-8"))["ingest_seq"]
    _ingest(SHALLOW)
    second = json.loads(STAGE.read_text(encoding="utf-8"))["ingest_seq"]
    assert second == first + 1


def test_resolve_export_creates_output():
    """resolve export writes /app/output/pack-object-export.json."""
    _pipeline(SHALLOW)
    assert EXPORT.is_file()


def test_shallow_blob_inflated_size():
    """Blob inflated_size must match independent reference."""
    _pipeline(SHALLOW)
    got = json.loads(EXPORT.read_text(encoding="utf-8"))
    ref = reference_export(STAGE)
    blob = next(o for o in got["objects"] if o["kind"] == "blob")
    ref_blob = next(o for o in ref["objects"] if o["kind"] == "blob")
    assert blob["inflated_size"] == ref_blob["inflated_size"] == 11


def test_shallow_delta_chain_depth():
    """delta-chain-ordering.md chain_depth for shallow ref_delta."""
    _pipeline(SHALLOW)
    got = json.loads(EXPORT.read_text(encoding="utf-8"))
    ref = reference_export(STAGE)
    delta = next(o for o in got["objects"] if o["kind"] == "ref_delta")
    ref_delta = next(o for o in ref["objects"] if o["kind"] == "ref_delta")
    assert delta["chain_depth"] == ref_delta["chain_depth"] == 1


def test_shallow_delta_sha1_matches_reference():
    """Exported sha1 must match SHA-1 of inflated bytes."""
    _pipeline(SHALLOW)
    got = json.loads(EXPORT.read_text(encoding="utf-8"))
    ref = reference_export(STAGE)
    delta = next(o for o in got["objects"] if o["kind"] == "ref_delta")
    ref_delta = next(o for o in ref["objects"] if o["kind"] == "ref_delta")
    assert delta["sha1"] == ref_delta["sha1"]


def test_total_inflated_bytes_rollup():
    """export-size-rollup.md sums final inflated sizes only."""
    _pipeline(SHALLOW)
    got = json.loads(EXPORT.read_text(encoding="utf-8"))
    ref = reference_export(STAGE)
    assert got["total_inflated_bytes"] == ref["total_inflated_bytes"] == 23


def test_export_path_contract():
    """Instruction output path /app/output/pack-object-export.json."""
    _pipeline(SHALLOW)
    assert str(EXPORT) == "/app/output/pack-object-export.json"


def test_staging_path_contract():
    """Instruction staging path /app/state/pack-stage.json."""
    _ingest(SHALLOW)
    assert STAGE == Path("/app/state/pack-stage.json")


def test_objects_sorted_by_id():
    """pack-export-schema.md requires objects sorted by id."""
    _pipeline(SHALLOW)
    got = json.loads(EXPORT.read_text(encoding="utf-8"))
    ids = [o["id"] for o in got["objects"]]
    assert ids == sorted(ids)


def test_reference_subprocess_full_export():
    """Independent reference agrees after subprocess ingest and export."""
    _pipeline(SHALLOW)
    got = json.loads(EXPORT.read_text(encoding="utf-8"))
    ref = reference_export(STAGE)
    assert got == ref


def test_independent_delta_applicator():
    """Independent delta applicator matches export inflated_size."""
    _ingest(SHALLOW)
    stage = json.loads(STAGE.read_text(encoding="utf-8"))
    stream = Path(stage["pack_stream_path"]).read_bytes()
    base_obj = next(o for o in stage["objects"] if o["kind"] == "blob")
    delta_obj = next(o for o in stage["objects"] if o["kind"] == "ref_delta")
    _, base_inflated = read_pack_object(stream, int(base_obj["pack_offset"]))
    got = reference_delta_only(stream, int(delta_obj["pack_offset"]), base_inflated)
    ref_export = reference_export(STAGE)
    ref_delta = next(o for o in ref_export["objects"] if o["kind"] == "ref_delta")
    assert len(got) == ref_delta["inflated_size"]


def test_pack_stream_path_in_staging():
    """Staging records absolute pack.stream path for resolve."""
    _ingest(SHALLOW)
    data = json.loads(STAGE.read_text(encoding="utf-8"))
    assert data["pack_stream_path"].endswith("pack.stream")


def test_export_schema_fields_present():
    """pack-export-schema.md fields present on every object row."""
    _pipeline(SHALLOW)
    got = json.loads(EXPORT.read_text(encoding="utf-8"))
    assert "pack_id" in got and "objects" in got and "total_inflated_bytes" in got
    for obj in got["objects"]:
        assert {"id", "kind", "inflated_size", "sha1", "chain_depth"} <= set(obj)


def _tb3_pack_dir() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="tb3-pack-"))
    shutil.copytree(TB3, tmp, dirs_exist_ok=True)
    return tmp


def test_tb3_four_deep_chain_resolves():
    """Hidden deep4 pack resolves four-hop ref_delta chain."""
    pack_dir = _tb3_pack_dir()
    try:
        _pipeline(pack_dir)
        got = json.loads(EXPORT.read_text(encoding="utf-8"))
        ref = reference_export(STAGE)
        assert got["total_inflated_bytes"] == ref["total_inflated_bytes"]
        depths = sorted(o["chain_depth"] for o in got["objects"] if o["kind"] == "ref_delta")
        assert depths == [1, 2, 3]
    finally:
        shutil.rmtree(pack_dir, ignore_errors=True)


def test_tb3_wrong_kind_ref_skipped():
    """ref-delta-kind-gate.md skips ref_delta with commit base."""
    pack_dir = _tb3_pack_dir()
    trap_id = "be59a5319ecb998279f10dee771d8e97cab1638b"
    try:
        _pipeline(pack_dir)
        got = json.loads(EXPORT.read_text(encoding="utf-8"))
        ref = reference_export(STAGE)
        assert trap_id not in {o["id"] for o in got["objects"]}
        assert got["objects"] == ref["objects"]
    finally:
        shutil.rmtree(pack_dir, ignore_errors=True)


def test_tb3_object_id_salt_mutation():
    """TB3_OBJECT_ID_SALT mutates exported ids without changing sha1."""
    pack_dir = _tb3_pack_dir()
    try:
        _fresh()
        _ingest(pack_dir)
        _run([PACKCTL, "resolve", "export"], env={"TB3_OBJECT_ID_SALT": "x9"})
        got = json.loads(EXPORT.read_text(encoding="utf-8"))
        ref = reference_export(STAGE, id_salt="x9")
        assert got["objects"] == ref["objects"]
        assert all(o["id"].endswith("x9") for o in got["objects"])
    finally:
        shutil.rmtree(pack_dir, ignore_errors=True)


def test_tb3_hidden_checksum_style_sha1():
    """Deepest hidden chain tip sha1 and inflated_size match reference."""
    pack_dir = _tb3_pack_dir()
    try:
        _pipeline(pack_dir)
        got = json.loads(EXPORT.read_text(encoding="utf-8"))
        ref = reference_export(STAGE)
        tip = max(got["objects"], key=lambda o: o["chain_depth"])
        ref_tip = max(ref["objects"], key=lambda o: o["chain_depth"])
        assert tip["sha1"] == ref_tip["sha1"]
        assert tip["inflated_size"] == ref_tip["inflated_size"]
    finally:
        shutil.rmtree(pack_dir, ignore_errors=True)


def test_tb3_commit_object_exported():
    """Non-delta commit objects export with chain_depth zero."""
    pack_dir = _tb3_pack_dir()
    try:
        _pipeline(pack_dir)
        got = json.loads(EXPORT.read_text(encoding="utf-8"))
        assert any(o["kind"] == "commit" for o in got["objects"])
    finally:
        shutil.rmtree(pack_dir, ignore_errors=True)


def test_tb3_salt_env_helper():
    """tb3_salt reads TB3_OBJECT_ID_SALT from environment."""
    os.environ["TB3_OBJECT_ID_SALT"] = "z"
    assert tb3_salt() == "z"
    del os.environ["TB3_OBJECT_ID_SALT"]
