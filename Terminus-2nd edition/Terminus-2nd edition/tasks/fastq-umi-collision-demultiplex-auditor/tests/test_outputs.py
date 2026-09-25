"""Behavioral tests for lumidmx FASTQ UMI collision demultiplex auditor."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from reference_demux import (
    canonical_r1,
    canonical_r2,
    load_json,
    pair_canonical,
    reference_atlas,
    reference_clusters,
    reference_contamination,
    reference_demux,
    reference_digest_paths,
    resolve_effective_samples,
    reverse_complement,
    rotate_left,
)

LUMIDMX = "/app/bin/lumidmx"
STAGING = Path("/app/state/lane-read-staging.json")
LEDGER = Path("/app/state/umi-demux-ledger.json")
ATLAS = Path("/app/output/umi-collision-atlas.json")
DIGEST = Path("/app/output/atlas-digest.txt")
READS = Path("/app/data/reads")
MANIFEST = Path("/app/data/manifest.json")
LANES = Path("/app/data/lanes.json")
TB3_READS = Path("/opt/verifier-fixtures/lumidmx/tb3-reads")
TB3_MANIFEST = Path("/opt/verifier-fixtures/lumidmx/tb3-manifest.json")
TB3_LANES = Path("/opt/verifier-fixtures/lumidmx/tb3-lanes.json")


def _run(cmd: list[str], *, env: dict | None = None, check: bool = True) -> subprocess.CompletedProcess:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(cmd, check=check, capture_output=True, text=True, env=merged)


def _fresh() -> None:
    for p in (STAGING, LEDGER, ATLAS, DIGEST):
        if p.exists():
            p.unlink()


def _ingest(reads_dir: Path, manifest: Path, lanes: Path) -> None:
    _run(
        [
            LUMIDMX,
            "stage",
            "ingest",
            "--reads-dir",
            str(reads_dir),
            "--manifest",
            str(manifest),
            "--lanes",
            str(lanes),
        ]
    )


def _demux(*, env: dict | None = None) -> None:
    _run([LUMIDMX, "demux", "run"], env=env)


def _export() -> None:
    _run([LUMIDMX, "atlas", "export"])


def _pipeline(reads_dir: Path, manifest: Path, lanes: Path, *, env: dict | None = None) -> None:
    _fresh()
    _ingest(reads_dir, manifest, lanes)
    _demux(env=env)
    _export()


@pytest.fixture(autouse=True)
def clean_state():
    _fresh()
    yield
    _fresh()


def test_lumidmx_binary_exists():
    """Instruction requires /app/bin/lumidmx built from workspace."""
    assert Path(LUMIDMX).is_file()


def test_bundled_data_paths():
    """Instruction cites bundled reads, manifest, and lanes."""
    assert READS.is_dir()
    assert MANIFEST.is_file()
    assert LANES.is_file()
    assert (READS / "L1" / "p001_R1.fastq").is_file()


def test_stage_ingest_writes_staging():
    """Stage ingest writes /app/state/lane-read-staging.json."""
    _ingest(READS, MANIFEST, LANES)
    assert STAGING.is_file()
    data = load_json(STAGING)
    assert data["precedence_order"] == "lane_first"
    assert len(data["pairs"]) >= 4


def test_stage_ingest_increments_seq():
    """Repeated ingest bumps ingest_seq."""
    _ingest(READS, MANIFEST, LANES)
    first = load_json(STAGING)["ingest_seq"]
    _ingest(READS, MANIFEST, LANES)
    second = load_json(STAGING)["ingest_seq"]
    assert second == first + 1


def test_paired_read_sync_excludes_orphan_r1():
    """paired-read-sync.md excludes mates missing R2."""
    _ingest(READS, MANIFEST, LANES)
    pairs = load_json(STAGING)["pairs"]
    ids = {p["pair_id"] for p in pairs}
    assert "p003" not in ids
    assert "p001" in ids


def test_lane_precedence_required_for_p001():
    """lane_first override ACCT required when global ACGT fails budget 0."""
    _ingest(READS, MANIFEST, LANES)
    _demux()
    ledger = load_json(LEDGER)
    p001 = next(e for e in ledger["entries"] if e["pair_id"] == "p001")
    assert p001["sample_id"] == "alpha"


def test_demux_run_writes_ledger():
    """demux run writes /app/state/umi-demux-ledger.json."""
    _ingest(READS, MANIFEST, LANES)
    _demux()
    assert LEDGER.is_file()
    ledger = load_json(LEDGER)
    assert ledger["entries"]


def test_barcode_n_ignored_matches_alpha():
    """barcode-mismatch-budget.md ignores N when matching ANGT to ACCT."""
    _ingest(READS, MANIFEST, LANES)
    _demux()
    ledger = load_json(LEDGER)
    p005 = next(e for e in ledger["entries"] if e["pair_id"] == "p005")
    assert p005["sample_id"] == "alpha"


def test_umi_r2_reverse_complement_and_rotate():
    """umi-canonicalization.md RC then rotate for R2."""
    shift = 2
    r2 = canonical_r2("TTTTCCCC", shift)
    assert r2 == rotate_left(reverse_complement("TTTTCCCC"), shift)
    assert r2 == "GGAAAAGG"


def test_ledger_r2_canonical_matches_reference():
    """Ledger stores RC-then-rotate R2 canonical mate UMIs."""
    _ingest(READS, MANIFEST, LANES)
    _demux()
    staging = load_json(STAGING)
    ledger = load_json(LEDGER)
    ref = reference_demux(staging)
    for got, exp in zip(ledger["entries"], ref["entries"]):
        assert got["r2_canonical"] == exp["r2_canonical"]


def test_pair_canonical_lex_min():
    """Pair canonical_umi is lex min of mate canonical strings."""
    r1 = canonical_r1("AAAABBBB", 2)
    r2 = canonical_r2("CCCCGGGG", 2)
    assert pair_canonical(r1, r2) == min(r1, r2)


def test_demux_entries_match_reference():
    """Bundled pipeline entries agree with independent reference demux."""
    _ingest(READS, MANIFEST, LANES)
    _demux()
    staging = load_json(STAGING)
    ledger = load_json(LEDGER)
    ref = reference_demux(staging)
    assert ledger["entries"] == ref["entries"]


def test_collision_cluster_id_lex_min_canonical():
    """cluster_id is lex min canonical_umi among cluster pair_ids."""
    _ingest(READS, MANIFEST, LANES)
    _demux()
    ledger = load_json(LEDGER)
    alpha_cluster = next(c for c in ledger["clusters"] if c["sample_id"] == "alpha")
    assert alpha_cluster["cluster_id"] == "AABBBBAA"
    assert set(alpha_cluster["pair_ids"]) >= {"p001", "p002", "p005"}


def test_clusters_match_reference():
    """Ledger clusters agree with reference collision builder."""
    _ingest(READS, MANIFEST, LANES)
    _demux()
    ledger = load_json(LEDGER)
    ref = reference_clusters(ledger["entries"])
    assert ledger["clusters"] == ref


def test_atlas_export_paths():
    """Instruction output paths are honored."""
    _pipeline(READS, MANIFEST, LANES)
    assert ATLAS.is_file()
    assert DIGEST.is_file()
    assert str(ATLAS) == "/app/output/umi-collision-atlas.json"
    assert str(DIGEST) == "/app/output/atlas-digest.txt"


def test_atlas_matches_reference():
    """Atlas body agrees with independent reference export."""
    _pipeline(READS, MANIFEST, LANES)
    staging = load_json(STAGING)
    ledger = load_json(LEDGER)
    got = load_json(ATLAS)
    ref = reference_atlas(staging, ledger)
    assert got == ref


def test_digest_matches_reference():
    """atlas-export-ledger.md digest matches independent SHA-256."""
    _pipeline(READS, MANIFEST, LANES)
    digest = DIGEST.read_text(encoding="utf-8").strip()
    assert digest == reference_digest_paths(STAGING, LEDGER)
    assert len(digest) == 64


def test_subprocess_cli_roundtrip():
    """Subprocess ingest demux export agrees with reference atlas."""
    _pipeline(READS, MANIFEST, LANES)
    staging = load_json(STAGING)
    ledger = load_json(LEDGER)
    got = load_json(ATLAS)
    ref = reference_atlas(staging, ledger)
    assert got == ref


def test_beta_lane_l2_demux():
    """L2 beta sample demux uses global barcodes with zero seed shift."""
    _ingest(READS, MANIFEST, LANES)
    _demux()
    ledger = load_json(LEDGER)
    p101 = next(e for e in ledger["entries"] if e["pair_id"] == "p101")
    assert p101["sample_id"] == "beta"
    assert p101["canonical_umi"] == "AAAATTTT"


def test_contamination_flags_empty_bundled():
    """Bundled atlas has no cross_sample flags."""
    _pipeline(READS, MANIFEST, LANES)
    atlas = load_json(ATLAS)
    assert atlas["contamination_flags"] == []


def _tb3_reads_dir() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="tb3-reads-"))
    shutil.copytree(TB3_READS, tmp, dirs_exist_ok=True)
    return tmp


def test_tb3_hidden_lane_precedence_random_samples():
    """Hidden L9 lane overrides apply to zxq47 and mkt91 sample ids."""
    reads = _tb3_reads_dir()
    try:
        _pipeline(reads, TB3_MANIFEST, TB3_LANES)
        staging = load_json(STAGING)
        effective = resolve_effective_samples(staging, "L9")
        ids = {row["sample_id"] for row in effective}
        assert ids == {"zxq47", "mkt91"}
        ledger = load_json(LEDGER)
        assert {e["sample_id"] for e in ledger["entries"]} == {"zxq47", "mkt91"}
    finally:
        shutil.rmtree(reads, ignore_errors=True)


def test_tb3_cross_sample_contamination_flag():
    """Hidden fixtures produce export-only cross_sample contamination."""
    reads = _tb3_reads_dir()
    try:
        _pipeline(reads, TB3_MANIFEST, TB3_LANES)
        ledger = load_json(LEDGER)
        flags = load_json(ATLAS)["contamination_flags"]
        ref_flags = reference_contamination(ledger["entries"])
        assert flags == ref_flags
        assert flags and flags[0]["flag"] == "cross_sample"
        assert len(flags[0]["sample_ids"]) == 2
    finally:
        shutil.rmtree(reads, ignore_errors=True)


def test_tb3_umi_seed_shift_env():
    """TB3_UMI_SEED_SHIFT offsets lane seed_shift for hidden reads."""
    reads = _tb3_reads_dir()
    try:
        _fresh()
        _ingest(reads, TB3_MANIFEST, TB3_LANES)
        _demux(env={"TB3_UMI_SEED_SHIFT": "3"})
        staging = load_json(STAGING)
        ledger = load_json(LEDGER)
        os.environ["TB3_UMI_SEED_SHIFT"] = "3"
        ref = reference_demux(staging)
        del os.environ["TB3_UMI_SEED_SHIFT"]
        assert ledger["entries"] == ref["entries"]
    finally:
        shutil.rmtree(reads, ignore_errors=True)
        os.environ.pop("TB3_UMI_SEED_SHIFT", None)


def test_tb3_hidden_digest():
    """Hidden fixture atlas digest matches reference ledger."""
    reads = _tb3_reads_dir()
    try:
        _pipeline(reads, TB3_MANIFEST, TB3_LANES)
        digest = DIGEST.read_text(encoding="utf-8").strip()
        assert digest == reference_digest_paths(STAGING, LEDGER)
    finally:
        shutil.rmtree(reads, ignore_errors=True)


def test_instruction_docs_referenced_paths():
    """Instruction /app/docs contracts exist on disk."""
    docs = Path("/app/docs")
    for name in (
        "paired-read-sync.md",
        "barcode-mismatch-budget.md",
        "umi-canonicalization.md",
        "lane-manifest-precedence.md",
        "atlas-export-ledger.md",
    ):
        assert (docs / name).is_file()


def test_staging_state_path_contract():
    """Staging path /app/state/lane-read-staging.json is honored."""
    _ingest(READS, MANIFEST, LANES)
    assert STAGING == Path("/app/state/lane-read-staging.json")


def test_lanes_json_loaded_into_staging():
    """Ingest reads /app/data/lanes.json lane configs into staging snapshot."""
    lanes_doc = load_json(LANES)
    _ingest(READS, MANIFEST, LANES)
    staging = load_json(STAGING)
    assert staging["lanes"] == lanes_doc["lanes"]
    assert staging["precedence_order"] == lanes_doc["precedence_order"]


def test_lane_read_staging_snapshot_fields():
    """lane-read-staging.json records manifest samples and synced pair rows."""
    _ingest(READS, MANIFEST, LANES)
    staging = load_json(STAGING)
    manifest = load_json(MANIFEST)
    assert staging["samples_global"] == manifest["samples"]
    assert staging["mismatch_budget"] == manifest["mismatch_budget"]
    assert all("pair_id" in row and "r1_umi" in row for row in staging["pairs"])
