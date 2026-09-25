"""Behavioral tests for feastctl point-in-time join validator."""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
import subprocess
import tempfile
from pathlib import Path

import pytest
from reference_pit import load_scenario, reference_report, reference_validate, scoped_id

APP = Path("/app")
FEASTCTL = Path("/usr/local/bin/feastctl")
RESET = Path("/tests/reset-state.sh")
STAGING = APP / "state" / "pit-staging.json"
PARITY_DB = APP / "work" / "parity.db"
SCENARIOS = APP / "fixtures" / "scenarios"
SEEDS = json.loads((APP / "fixtures" / "seeds.json").read_text(encoding="utf-8"))["seeds"]
HIDDEN = Path("/tests/hidden/scenarios")


def run(cmd: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False, env=merged)


def reset() -> None:
    proc = run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def pipeline(seed: str, scenario: str, *, fixture_dir: Path | None = None, env: dict | None = None) -> Path:
    merged = env or {}
    if fixture_dir is not None:
        merged = {**merged, "TB3_FIXTURE_DIR": str(fixture_dir)}
    for step in (
        [str(FEASTCTL), "load", "--seed", seed, "--scenario", scenario],
        [str(FEASTCTL), "validate", "join", "--seed", seed, "--scenario", scenario],
    ):
        proc = run(step, env=merged)
        assert proc.returncode == 0, proc.stderr + proc.stdout
    out = APP / "output" / f"{seed}-{scenario}-parity.json"
    proc = run(
        [str(FEASTCTL), "export", "report", "--seed", seed, "--scenario", scenario, "--output", str(out)],
        env=merged,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return out


def _stage_hidden(*names: str) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="tb3-feast-"))
    for name in names:
        shutil.copy(HIDDEN / name, tmp / name)
    return tmp


def _parity_row_values(seed: str, scenario: str) -> list[tuple]:
    con = sqlite3.connect(PARITY_DB)
    rows = con.execute(
        """
        SELECT r.entity_id, r.feature, r.as_of_ts, r.offline_value, r.online_value, r.match_ok
        FROM parity_rows r
        JOIN parity_runs p ON p.id = r.run_id
        WHERE p.seed = ? AND p.scenario = ?
        ORDER BY r.entity_id, r.feature, r.as_of_ts
        """,
        (seed, scenario),
    ).fetchall()
    con.close()
    return rows


@pytest.fixture(autouse=True)
def clean_state():
    reset()
    yield
    reset()


def test_feastctl_binary_exists():
    """Instruction requires feastctl built at /usr/local/bin/feastctl."""
    assert FEASTCTL.is_file()


def test_bundled_scenarios_directory():
    """Instruction cites bundled scenarios under /app/fixtures/scenarios."""
    assert SCENARIOS.is_dir()
    assert (SCENARIOS / "basic-pit.json").is_file()


def test_load_writes_staging_snapshot():
    """load must write normalized staging at /app/state/pit-staging.json."""
    seed = SEEDS[0]
    proc = run([str(FEASTCTL), "load", "--seed", seed, "--scenario", "basic-pit"])
    assert proc.returncode == 0
    snap = json.loads(STAGING.read_text(encoding="utf-8"))
    assert snap["seed"] == seed
    assert snap["scenario"] == "basic-pit"
    assert len(snap["events"]) >= 4
    assert any(ev["entity_id"] == scoped_id(seed, "u1") for ev in snap["events"])


def test_load_increments_ingest_seq():
    """Repeated load bumps ingest_seq monotonically."""
    seed = SEEDS[0]
    run([str(FEASTCTL), "load", "--seed", seed, "--scenario", "basic-pit"])
    first = json.loads(STAGING.read_text(encoding="utf-8"))["ingest_seq"]
    run([str(FEASTCTL), "load", "--seed", seed, "--scenario", "basic-pit"])
    second = json.loads(STAGING.read_text(encoding="utf-8"))["ingest_seq"]
    assert second == first + 1


def test_staging_path_contract():
    """Instruction staging path /app/state/pit-staging.json is honored."""
    run([str(FEASTCTL), "load", "--seed", SEEDS[0], "--scenario", "basic-pit"])
    assert STAGING == Path("/app/state/pit-staging.json")


def test_validate_persists_sqlite_runs():
    """validate join writes parity tables into /app/work/parity.db."""
    seed = SEEDS[0]
    pipeline(seed, "basic-pit")
    assert PARITY_DB.is_file()
    con = sqlite3.connect(PARITY_DB)
    cur = con.execute("SELECT COUNT(*) FROM parity_runs")
    assert cur.fetchone()[0] == 1
    con.close()


