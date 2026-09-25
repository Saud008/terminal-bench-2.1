
"""Primary flink-skew verifier contracts."""
from __future__ import annotations

import json
import subprocess

import pytest

from flink_skew_shell_ops import HIDDEN_ROOT, JAR, PATHS, exec_skew, fixture_events_dir, rebuild_jar, run_full_pipeline, wipe_workspace
from skew_refmath import reference_alignment_rows, reference_chronicle, reference_event_index


def test_tf7c2a91e_load_events_writes_index() -> None:
    """load-events must write event_index.json with sorted events."""
    wipe_workspace()
    proc = exec_skew(["load-events", "--input", str(fixture_events_dir()), "--out", str(PATHS["index"])])
    assert proc.returncode == 0
    assert PATHS["index"].is_file()
    body = json.loads(PATHS["index"].read_text(encoding="utf-8"))
    assert len(body) >= 20


def test_tf7c2a91e_index_matches_reference() -> None:
    """event_index.json must match independent reference loader math."""
    wipe_workspace()
    proc = exec_skew(["load-events", "--input", str(fixture_events_dir()), "--out", str(PATHS["index"])])
    assert proc.returncode == 0
    got = json.loads(PATHS["index"].read_text(encoding="utf-8"))
    ref = reference_event_index(fixture_events_dir())
    assert len(got) == len(ref)
    assert [r["timestamp_ms"] for r in got] == [r["timestamp_ms"] for r in ref]


def test_tf7c2a91e_load_events_idempotent_bytes() -> None:
    """Repeated load-events must write byte-identical event_index.json."""
    wipe_workspace()
    for _ in range(2):
        proc = exec_skew(["load-events", "--input", str(fixture_events_dir()), "--out", str(PATHS["index"])])
        assert proc.returncode == 0
    first = PATHS["index"].read_bytes()
    proc = exec_skew(["load-events", "--input", str(fixture_events_dir()), "--out", str(PATHS["index"])])
    assert proc.returncode == 0
    assert PATHS["index"].read_bytes() == first


def test_tf7c2a91e_align_writes_buffer() -> None:
    """align-barriers must write alignment.buffer JSONL."""
    run_full_pipeline()
    assert PATHS["buffer"].is_file()
    lines = [ln for ln in PATHS["buffer"].read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) >= 6


def test_tf7c2a91e_buffer_digest_present() -> None:
    """Each alignment.buffer row must include 16-hex buffer_digest."""
    run_full_pipeline()
    for line in PATHS["buffer"].read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        assert len(row["buffer_digest"]) == 16


def test_tf7c2a91e_buffer_matches_reference() -> None:
    """alignment.buffer rows must match reference skew math."""
    run_full_pipeline()
    got = [json.loads(ln) for ln in PATHS["buffer"].read_text(encoding="utf-8").splitlines() if ln.strip()]
    ref = reference_alignment_rows(json.loads(PATHS["index"].read_text(encoding="utf-8")))
    assert len(got) == len(ref)
    for g, r in zip(got, ref):
        assert g["operator_id"] == r["operator_id"]
        assert g["skew_ms"] == r["skew_ms"]
        assert g["alignment_class"] == r["alignment_class"]


def test_tf7c2a91e_buffer_bytes_before_chronicle() -> None:
    """emit-chronicle must not mutate alignment.buffer bytes."""
    wipe_workspace()
    events = fixture_events_dir()
    exec_skew(["load-events", "--input", str(events), "--out", str(PATHS["index"])])
    exec_skew(["align-barriers", "--index", str(PATHS["index"]), "--out", str(PATHS["buffer"])])
    before = PATHS["buffer"].read_bytes()
    proc = exec_skew(["emit-chronicle", "--buffer", str(PATHS["buffer"]), "--out", str(PATHS["chronicle"])])
    assert proc.returncode == 0
    assert PATHS["buffer"].read_bytes() == before


def test_tf7c2a91e_chronicle_job_id() -> None:
    """Chronicle must copy job_id from job_meta.json."""
    run_full_pipeline()
    body = json.loads(PATHS["chronicle"].read_text(encoding="utf-8"))
    assert body["job_id"] == "job-f7c2a91e-flinkops"


def test_tf7c2a91e_chronicle_checkpoint_sort() -> None:
    """checkpoints sorted by checkpoint_id then attempt_id."""
    run_full_pipeline()
    body = json.loads(PATHS["chronicle"].read_text(encoding="utf-8"))
    keys = [(c["checkpoint_id"], c["attempt_id"]) for c in body["checkpoints"]]
    assert keys == sorted(keys)


def test_tf7c2a91e_chronicle_operator_sort() -> None:
    """operators within checkpoint sorted by operator_id."""
    run_full_pipeline()
    body = json.loads(PATHS["chronicle"].read_text(encoding="utf-8"))
    for cp in body["checkpoints"]:
        ids = [o["operator_id"] for o in cp["operators"]]
        assert ids == sorted(ids)


def test_tf7c2a91e_chronicle_matches_reference() -> None:
    """barrier_skew_chronicle.json must match reference chronicle math."""
    run_full_pipeline()
    got = json.loads(PATHS["chronicle"].read_text(encoding="utf-8"))
    ref = reference_chronicle([json.loads(ln) for ln in PATHS["buffer"].read_text(encoding="utf-8").splitlines() if ln.strip()])
    assert got["job_id"] == ref["job_id"]
    assert len(got["checkpoints"]) == len(ref["checkpoints"])


