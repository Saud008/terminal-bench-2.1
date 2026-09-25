"""Safetensors shard index lineage checker contract tests."""
from __future__ import annotations

import os
from pathlib import Path

from xr7_ref_harness import (
    BIN,
    OUT,
    STATE,
    atlas_publish_only,
    catalog_dir,
    catalog_scan_only,
    load_report,
    load_journal_rows,
    pipeline,
    rebuild,
    weight_root,
)
from xr7_ref_math import reference_report, reference_journal


def test_xr7_release_binary_rebuilds():
    """Rebuild must produce the xr7 release binary before subprocess grading runs."""
    rebuild()
    assert BIN.is_file()


def test_catalog_atlas_pipeline_writes_outputs():
    """Catalog scan plus atlas publish must write journal and lineage atlas paths."""
    rebuild()
    pipeline()
    assert STATE.is_file()
    assert OUT.is_file()


def test_lineage_report_is_json_array():
    """The lineage report must be a JSON array with one entry per manifest file."""
    rebuild()
    pipeline()
    data = load_report()
    assert isinstance(data, list)
    assert len(data) >= 3


def test_each_manifest_has_totals_block():
    """Each manifest report object must expose violations and totals keys."""
    rebuild()
    pipeline()
    for entry in load_report():
        assert "violations" in entry and "totals" in entry


def test_violation_count_matches_array_length():
    """totals.violation_count must equal len(violations) for every manifest."""
    rebuild()
    pipeline()
    for entry in load_report():
        assert entry["totals"]["violation_count"] == len(entry["violations"])


def test_violations_sorted_by_tensor_then_code():
    """Violations must be sorted by tensor name then code."""
    rebuild()
    pipeline()
    for entry in load_report():
        keys = [(v["tensor"], v["code"]) for v in entry["violations"]]
        assert keys == sorted(keys)


def test_journal_run_seq_globally_monotonic():
    """Journal run_seq must increase monotonically across the whole catalog scan batch."""
    rebuild()
    pipeline()
    seqs = [row["run_seq"] for row in load_journal_rows()]
    assert seqs == sorted(seqs)
    assert seqs == list(range(len(seqs)))


def test_journal_rows_preserve_manifest_order():
    """Journal rows must follow manifest directory order then shard tensor order."""
    rebuild()
    pipeline()
    mids = [row["manifest_id"] for row in load_journal_rows()]
    assert mids.index("lora_alpha") < mids.index("lora_beta")


def test_alpha_manifest_tensor_count():
    """lora_alpha manifest must journal two tensors from alpha_adapter shard."""
    rebuild()
    pipeline()
    alpha = [r for r in load_journal_rows() if r["manifest_id"] == "lora_alpha"]
    assert len(alpha) == 2


def test_bf16_tensor_element_size_validated():
    """BF16 tensors must use two byte element sizing during catalog scan."""
    rebuild()
    pipeline()
    bf16 = [r for r in load_journal_rows() if r["dtype"] == "BF16"]
    assert bf16
    for row in bf16:
        count = 1
        for d in row["shape"]:
            count *= d
        assert row["offset_end"] - row["offset_start"] == count * 2


def test_bundled_manifests_zero_violations():
    """Correct catalog scan must yield zero violations on bundled manifest fixtures."""
    rebuild()
    pipeline()
    for entry in load_report():
        assert entry["violations"] == []


def test_journal_matches_reference_rows():
    """Journal rows must match the independent reference catalog scan output."""
    rebuild()
    pipeline()
    got = load_journal_rows()
    ref = reference_journal(catalog_dir(), weight_root())
    assert len(got) == len(ref)
    for g, r in zip(got, ref):
        assert g["manifest_id"] == r["manifest_id"]
        assert g["tensor"] == r["tensor"]
        assert g["payload_fingerprint"] == r["payload_fingerprint"]
        assert g["run_seq"] == r["run_seq"]
        assert g["lineage_ok"] == r["lineage_ok"]


def test_journal_snapshot_on_disk_after_catalog_scan():
    """Journal snapshot file must exist on disk after catalog-scan-only."""
    rebuild()
    catalog_scan_only()
    assert STATE.is_file()
    rows = load_journal_rows()
    assert rows
    ref = reference_journal(catalog_dir(), weight_root())
    assert len(rows) == len(ref)