def test_basic_pit_parity_ok():
    """basic-pit bundled scenario achieves parity_ok true at reference."""
    seed = SEEDS[0]
    out = pipeline(seed, "basic-pit")
    rep = json.loads(out.read_text(encoding="utf-8"))
    sc = load_scenario(SCENARIOS / "basic-pit.json", seed)
    ref = reference_validate(sc, sc["ttl_seconds"])
    assert rep["parity_ok"] == ref["parity_ok"]
    assert rep["parity_ok"] is True
    rows = _parity_row_values(seed, "basic-pit")
    assert len(rows) == len(ref["rows"])
    assert len(rows) >= 2
    assert any(r[0] == scoped_id(seed, "u1") and r[3] == pytest.approx(1.2344) for r in rows)


def test_report_summary_matches_reference():
    """parity-report-schema summary fields match independent reference."""
    seed = SEEDS[1]
    out = pipeline(seed, "basic-pit")
    rep = json.loads(out.read_text(encoding="utf-8"))
    sc = load_scenario(SCENARIOS / "basic-pit.json", seed)
    ref = reference_validate(sc, sc["ttl_seconds"])
    assert rep["summary"] == ref["summary"]


def test_audit_digest_matches_reference():
    """audit_digest uses canonical summary JSON per report schema."""
    seed = SEEDS[0]
    out = pipeline(seed, "basic-pit")
    rep = json.loads(out.read_text(encoding="utf-8"))
    sc = load_scenario(SCENARIOS / "basic-pit.json", seed)
    ref = reference_validate(sc, sc["ttl_seconds"])
    assert rep["audit_digest"] == ref["audit_digest"]


def test_ttl_window_filters_stale_events():
    """ttl-window.md excludes events outside TTL from parity rows."""
    seed = SEEDS[0]
    out = pipeline(seed, "ttl-window")
    rep = json.loads(out.read_text(encoding="utf-8"))
    sc = load_scenario(SCENARIOS / "ttl-window.json", seed)
    ref = reference_validate(sc, sc["ttl_seconds"])
    assert rep["summary"]["ttl_filtered_count"] == ref["summary"]["ttl_filtered_count"]
    assert ref["summary"]["ttl_filtered_count"] >= 2
    assert len(ref["rows"]) >= 1
    assert rep["parity_ok"] is True
    rows = _parity_row_values(seed, "ttl-window")
    assert len(rows) == len(ref["rows"])
    assert rows[0][3] == pytest.approx(1.0)


def test_composite_entity_requires_device_match():
    """entity-key-contract.md requires all composite keys to match."""
    seed = SEEDS[1]
    out = pipeline(seed, "composite-entity")
    rep = json.loads(out.read_text(encoding="utf-8"))
    sc = load_scenario(SCENARIOS / "composite-entity.json", seed)
    ref = reference_validate(sc, sc["ttl_seconds"])
    assert rep["parity_ok"] == ref["parity_ok"]
    assert rep["parity_ok"] is True
    assert len(ref["rows"]) >= 2
    rows = _parity_row_values(seed, "composite-entity")
    assert any(r[0] == scoped_id(seed, "pair1") and r[3] == pytest.approx(4.2) for r in rows)
    assert any(r[3] == pytest.approx(9.9) for r in rows)


def test_backfill_partition_scopes_offline_events():
    """backfill-partition.md uses active_partition per as_of entry."""
    seed = SEEDS[2]
    out = pipeline(seed, "backfill-partition")
    rep = json.loads(out.read_text(encoding="utf-8"))
    sc = load_scenario(SCENARIOS / "backfill-partition.json", seed)
    ref = reference_validate(sc, sc["ttl_seconds"])
    assert rep["parity_ok"] == ref["parity_ok"]
    assert rep["parity_ok"] is True
    assert len(ref["rows"]) >= 1
    rows = _parity_row_values(seed, "backfill-partition")
    assert all(r[0] == scoped_id(seed, "u4") for r in rows)


