"""Verifier contract for chunkline S5 dataset lineage profiler.

Independent reference math mirrors /app/docs contracts. Every test invokes the
chunkline CLI via subprocess.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import subprocess
from pathlib import Path

CHUNKLINE = "s5lineage"
BASIC_BUNDLE = Path("/app/fixtures/basic")
TB3_BUNDLE = Path("/opt/verifier-fixtures/tb3_shadow")
STATE = Path("/app/state")
OUT = Path("/app/output/lineage_report.json")

subprocess.run(
    ["cargo", "build", "--release", "--locked"],
    cwd="/app",
    check=True,
)


def run_chunkline(args: list[str], env: dict | None = None) -> subprocess.CompletedProcess:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        [CHUNKLINE, *args],
        check=True,
        capture_output=True,
        text=True,
        env=merged,
    )


def reset_state() -> None:
    if STATE.exists():
        shutil.rmtree(STATE)
    STATE.mkdir(parents=True, exist_ok=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if OUT.exists():
        OUT.unlink()


def ingest(env: dict | None = None) -> None:
    run_chunkline(
        ["ingest", "--catalog", "/app/fixtures/basic", "--state", "/app/state"],
        env=env,
    )


def export(env: dict | None = None) -> bytes:
    run_chunkline(
        ["export", "--state", "/app/state", "--out", "/app/output/lineage_report.json"],
        env=env,
    )
    return OUT.read_bytes()


def load_staging() -> dict:
    return json.loads((STATE / "staging.json").read_text(encoding="utf-8"))


def load_report() -> dict:
    return json.loads(OUT.read_text(encoding="utf-8"))


def reference_chunks_per_dim(dims: list[int], chunk_dims: list[int]) -> list[int]:
    return [math.ceil(d / c) for d, c in zip(dims, chunk_dims)]


def reference_linear_origin(linear: int, dims: list[int], chunk_dims: list[int]) -> list[int]:
    counts = reference_chunks_per_dim(dims, chunk_dims)
    rem = linear
    coords = [0] * len(counts)
    for axis in range(len(counts) - 1, -1, -1):
        stride = counts[axis]
        coords[axis] = rem % stride
        rem //= stride
    return [c * cd for c, cd in zip(coords, chunk_dims)]


def reference_effective_attrs(catalog: dict, dataset_path: str) -> dict:
    ds = next(d for d in catalog["datasets"] if d["path"] == dataset_path)
    merged: dict = {}
    for parent in ds.get("parent_chain", []):
        for k, v in parent["attrs"].items():
            merged.setdefault(k, v)
    merged.update(ds["attrs"])
    return merged


def reference_filter_chain_hash(filters: list[str]) -> str:
    return hashlib.sha256("|".join(filters).encode()).hexdigest()


def reference_mask_count(mask_path: Path, cells: int) -> int:
    data = mask_path.read_bytes()
    total = 0
    for i in range(cells):
        byte = data[i // 8] if i // 8 < len(data) else 0
        if (byte >> (i % 8)) & 1:
            total += 1
    return total


def test_s5prof_ingest_writes_staging_snapshot() -> None:
    """Ingest must materialize /app/state/staging.json per report-contract.md."""
    reset_state()
    ingest()
    snap = load_staging()
    assert snap["version"] == 1
    assert snap["catalog_root"] == "/"
    assert len(snap["chunks"]) == 2


def test_s5prof_staging_json_path_exists_after_ingest() -> None:
    """Instruction cites /app/state/staging.json as the staging artifact path."""
    reset_state()
    ingest()
    staging_file = STATE / "staging.json"
    assert staging_file.is_file()
    assert staging_file.read_text(encoding="utf-8").strip()


def test_s5prof_sequence_txt_persisted_under_state() -> None:
    """Ingest must persist monotonic counter at /app/state/sequence.txt."""
    reset_state()
    ingest()
    seq_file = STATE / "sequence.txt"
    assert seq_file.is_file()
    assert seq_file.read_text(encoding="utf-8").strip() == "1"


def test_s5prof_export_writes_lineage_report() -> None:
    """Export must write /app/output/lineage_report.json."""
    reset_state()
    ingest()
    export()
    report = load_report()
    assert report["version"] == 1
    assert "/obs/temp" in report["datasets"]


def test_s5prof_chunk_origins_match_index_sidecar() -> None:
    """Chunk origins must match catalog index sidecar bytes."""
    reset_state()
    ingest()
    snap = load_staging()
    origins = [c["origin"] for c in snap["chunks"]]
    assert origins == [[0, 0], [2, 0]]


def test_s5prof_row_major_coordinate_consistency_flags() -> None:
    """coord_consistent follows row-major traversal from index-walk.md."""
    reset_state()
    ingest()
    snap = load_staging()
    assert all(c["coord_consistent"] for c in snap["chunks"])


def test_s5prof_effective_attrs_child_overrides_parent_units() -> None:
    """Dataset attrs override parent_chain per attr-chain.md (units key)."""
    reset_state()
    ingest()
    snap = load_staging()
    attrs = snap["chunks"][0]["effective_attrs"]
    assert attrs["units"] == "K"
    assert attrs["calibration"] == "lab"
    assert attrs["scale"] == 0.5


def test_s5prof_filter_chain_hash_preserves_catalog_order() -> None:
    """filter_chain_hash must not sort filters (filter-chain.md)."""
    reset_state()
    ingest()
    snap = load_staging()
    expected = reference_filter_chain_hash(["shuffle", "gzip"])
    assert snap["chunks"][0]["filter_chain_hash"] == expected
    assert snap["chunks"][0]["filter_chain_hash"] != reference_filter_chain_hash(
        sorted(["shuffle", "gzip"])
    )


def test_s5prof_mask_accounting_counts_set_bits_only() -> None:
    """masked_cells counts mask bits only (bit-tally.md)."""
    reset_state()
    ingest()
    snap = load_staging()
    cells = 2 * 3
    expected = reference_mask_count(BASIC_BUNDLE / "masks/temp.mask", cells)
    assert snap["chunks"][0]["masked_cells"] == expected
    assert expected == 1


def test_s5prof_coord_labels_apply_scale_attribute() -> None:
    """coord_labels multiply origin by effective scale (origin-labels.md)."""
    reset_state()
    ingest()
    snap = load_staging()
    labels = snap["chunks"][1]["coord_labels"]
    assert labels == [1.0, 0.0]


def test_s5prof_compression_totals_aggregate_payload_and_masks() -> None:
    """compression_totals sums payload bytes and masked cells across chunks."""
    reset_state()
    ingest()
    snap = load_staging()
    totals = snap["compression_totals"]
    assert totals["total_payload_bytes"] == 220
    assert totals["total_masked_cells"] == 2
    assert totals["filter_usage"]["shuffle"] == 2
    assert totals["filter_usage"]["gzip"] == 2


def test_s5prof_export_sorts_chunks_by_index() -> None:
    """Export sorts chunks ascending by chunk_index (report-contract.md)."""
    reset_state()
    ingest()
    export()
    report = load_report()
    idxs = [c["chunk_index"] for c in report["datasets"]["/obs/temp"]["chunks"]]
    assert idxs == sorted(idxs)


def test_s5prof_export_is_byte_stable_across_runs() -> None:
    """Repeated export with unchanged staging yields identical bytes."""
    reset_state()
    ingest()
    first = export()
    second = export()
    assert first == second


def test_s5prof_sequence_counter_increments_on_reingest() -> None:
    """sequence.txt increments on every ingest invocation."""
    reset_state()
    ingest()
    seq1 = load_staging()["sequence"]
    ingest()
    seq2 = load_staging()["sequence"]
    assert seq1 == 1
    assert seq2 == 2


def test_s5prof_export_fingerprint_hashes_datasets_map_only() -> None:
    """export_fingerprint hashes compact datasets JSON only."""
    reset_state()
    ingest()
    export()
    report = load_report()
    datasets_bytes = json.dumps(report["datasets"], separators=(",", ":")).encode()
    assert report["export_fingerprint"] == hashlib.sha256(datasets_bytes).hexdigest()


def test_s5prof_staging_records_nonempty_filter_chain_hash() -> None:
    """Every staging chunk record carries non-empty filter_chain_hash."""
    reset_state()
    ingest()
    snap = load_staging()
    assert all(c["filter_chain_hash"] for c in snap["chunks"])


def test_s5prof_tb3_hidden_bundle_filter_order_hash() -> None:
    """TB3_BUNDLE hidden ingest preserves gzip|shuffle filter order hash."""
    reset_state()
    ingest(env={"TB3_BUNDLE": "/opt/verifier-fixtures/tb3_shadow"})
    snap = load_staging()
    expected = reference_filter_chain_hash(["gzip", "shuffle"])
    assert snap["chunks"][0]["filter_chain_hash"] == expected


def test_s5prof_tb3_hidden_attribute_lineage_chain() -> None:
    """Hidden bundle checks multi-level attribute inheritance with units and frame."""
    reset_state()
    ingest(env={"TB3_BUNDLE": "/opt/verifier-fixtures/tb3_shadow"})
    snap = load_staging()
    cat = json.loads((TB3_BUNDLE / "catalog.s5cat").read_text(encoding="utf-8"))
    attrs = reference_effective_attrs(cat, "/grid/field")
    got = snap["chunks"][0]["effective_attrs"]
    assert got["units"] == "Pa"
    assert got["frame"] == "ECMWF"
    assert got["scale"] == 2.0
    assert attrs == got


def test_s5prof_tb3_hidden_four_chunk_grid_and_mask_total() -> None:
    """Hidden 4-chunk grid exercises mask totals on TB3 fixture bundle."""
    reset_state()
    ingest(env={"TB3_BUNDLE": "/opt/verifier-fixtures/tb3_shadow"})
    snap = load_staging()
    assert len(snap["chunks"]) == 4
    cells = 2 * 2
    per = reference_mask_count(TB3_BUNDLE / "masks/field.mask", cells)
    assert per == 2
    assert snap["compression_totals"]["total_masked_cells"] == per * 4


def test_s5prof_tb3_export_coordinate_ok_true() -> None:
    """Hidden bundle export reports coordinate_ok true when grid is consistent."""
    reset_state()
    ingest(env={"TB3_BUNDLE": "/opt/verifier-fixtures/tb3_shadow"})
    export()
    report = load_report()
    assert report["datasets"]["/grid/field"]["coordinate_ok"] is True


def test_s5prof_row_major_origin_for_chunk_index_one() -> None:
    """Ingested chunk index 1 origin must match row-major linear decode."""
    reset_state()
    ingest()
    snap = load_staging()
    chunk_one = next(c for c in snap["chunks"] if c["chunk_index"] == 1)
    expected = reference_linear_origin(1, [4, 3], [2, 3])
    assert chunk_one["origin"] == expected
    assert chunk_one["coord_consistent"] is True


def test_s5prof_subprocess_hdclp_cli_failure_on_missing_catalog() -> None:
    """CLI ingest must exit non-zero when catalog directory is missing."""
    reset_state()
    proc = subprocess.run(
        [CHUNKLINE, "ingest", "--catalog", "/nope", "--state", "/app/state"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode != 0
