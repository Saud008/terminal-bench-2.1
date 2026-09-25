"""Bundled crpe behavioral tests."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from crpe_cli_support import NORMALIZED, run_pipeline, wipe, invoke, CLI, APP
from crpe_contract_math import reference_ledger, normalized_fingerprint, ledger_digest


def test_crpe_cli_on_path():
    """Verify crpe is installed at /app/bin/crpe per instruction."""
    assert Path("/app/bin/crpe").is_file()
    proc = subprocess.run(["/app/bin/crpe"], capture_output=True, text=True)
    assert proc.returncode != 0


def test_coastal_pool_ledger_matches_reference():
    """Verify coastal-pool cluster topology ledger pg_traces and ledger_digest match reference math."""
    wipe()
    out = run_pipeline("coastal-pool", "run-coastal", 0, 7)
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_ledger(Path("/app/maps/coastal-pool"), "run-coastal", 0, 7)
    assert rep["pg_traces"] == ref["pg_traces"]
    assert rep["ledger_digest"] == ref["ledger_digest"]


def test_normalized_snapshot_written():
    """Verify crpe-normalized.json fleet snapshot includes run_id and normalized_fingerprint after normalize."""
    wipe()
    run_pipeline("coastal-pool", "run-norm", 0, 1)
    snap = json.loads(NORMALIZED.read_text(encoding="utf-8"))
    assert snap["run_id"] == "run-norm"
    assert "normalized_fingerprint" in snap


def test_normalized_fingerprint_matches_reference():
    """Verify normalized_fingerprint matches independent hash from normalized-snapshot-schema."""
    wipe()
    run_pipeline("coastal-pool", "run-fp", 0, 1)
    snap = json.loads(NORMALIZED.read_text(encoding="utf-8"))
    loaded = json.loads((APP / "work/run-fp-loaded.json").read_text(encoding="utf-8"))
    ref_fp = normalized_fingerprint(loaded["crush"]["buckets"], loaded["osd"]["osds"])
    assert snap["normalized_fingerprint"] == ref_fp


def test_pg_traces_sorted_ascending():
    """Verify ledger pg_traces sort ascending by pg_num per placement-trace-ledger-schema."""
    wipe()
    out = run_pipeline("coastal-pool", "run-sort", 0, 5)
    rep = json.loads(out.read_text(encoding="utf-8"))
    nums = [t["pg_num"] for t in rep["pg_traces"]]
    assert nums == sorted(nums)


def test_pg_id_hex_format():
    """Verify pg_id uses pool_id dot lowercase hex pg_num."""
    wipe()
    out = run_pipeline("coastal-pool", "run-pgid", 10, 10)
    rep = json.loads(out.read_text(encoding="utf-8"))
    row = rep["pg_traces"][0]
    assert row["pg_id"] == f"{row['pool_id']}.{row['pg_num']:x}"


def test_acting_set_size_matches_pool():
    """Verify acting_set length equals pool size for coastal-pool."""
    wipe()
    out = run_pipeline("coastal-pool", "run-size", 0, 4)
    rep = json.loads(out.read_text(encoding="utf-8"))
    for row in rep["pg_traces"]:
        assert len(row["acting_set"]) == 3


def test_primary_osd_is_first_acting():
    """Verify primary_osd equals first acting_set member."""
    wipe()
    out = run_pipeline("coastal-pool", "run-primary", 0, 6)
    rep = json.loads(out.read_text(encoding="utf-8"))
    for row in rep["pg_traces"]:
        assert row["primary_osd"] == row["acting_set"][0]


def test_out_osd_trap_excludes_down_out():
    """Verify out-osd-trap excludes down and out osds from acting sets."""
    wipe()
    out = run_pipeline("out-osd-trap", "run-out", 0, 3)
    rep = json.loads(out.read_text(encoding="utf-8"))
    for row in rep["pg_traces"]:
        assert 11 not in row["acting_set"]
        assert 12 not in row["acting_set"]


def test_out_osd_trap_trace_excluded_field():
    """Verify chooseleaf steps list excluded down/out osds in trace rows."""
    wipe()
    out = run_pipeline("out-osd-trap", "run-trace-excl", 1, 1)
    rep = json.loads(out.read_text(encoding="utf-8"))
    steps = rep["pg_traces"][0]["steps"]
    leaf = next(s for s in steps if s["op"] == "chooseleaf")
    assert 11 in leaf["excluded_osds"]
    assert 12 in leaf["excluded_osds"]


def test_rand_weight_pool_matches_reference():
    """Verify rand-weight-pool ledger matches reference with reweight multiplication."""
    wipe()
    out = run_pipeline("rand-weight-pool", "run-rand", 0, 5)
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_ledger(Path("/app/maps/rand-weight-pool"), "run-rand", 0, 5)
    assert rep["pg_traces"] == ref["pg_traces"]


def test_ledger_digest_matches_reference():
    """Verify ledger_digest seals pg trace rows per placement-trace-ledger-schema."""
    wipe()
    out = run_pipeline("coastal-pool", "run-digest", 0, 2)
    rep = json.loads(out.read_text(encoding="utf-8"))
    pool = json.loads((Path("/app/maps/coastal-pool/pool.json")).read_text(encoding="utf-8"))
    ref_digest = ledger_digest("run-digest", pool, rep["pg_traces"])
    assert rep["ledger_digest"] == ref_digest


def test_export_bytes_stable_on_repeat():
    """Verify repeat export to same path is byte-identical."""
    wipe()
    run_pipeline("coastal-pool", "run-stable", 0, 2)
    first = (APP / "output/run-stable-ledger.json").read_bytes()
    invoke([str(CLI), "export-ledger", "--run-id", "run-stable", "--pg-start", "0", "--pg-end", "2", "--output", str(APP / "output/run-stable-ledger.json")])
    assert first == (APP / "output/run-stable-ledger.json").read_bytes()


def test_decoy_rack_rank_helper_absent():
    """Verify ledger JSON does not include decoy rack_rank_helper output."""
    wipe()
    out = run_pipeline("coastal-pool", "run-decoy", 0, 1)
    assert "decoy-rack-rank" not in out.read_text(encoding="utf-8")


def test_take_step_present_in_trace():
    """Verify each pg trace includes a take step naming the default bucket."""
    wipe()
    out = run_pipeline("coastal-pool", "run-take", 0, 2)
    rep = json.loads(out.read_text(encoding="utf-8"))
    for row in rep["pg_traces"]:
        take = next(s for s in row["steps"] if s["op"] == "take")
        assert take["bucket"] == "default"


def test_emit_step_records_acting_set():
    """Verify emit step acting_set matches top-level acting_set."""
    wipe()
    out = run_pipeline("coastal-pool", "run-emit", 0, 2)
    rep = json.loads(out.read_text(encoding="utf-8"))
    for row in rep["pg_traces"]:
        emit = next(s for s in row["steps"] if s["op"] == "emit")
        assert emit["acting_set"] == row["acting_set"]


def test_cross_run_state_reset():
    """Verify cross-run fleet isolation clears work output and state directories between run ids."""
    wipe()
    run_pipeline("coastal-pool", "run-cross-a", 0, 1)
    wipe()
    assert not list((APP / "work").glob("*"))
    out = run_pipeline("coastal-pool", "run-cross-b", 0, 1)
    assert out.exists()


def test_loaded_json_retains_map_name():
    """Verify loaded cluster manifest records map_name for placement manifest export."""
    wipe()
    out = run_pipeline("coastal-pool", "run-mapname", 0, 0)
    rep = json.loads(out.read_text(encoding="utf-8"))
    assert rep["map_name"] == "coastal-pool"