def test_ingest_only_catalog_scan_then_export_atlas_publish():
    """Catalog-scan-only then atlas-publish must match full pipeline output."""
    rebuild()
    catalog_scan_only()
    atlas_publish_only()
    got = load_report()
    ref = reference_report(catalog_dir(), weight_root(), reference_journal(catalog_dir(), weight_root()))
    assert got == ref


def test_report_matches_reference_audit():
    """Lineage report must match the independent reference atlas publish output."""
    rebuild()
    pipeline()
    got = load_report()
    ref = reference_report(catalog_dir(), weight_root(), reference_journal(catalog_dir(), weight_root()))
    assert got == ref


def test_tensor_count_matches_journal():
    """totals.tensor_count must equal staged rows per manifest."""
    rebuild()
    pipeline()
    staged = load_journal_rows()
    for entry in load_report():
        count = sum(1 for r in staged if r["manifest_id"] == entry["manifest_id"])
        assert entry["totals"]["tensor_count"] == count


def test_hidden_manifest_dir_override(tmp_path, monkeypatch):
    """XR7_CATALOG_ROOT and XR7_WEIGHT_ROOT must drive catalog scan on hidden fixtures."""
    hidden_m = Path("/opt/verifier-fixtures/xr7_probe/catalogs")
    hidden_s = Path("/opt/verifier-fixtures/xr7_probe/weights")
    if not hidden_m.is_dir():
        return
    monkeypatch.setenv("XR7_CATALOG_ROOT", str(hidden_m))
    monkeypatch.setenv("XR7_WEIGHT_ROOT", str(hidden_s))
    rebuild()
    pipeline(hidden_m, hidden_s)
    got = load_journal_rows()
    ref = reference_journal(hidden_m, hidden_s)
    assert len(got) == len(ref)


def test_hidden_mixed_case_lineage_hash():
    """Hidden lineage_mixed_case manifest must accept case insensitive hash match."""
    hidden_m = Path("/opt/verifier-fixtures/xr7_probe/catalogs")
    hidden_s = Path("/opt/verifier-fixtures/xr7_probe/weights")
    if not hidden_m.is_dir():
        return
    os.environ["XR7_CATALOG_ROOT"] = str(hidden_m)
    os.environ["XR7_WEIGHT_ROOT"] = str(hidden_s)
    rebuild()
    pipeline(hidden_m, hidden_s)
    rows = [r for r in load_journal_rows() if r["manifest_id"] == "lineage_mixed_case"]
    assert rows and all(r["lineage_ok"] for r in rows)


def test_hidden_offset_payload_boundary():
    """Hidden tight_offset manifest must validate offsets against payload length only."""
    hidden_m = Path("/opt/verifier-fixtures/xr7_probe/catalogs")
    hidden_s = Path("/opt/verifier-fixtures/xr7_probe/weights")
    if not hidden_m.is_dir():
        return
    os.environ["XR7_CATALOG_ROOT"] = str(hidden_m)
    os.environ["XR7_WEIGHT_ROOT"] = str(hidden_s)
    rebuild()
    pipeline(hidden_m, hidden_s)
    for entry in load_report():
        if entry["manifest_id"] == "tight_offset":
            assert entry["violations"] == []


def test_hidden_fingerprint_payload_only():
    """Hidden fixtures must use payload-only fingerprints not whole-file digests."""
    hidden_m = Path("/opt/verifier-fixtures/xr7_probe/catalogs")
    hidden_s = Path("/opt/verifier-fixtures/xr7_probe/weights")
    if not hidden_m.is_dir():
        return
    os.environ["XR7_CATALOG_ROOT"] = str(hidden_m)
    os.environ["XR7_WEIGHT_ROOT"] = str(hidden_s)
    rebuild()
    pipeline(hidden_m, hidden_s)
    got = load_journal_rows()
    ref = reference_journal(hidden_m, hidden_s)
    for g, r in zip(got, ref):
        assert g["payload_fingerprint"] == r["payload_fingerprint"]


def test_repeated_atlas_publish_deterministic():
    """Repeated atlas publish runs must emit byte-identical JSON output."""
    rebuild()
    pipeline()
    first = OUT.read_text(encoding="utf-8")
    pipeline()
    second = OUT.read_text(encoding="utf-8")
    assert first == second


def test_decoy_module_not_required():
    """Pipeline must succeed without invoking tensor_decoy_surface decoy helpers."""
    rebuild()
    pipeline()
    assert OUT.is_file()