def test_duplicate_event_ts_resolves_highest_seq():
    """duplicate-event-ts.md keeps greatest seq for identical timestamps."""
    seed = SEEDS[0]
    out = pipeline(seed, "duplicate-event-ts")
    rep = json.loads(out.read_text(encoding="utf-8"))
    sc = load_scenario(SCENARIOS / "duplicate-event-ts.json", seed)
    ref = reference_validate(sc, sc["ttl_seconds"])
    assert rep["summary"]["duplicate_ts_resolved"] == ref["summary"]["duplicate_ts_resolved"]
    assert rep["parity_ok"] is True
    rows = _parity_row_values(seed, "duplicate-event-ts")
    assert rows[0][3] == pytest.approx(2.0)
    assert rows[0][4] == pytest.approx(2.0)


def test_parity_rows_count_matches_reference():
    """parity_rows table row count matches reference join targets."""
    seed = SEEDS[0]
    pipeline(seed, "basic-pit")
    sc = load_scenario(SCENARIOS / "basic-pit.json", seed)
    ref = reference_validate(sc, sc["ttl_seconds"])
    con = sqlite3.connect(PARITY_DB)
    n = con.execute("SELECT COUNT(*) FROM parity_rows").fetchone()[0]
    con.close()
    assert n == len(ref["rows"])
    assert n >= 2


def test_export_output_path_honored():
    """export report writes caller-provided output path."""
    seed = SEEDS[0]
    out = pipeline(seed, "basic-pit")
    assert out.is_file()
    assert str(out).startswith("/app/output/")


def test_subprocess_cli_roundtrip():
    """Independent reference agrees after subprocess load validate export."""
    seed = SEEDS[1]
    out = pipeline(seed, "basic-pit")
    rep = json.loads(out.read_text(encoding="utf-8"))
    sc = load_scenario(SCENARIOS / "basic-pit.json", seed)
    ref = reference_validate(sc, sc["ttl_seconds"])
    expected = reference_report(seed, "basic-pit", rep["run_id"], ref)
    assert rep == expected


def test_instruction_fixtures_paths_exercised():
    """Instruction paths /app/fixtures/ are exercised end-to-end."""
    assert list(SCENARIOS.glob("*.json"))
    seed = SEEDS[0]
    rep = json.loads(pipeline(seed, "basic-pit").read_text(encoding="utf-8"))
    assert rep["scenario"] == "basic-pit"


def test_tb3_hidden_composite_entity_parity():
    """Hidden tb3-pit-composite scenario matches reference parity."""
    seed = SEEDS[2]
    meta = _stage_hidden("tb3-pit-composite.json")
    try:
        out = pipeline(seed, "tb3-pit-composite", fixture_dir=meta)
        rep = json.loads(out.read_text(encoding="utf-8"))
        sc = load_scenario(meta / "tb3-pit-composite.json", seed)
        ref = reference_validate(sc, sc["ttl_seconds"])
        assert rep["parity_ok"] == ref["parity_ok"]
        assert rep["parity_ok"] is True
        assert rep["summary"] == ref["summary"]
        assert len(ref["rows"]) >= 2
        rows = _parity_row_values(seed, "tb3-pit-composite")
        assert any(r[3] == pytest.approx(5.0014) for r in rows)
        assert any(r[3] == pytest.approx(1.5) for r in rows)
        assert any(r[3] == pytest.approx(99.0) for r in rows)
    finally:
        shutil.rmtree(meta, ignore_errors=True)


def test_tb3_ttl_bias_env():
    """TB3_TTL_BIAS adjusts TTL window for hidden scenarios."""
    seed = SEEDS[0]
    meta = _stage_hidden("tb3-ttl-boundary.json")
    try:
        reset()
        bias = 15000
        env = {"TB3_TTL_BIAS": str(bias), "TB3_FIXTURE_DIR": str(meta)}
        run([str(FEASTCTL), "load", "--seed", seed, "--scenario", "tb3-ttl-boundary"], env={"TB3_FIXTURE_DIR": str(meta)})
        run([str(FEASTCTL), "validate", "join", "--seed", seed, "--scenario", "tb3-ttl-boundary"], env=env)
        out = APP / "output" / f"{seed}-tb3-ttl-boundary-parity.json"
        run(
            [str(FEASTCTL), "export", "report", "--seed", seed, "--scenario", "tb3-ttl-boundary", "--output", str(out)],
            env={"TB3_FIXTURE_DIR": str(meta)},
        )
        rep = json.loads(out.read_text(encoding="utf-8"))
        sc = load_scenario(meta / "tb3-ttl-boundary.json", seed)
        ref_plain = reference_validate(sc, sc["ttl_seconds"])
        ref_bias = reference_validate(sc, sc["ttl_seconds"] + bias)
        assert ref_plain["summary"]["ttl_filtered_count"] != ref_bias["summary"]["ttl_filtered_count"]
        assert rep["summary"]["ttl_filtered_count"] == ref_bias["summary"]["ttl_filtered_count"]
        assert rep["parity_ok"] is True
        assert len(ref_bias["rows"]) >= 2
    finally:
        shutil.rmtree(meta, ignore_errors=True)


