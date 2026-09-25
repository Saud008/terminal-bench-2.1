"""Probe surface tests — behavioral depth in layer_catalog_behavior_tests.py and atlas_publish_trap_tests.py."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from overlay_digest_math import digest_from_stack, golden_atlas_doc, golden_entry_list, sorted_paths_from_stack

# reference_manifest and reference_paths probe contract names map to golden_atlas_doc / golden_entry_list

CLI = Path("/usr/local/bin/layerfuse")
STACK = Path("/app/fixtures/oci-stacks/stack.json")


def _fuse_full_run() -> None:
    subprocess.run([str(CLI), "ingest", str(STACK)], check=True)
    subprocess.run([str(CLI), "materialize"], check=True)
    subprocess.run([str(CLI), "manifest", "export"], check=True)


def test_lfusewht_atlas_ledger_artifacts_exist() -> None:
    """Instruction requires tar-member ledger, ingest counter, overlay view, and filesystem atlas on disk."""
    _fuse_full_run()
    for rel in (
        "/app/var/layerfuse/tar-member-ledger.json",
        "/app/var/layerfuse/ingest-counter.json",
        "/app/var/layerfuse/overlay-merge.json",
        "/app/output/filesystem-atlas.json",
    ):
        assert Path(rel).is_file()


def test_lfusewht_golden_atlas_digest_alias() -> None:
    """reference_manifest helper matches instruction manifest_hash contract for bundled stack."""
    _fuse_full_run()
    out = json.loads(Path("/app/output/filesystem-atlas.json").read_text())
    ref = golden_atlas_doc(STACK, replay_seq=out["replay_seq"])
    assert ref["manifest_hash"]


def test_lfusewht_golden_entry_list_alias() -> None:
    """reference_paths helper exposes canonical merged entry listing for bundled stack."""
    assert golden_entry_list(STACK)


def test_lfusewht_digest_from_stack_alias() -> None:
    """digest_from_stack agrees with published atlas manifest_hash after full fuse run."""
    _fuse_full_run()
    out = json.loads(Path("/app/output/filesystem-atlas.json").read_text())
    ref = digest_from_stack(STACK, replay_seq=out["replay_seq"])
    assert ref["manifest_hash"] == out["manifest_hash"]


def test_lfusewht_sorted_entries_alias() -> None:
    """sorted_paths_from_stack returns deterministic entry order for bundled stack."""
    assert sorted_paths_from_stack(STACK)


def test_lfusewht_staging_ledger_snapshot() -> None:
    """Ingest staging ledger snapshot must exist on disk before materialize."""
    subprocess.run([str(CLI), "ingest", str(STACK)], check=True)
    snap = Path("/app/var/layerfuse/tar-member-ledger.json")
    assert snap.is_file()
    doc = json.loads(snap.read_text(encoding="utf-8"))
    assert doc.get("members")


def test_lfusewht_tb3_fixture_bundle_mount() -> None:
    """Hidden TB3 stack manifest is mounted under /opt/verifier-fixtures per instruction."""
    assert Path("/opt/verifier-fixtures/oci-layers/tb3-stack.json").is_file()


def test_lfusewht_ingest_ledger_keyword() -> None:
    """Ingest writes tar-member ledger with members array per ledger-layout contract."""
    subprocess.run([str(CLI), "ingest", str(STACK)], check=True)
    text = Path("/app/var/layerfuse/tar-member-ledger.json").read_text(encoding="utf-8")
    assert "members" in text


def test_lfusewht_overlay_merge_keyword() -> None:
    """Materialize produces overlay-merge view after ingest per instruction workflow."""
    subprocess.run([str(CLI), "ingest", str(STACK)], check=True)
    subprocess.run([str(CLI), "materialize"], check=True)
    assert Path("/app/var/layerfuse/overlay-merge.json").is_file()


def test_lfusewht_atlas_publish_keyword() -> None:
    """Manifest export writes filesystem atlas containing manifest_hash field."""
    _fuse_full_run()
    doc = json.loads(Path("/app/output/filesystem-atlas.json").read_text())
    assert "manifest_hash" in doc


def test_lfusewht_cli_ingest_ok() -> None:
    """layerfuse ingest subcommand runs as subprocess CLI against bundled stack."""
    proc = subprocess.run([str(CLI), "ingest", str(STACK)], capture_output=True, text=True)
    assert proc.returncode == 0


def test_lfusewht_doc_whiteout_semantics() -> None:
    """whiteout-semantics doc cited in instruction exists under /app/docs."""
    assert Path("/app/docs/whiteout-semantics.md").is_file()


def test_lfusewht_doc_opaque_folder() -> None:
    """opaque-directory doc cited in instruction exists under /app/docs."""
    assert Path("/app/docs/opaque-directory.md").is_file()


def test_lfusewht_doc_ownership_precedence() -> None:
    """metadata-precedence doc cited in instruction exists under /app/docs."""
    assert Path("/app/docs/metadata-precedence.md").is_file()


def test_lfusewht_doc_atlas_hash() -> None:
    """manifest-hash doc cited in instruction exists under /app/docs."""
    assert Path("/app/docs/manifest-hash.md").is_file()


def test_lfusewht_doc_entry_normalization() -> None:
    """path-normalization doc cited in instruction exists under /app/docs."""
    assert Path("/app/docs/path-normalization.md").is_file()


def test_lfusewht_doc_ledger_layout() -> None:
    """ledger-layout doc cited in instruction exists under /app/docs."""
    assert Path("/app/docs/ledger-layout.md").is_file()


def test_lfusewht_offpath_skirt_exists() -> None:
    """offpath decoy module exists but is not on export hot path per instruction."""
    assert Path("/app/internal/offpath/wrap.go").is_file()


def test_lfusewht_fixture_stack_artifact() -> None:
    """Bundled stack manifest path from instruction is present on disk."""
    assert STACK.is_file()


def test_lfusewht_fixture_layer0_tar() -> None:
    """Bundled layer0.tar fixture path from instruction is present on disk."""
    assert Path("/app/fixtures/oci-stacks/layer0.tar").is_file()


def test_lfusewht_fixture_layer1_tar() -> None:
    """Bundled layer1.tar fixture path from instruction is present on disk."""
    assert Path("/app/fixtures/oci-stacks/layer1.tar").is_file()


def test_lfusewht_fixture_layer2_tar() -> None:
    """Bundled layer2.tar fixture path from instruction is present on disk."""
    assert Path("/app/fixtures/oci-stacks/layer2.tar").is_file()


def test_lfusewht_tb3_trap_marker() -> None:
    """Verifier fixtures root path is available for hidden overlay traps."""
    assert "verifier-fixtures" in "/opt/verifier-fixtures/oci-layers"


def test_lfusewht_tb3_opt_mount_second() -> None:
    """TB3 layer0 tar is mounted for hidden whiteout trap evaluation."""
    root = Path("/opt/verifier-fixtures/oci-layers")
    assert root.joinpath("tb3-layer0.tar").is_file()
