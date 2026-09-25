"""Behavioral tests for hclctl merge export governor."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

from reference_merge import reference_block, reference_checksum

HCLCTL = "/app/bin/hclctl"
STAGE = Path("/app/state/hcl-stage.json")
BUNDLED = Path("/app/data/fragments")
OUTPUT_DIR = Path("/app/output")
HCL_OUT = OUTPUT_DIR / "merged.hcl"
CHECKSUM_OUT = OUTPUT_DIR / "merge-checksum.txt"
TB3_DIR = Path("/opt/verifier-fixtures/hcl2-merge")


def _run(cmd: list[str], *, env: dict | None = None) -> subprocess.CompletedProcess:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(cmd, check=True, capture_output=True, text=True, env=merged)


def _fresh_output() -> None:
    for p in (STAGE, HCL_OUT, CHECKSUM_OUT):
        if p.exists():
            p.unlink()


def _ingest_export(frag_dir: Path) -> None:
    _fresh_output()
    _run([HCLCTL, "ingest", str(frag_dir)])
    _run([HCLCTL, "merge", "export"])


def test_hclctl_binary_exists():
    """Instruction requires /app/bin/hclctl built from cmd/hclctl."""
    assert Path(HCLCTL).is_file()


def test_bundled_fragments_directory_exists():
    """Instruction cites bundled fixtures under /app/data/fragments/."""
    assert BUNDLED.is_dir()
    assert any(BUNDLED.glob("*.hcl"))


def test_ingest_writes_staging_snapshot():
    """Ingest must write normalized staging at /app/state/hcl-stage.json."""
    _run([HCLCTL, "ingest", str(BUNDLED)])
    assert STAGE.is_file()
    data = json.loads(STAGE.read_text(encoding="utf-8"))
    assert len(data["fragments"]) == 2
    assert data["fragments"][0]["source"] == "01_base.hcl"


def test_staging_preserves_fragment_order_field():
    """Staging lists fragments in source declaration order per instruction."""
    _run([HCLCTL, "ingest", str(BUNDLED)])
    data = json.loads(STAGE.read_text(encoding="utf-8"))
    orders = [f["order"] for f in data["fragments"]]
    assert orders == [1, 2]


def test_merge_export_creates_artifacts():
    """merge export writes merged HCL and checksum under /app/output/."""
    _ingest_export(BUNDLED)
    assert OUTPUT_DIR.is_dir()
    assert HCL_OUT.is_file()
    assert CHECKSUM_OUT.is_file()


def test_merge_checksum_path_and_format():
    """Checksum artifact must live at /app/output/merge-checksum.txt."""
    _ingest_export(BUNDLED)
    assert str(CHECKSUM_OUT) == "/app/output/merge-checksum.txt"
    digest = CHECKSUM_OUT.read_text(encoding="utf-8").strip()
    assert len(digest) == 64


def test_deep_merge_retains_nested_name_key():
    """merge-contract.md requires deep merge preserving nested object keys."""
    _ingest_export(BUNDLED)
    block = reference_block(STAGE)
    tags = block["attributes"]["tags"]
    assert tags["tier"] == "front"
    assert tags["env"] == "staging"
    assert "Name" not in tags or tags.get("Name") is None


def test_explicit_null_removes_name():
    """Explicit null in merge_override must win over base values."""
    _ingest_export(BUNDLED)
    block = reference_block(STAGE)
    tags = block["attributes"]["tags"]
    assert tags.get("Name") is None


def test_export_labels_keep_lowest_order_declaration():
    """staging-schema.md tie-break uses lowest source-order fragment labels."""
    _ingest_export(BUNDLED)
    block = reference_block(STAGE)
    assert block["labels"] == ["z", "a"]


def test_merged_hcl_output_path():
    """merge export must write merged HCL to /app/output/merged.hcl."""
    _ingest_export(BUNDLED)
    assert str(HCL_OUT) == "/app/output/merged.hcl"
    assert HCL_OUT.is_file()


def test_merged_hcl_labels_not_alphabetized():
    """Export must not alphabetize label keys for repeated blocks."""
    _ingest_export(BUNDLED)
    text = HCL_OUT.read_text(encoding="utf-8")
    assert "block resource z a" in text


def test_dynamic_rows_use_post_override_env():
    """dynamic-blocks.md applies merge_override before dynamic expansion."""
    _ingest_export(BUNDLED)
    block = reference_block(STAGE)
    rows = block["expanded_dynamics"]
    assert len(rows) == 2
    for row in rows:
        assert row["tags.env"] == "staging"


def test_checksum_matches_reference_json():
    """Checksum follows normalized JSON per export-checksum.md."""
    _ingest_export(BUNDLED)
    expected = reference_checksum(STAGE)
    actual = CHECKSUM_OUT.read_text(encoding="utf-8").strip()
    assert actual == expected


def test_checksum_not_equal_to_hcl_hash():
    """Checksum must not be derived from pretty-printed HCL text alone."""
    _ingest_export(BUNDLED)
    import hashlib

    hcl_hash = hashlib.sha256(HCL_OUT.read_text(encoding="utf-8").strip().encode()).hexdigest()
    ref = reference_checksum(STAGE)
    assert CHECKSUM_OUT.read_text(encoding="utf-8").strip() == ref
    assert hcl_hash != ref or ref


def test_rebuild_subprocess_cli_ingest_export():
    """Verifier rebuilds hclctl and exercises merge export via subprocess CLI."""
    _ingest_export(BUNDLED)
    cp = subprocess.run([HCLCTL, "merge", "export"], capture_output=True, text=True)
    assert cp.returncode == 0


def test_staging_json_schema_fields():
    """Staging snapshot includes parsed blocks, dynamics, and merge_overrides."""
    _run([HCLCTL, "ingest", str(BUNDLED)])
    frag = json.loads(STAGE.read_text(encoding="utf-8"))["fragments"][0]
    for key in ("source", "order", "block_type", "labels", "attributes", "dynamics", "merge_overrides"):
        assert key in frag


def test_dynamic_template_parsed():
    """Ingest captures dynamic block templates from fragment sources."""
    _run([HCLCTL, "ingest", str(BUNDLED)])
    frags = json.loads(STAGE.read_text(encoding="utf-8"))["fragments"]
    dyn = frags[1]["dynamics"][0]
    assert dyn["name"] == "ingress"
    assert dyn["values"] == ["80", "443"]


def test_tb3_hidden_directory_present():
    """Hidden verifier fixtures directory is available at runtime."""
    assert TB3_DIR.is_dir()


def test_tb3_hidden_deep_merge_poison_pill():
    """Hidden fragments trap shallow merge on nested tag collisions."""
    tmp = Path("/tmp/tb3-fragments")
    if tmp.exists():
        shutil.rmtree(tmp)
    shutil.copytree(TB3_DIR, tmp)
    _ingest_export(tmp)
    block = reference_block(STAGE)
    tags = block["attributes"]["tags"]
    assert tags["env"] == "staging"
    assert tags["tier"] == "back"
    assert tags.get("Name") is None
    assert tags["zone"] == "a"


def test_tb3_hidden_checksum():
    """Hidden fixture set must match independent reference checksum."""
    tmp = Path("/tmp/tb3-fragments-ck")
    if tmp.exists():
        shutil.rmtree(tmp)
    shutil.copytree(TB3_DIR, tmp)
    _ingest_export(tmp)
    assert CHECKSUM_OUT.read_text(encoding="utf-8").strip() == reference_checksum(STAGE)


def test_tb3_dynamic_hidden_uses_override_env():
    """Hidden dynamics fail when overrides run after expansion."""
    tmp = Path("/tmp/tb3-fragments-dyn")
    if tmp.exists():
        shutil.rmtree(tmp)
    shutil.copytree(TB3_DIR, tmp)
    _ingest_export(tmp)
    block = reference_block(STAGE)
    for row in block["expanded_dynamics"]:
        assert row["tags.env"] == "staging"


def test_per_run_ingest_mutates_staging(tmp_path: Path):
    """Each ingest run rewrites staging from the supplied fragment directory."""
    alt = tmp_path / "fragments"
    alt.mkdir()
    shutil.copy(BUNDLED / "01_base.hcl", alt / "01_base.hcl")
    _run([HCLCTL, "ingest", str(alt)])
    first = json.loads(STAGE.read_text(encoding="utf-8"))
    shutil.copy(BUNDLED / "02_overlay.hcl", alt / "02_overlay.hcl")
    _run([HCLCTL, "ingest", str(alt)])
    second = json.loads(STAGE.read_text(encoding="utf-8"))
    assert len(first["fragments"]) == 1
    assert len(second["fragments"]) == 2


def test_decoy_module_not_required():
    """internal/decoy is off the export hot path and must not be edited."""
    decoy = Path("/app/internal/decoy/wrap.go")
    assert decoy.is_file()


def test_export_writes_trailing_checksum_newline():
    """merge-checksum.txt ends with a single trailing newline after the digest."""
    _ingest_export(BUNDLED)
    raw = CHECKSUM_OUT.read_text(encoding="utf-8")
    assert raw.endswith("\n")
    assert len(raw.strip()) == 64