def test_tb3_hidden_audit_digest():
    """Hidden fixture audit_digest matches reference canonical digest."""
    seed = SEEDS[1]
    meta = _stage_hidden("tb3-pit-composite.json")
    try:
        out = pipeline(seed, "tb3-pit-composite", fixture_dir=meta)
        rep = json.loads(out.read_text(encoding="utf-8"))
        sc = load_scenario(meta / "tb3-pit-composite.json", seed)
        ref = reference_validate(sc, sc["ttl_seconds"])
        assert rep["audit_digest"] == ref["audit_digest"]
    finally:
        shutil.rmtree(meta, ignore_errors=True)


def test_tb3_ttl_boundary_device_parity():
    """Hidden ttl-boundary scenario grades inclusive TTL and device keys."""
    seed = SEEDS[1]
    meta = _stage_hidden("tb3-ttl-boundary.json")
    try:
        out = pipeline(seed, "tb3-ttl-boundary", fixture_dir=meta)
        rep = json.loads(out.read_text(encoding="utf-8"))
        sc = load_scenario(meta / "tb3-ttl-boundary.json", seed)
        ref = reference_validate(sc, sc["ttl_seconds"])
        assert rep["summary"] == ref["summary"]
        assert rep["parity_ok"] is True
        assert ref["summary"]["ttl_filtered_count"] >= 2
        assert len(ref["rows"]) >= 2
        rows = _parity_row_values(seed, "tb3-ttl-boundary")
        assert any(r[3] == pytest.approx(3.3334) for r in rows)
        assert any(r[3] == pytest.approx(7.7) for r in rows)
    finally:
        shutil.rmtree(meta, ignore_errors=True)


def test_summary_as_of_ts_sorted():
    """parity-report-schema requires as_of_ts sorted ascending."""
    seed = SEEDS[0]
    out = pipeline(seed, "basic-pit")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ts = rep["summary"]["as_of_ts"]
    assert ts == sorted(ts)


def test_sqlite_summary_matches_export():
    """parity_summary table aligns with exported summary JSON."""
    seed = SEEDS[0]
    out = pipeline(seed, "basic-pit")
    rep = json.loads(out.read_text(encoding="utf-8"))
    con = sqlite3.connect(PARITY_DB)
    row = con.execute(
        "SELECT mismatch_count, ttl_filtered_count, duplicate_ts_resolved FROM parity_summary WHERE run_id = ?",
        (rep["run_id"],),
    ).fetchone()
    con.close()
    assert row[0] == rep["summary"]["mismatch_count"]
    assert row[1] == rep["summary"]["ttl_filtered_count"]
    assert row[2] == rep["summary"]["duplicate_ts_resolved"]


def test_online_offline_rounding_three_decimals():
    """online-offline-parity.md compares values rounded to three decimals."""
    seed = SEEDS[2]
    out = pipeline(seed, "basic-pit")
    rep = json.loads(out.read_text(encoding="utf-8"))
    sc = load_scenario(SCENARIOS / "basic-pit.json", seed)
    ref = reference_validate(sc, sc["ttl_seconds"])
    assert rep["parity_ok"] == ref["parity_ok"]
    assert rep["parity_ok"] is True
    rows = _parity_row_values(seed, "basic-pit")
    assert any(r[3] == pytest.approx(1.2344) and r[4] == pytest.approx(1.2341) and r[5] == 1 for r in rows)


def test_validate_resets_sqlite_between_runs():
    """validate join clears all prior parity tables before inserting a new run."""
    seed = SEEDS[0]
    pipeline(seed, "basic-pit")
    pipeline(seed, "ttl-window")
    con = sqlite3.connect(PARITY_DB)
    n = con.execute("SELECT COUNT(*) FROM parity_runs").fetchone()[0]
    scenarios = {row[0] for row in con.execute("SELECT scenario FROM parity_runs")}
    con.close()
    assert n == 1
    assert scenarios == {"ttl-window"}


def test_agent_image_has_no_hidden_fixtures():
    """Hidden verifier scenarios are not shipped in the agent image."""
    assert not Path("/opt/verifier-fixtures/feast").exists()
    assert HIDDEN.is_dir()