def test_tf7c2a91e_emit_without_buffer_errors() -> None:
    """emit-chronicle must fail when buffer missing."""
    rebuild_jar()
    wipe_workspace()
    result = subprocess.run(
        ["java", "-jar", str(JAR), "emit-chronicle", "--buffer", str(PATHS["buffer"]), "--out", str(PATHS["chronicle"])],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0


def test_tf7c2a91e_align_without_index_errors() -> None:
    """align-barriers must fail when index missing."""
    rebuild_jar()
    wipe_workspace()
    result = subprocess.run(
        ["java", "-jar", str(JAR), "align-barriers", "--index", str(PATHS["index"]), "--out", str(PATHS["buffer"])],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0


def test_tf7c2a91e_map2_skew_nonzero() -> None:
    """map-2 operator must show non-zero skew on bundled fixtures."""
    run_full_pipeline()
    rows = [json.loads(ln) for ln in PATHS["buffer"].read_text(encoding="utf-8").splitlines() if ln.strip()]
    map_rows = [r for r in rows if r["operator_id"] == "map-2"]
    assert map_rows
    assert any(r["skew_ms"] > 0 for r in map_rows)


def test_tf7c2a91e_summary_timeout_counts() -> None:
    """summary.timeout_violation_count must match operator rows."""
    run_full_pipeline()
    body = json.loads(PATHS["chronicle"].read_text(encoding="utf-8"))
    for cp in body["checkpoints"]:
        ops = cp["operators"]
        summary = cp["summary"]
        expected = sum(1 for o in ops if o["alignment_class"] == "TIMEOUT_VIOLATION")
        assert summary["timeout_violation_count"] == expected


def test_tf7c2a91e_misalignment_class_mapping() -> None:
    """TIMEOUT_VIOLATION maps to SKEW_TIMEOUT misalignment_class."""
    run_full_pipeline()
    body = json.loads(PATHS["chronicle"].read_text(encoding="utf-8"))
    for cp in body["checkpoints"]:
        for op in cp["operators"]:
            if op["alignment_class"] == "TIMEOUT_VIOLATION":
                assert op["misalignment_class"] == "SKEW_TIMEOUT"


def test_tf7c2a91e_hidden_tb3_unaligned_only(monkeypatch: pytest.MonkeyPatch) -> None:
    """Hidden unaligned-only fixtures must declare UNALIGNED_DECLARED with non-zero skew."""
    monkeypatch.setenv("TB3_FIXTURE_ROOT", str(HIDDEN_ROOT / "unaligned_only"))
    run_full_pipeline()
    rows = [json.loads(ln) for ln in PATHS["buffer"].read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert any(r["alignment_class"] == "UNALIGNED_DECLARED" and r["skew_ms"] > 0 for r in rows)


def test_tf7c2a91e_hidden_tb3_chained_only(monkeypatch: pytest.MonkeyPatch) -> None:
    """Hidden chained-only fixtures must not double-count chain boundary barriers."""
    monkeypatch.setenv("TB3_FIXTURE_ROOT", str(HIDDEN_ROOT / "chained_only"))
    run_full_pipeline()
    ref = reference_alignment_rows(json.loads(PATHS["index"].read_text(encoding="utf-8")))
    got = [json.loads(ln) for ln in PATHS["buffer"].read_text(encoding="utf-8").splitlines() if ln.strip()]
    for g, r in zip(got, ref):
        assert g["barriers_received"] == r["barriers_received"]


def test_tf7c2a91e_watermark_excluded_from_barriers() -> None:
    """barriers_received must exclude watermark-only receipts."""
    run_full_pipeline()
    ref = reference_alignment_rows(json.loads(PATHS["index"].read_text(encoding="utf-8")))
    got = [json.loads(ln) for ln in PATHS["buffer"].read_text(encoding="utf-8").splitlines() if ln.strip()]
    for g, r in zip(got, ref):
        assert g["barriers_received"] == r["barriers_received"]


def test_tf7c2a91e_attempt_retry_rows_preserved() -> None:
    """Distinct attempt_id rows must survive load-events dedupe."""
    run_full_pipeline()
    idx = json.loads(PATHS["index"].read_text(encoding="utf-8"))
    attempts = {(r["checkpoint_id"], r["attempt_id"]) for r in idx}
    assert len(attempts) >= 6


def test_tf7c2a91e_cross_run_load_idempotent_after_reset() -> None:
    """load-events must stay byte-stable across workspace reset and reload."""
    wipe_workspace()
    events = fixture_events_dir()
    exec_skew(["load-events", "--input", str(events), "--out", str(PATHS["index"])])
    first = PATHS["index"].read_bytes()
    wipe_workspace()
    exec_skew(["load-events", "--input", str(events), "--out", str(PATHS["index"])])
    second = PATHS["index"].read_bytes()
    assert first == second


def test_tf7c2a91e_incomplete_class_when_subtasks_missing() -> None:
    """operators with fewer barrier receipts than parallelism must be INCOMPLETE when aligned."""
    run_full_pipeline()
    rows = [json.loads(ln) for ln in PATHS["buffer"].read_text(encoding="utf-8").splitlines() if ln.strip()]
    incomplete = [r for r in rows if r["alignment_class"] == "INCOMPLETE"]
    assert incomplete or all(r["barriers_received"] >= r["expected_subtasks"] for r in rows)


def test_tf7c2a91e_unaligned_skew_not_zero_in_buffer(monkeypatch: pytest.MonkeyPatch) -> None:
    """UNALIGNED_DECLARED rows must retain computed skew_ms on hidden unaligned fixtures."""
    monkeypatch.setenv("TB3_FIXTURE_ROOT", str(HIDDEN_ROOT / "unaligned_only"))
    run_full_pipeline()
    rows = [json.loads(ln) for ln in PATHS["buffer"].read_text(encoding="utf-8").splitlines() if ln.strip()]
    unaligned = [r for r in rows if r["alignment_class"] == "UNALIGNED_DECLARED"]
    assert unaligned and all(r["skew_ms"] > 0 for r in unaligned)
