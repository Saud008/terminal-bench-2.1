"""Behavioral checks for bondacc bond accrual pipeline."""

from __future__ import annotations

import json
import sqlite3
import string

from accr_runner import ACCRCTL, ATLAS, DB, FIX, PASS, SCEN_EOM, SCEN_EX, SCEN_HOL, SCEN_MULTI, SCEN_PLAIN, SCEN_30360, flush, pipeline, read_json
from bond_refmath import atlas_digest, reference_accrual_row


def _load_scenario(name: str) -> tuple[dict, dict, dict]:
    raw = json.loads((FIX / "scenarios" / f"{name}.json").read_text(encoding="utf-8"))
    bond = raw["bonds"][0]
    trade = raw["trades"][0]
    cal = raw["calendars"][0]
    return bond, trade, cal


def test_seed_schedules_creates_db() -> None:
    """seed-schedules materializes bond rows into /app/state/accrual.db."""
    flush()
    pipeline(SCEN_PLAIN)
    assert DB.as_posix() == "/app/state/accrual.db"
    assert DB.is_file()
    conn = sqlite3.connect(DB)
    try:
        n = conn.execute("SELECT COUNT(*) FROM bonds").fetchone()[0]
        assert n >= 1
    finally:
        conn.close()


def test_accrual_pass_gate_advances() -> None:
    """Full pipeline advances accrual_pass in /app/state/accrual-pass.json to at least 2."""
    flush()
    pipeline(SCEN_PLAIN)
    assert PASS.as_posix() == "/app/state/accrual-pass.json"
    meta = read_json(PASS)
    assert meta["accrual_pass"] >= 2


def test_atlas_written_to_output_path() -> None:
    """publish-atlas writes /app/output/accrual-atlas.json when accrual_pass gate passes."""
    flush()
    pipeline(SCEN_PLAIN)
    assert ATLAS.as_posix() == "/app/output/accrual-atlas.json"
    assert ATLAS.is_file()


def test_atlas_engine_field() -> None:
    """Atlas JSON records engine bondacc per accrual-atlas-layout contract."""
    flush()
    pipeline(SCEN_PLAIN)
    atlas = read_json(ATLAS)
    assert atlas["engine"] == "bondacc"


def test_act360_accrued_matches_reference() -> None:
    """ACT/360 accrued cents match independent bond_refmath for plain-act360 scenario."""
    flush()
    pipeline(SCEN_PLAIN)
    bond, trade, cal = _load_scenario(SCEN_PLAIN)
    exp = reference_accrual_row(bond, trade, cal)
    atlas = read_json(ATLAS)
    row = atlas["rows"][0]
    assert row["accrued_cents"] == exp["accrued_cents"]


def test_settlement_date_uses_business_days() -> None:
    """Settlement date skips holidays per trade-settlement-lag contract."""
    flush()
    pipeline(SCEN_HOL)
    bond, trade, cal = _load_scenario(SCEN_HOL)
    exp = reference_accrual_row(bond, trade, cal)
    atlas = read_json(ATLAS)
    assert atlas["rows"][0]["settlement_date"] == exp["settlement_date"]


def test_thirt360_convention_fraction() -> None:
    """30/360 US day-count accrued interest matches reference math."""
    flush()
    pipeline(SCEN_30360)
    bond, trade, cal = _load_scenario(SCEN_30360)
    exp = reference_accrual_row(bond, trade, cal)
    atlas = read_json(ATLAS)
    assert atlas["rows"][0]["accrued_cents"] == exp["accrued_cents"]


def test_ex_coupon_zeroes_accrued() -> None:
    """Trades inside ex-coupon window publish zero accrued cents to buyer."""
    flush()
    pipeline(SCEN_EX)
    atlas = read_json(ATLAS)
    assert atlas["rows"][0]["ex_coupon"] is True
    assert atlas["rows"][0]["accrued_cents"] == 0


def test_atlas_digest_lowercase_hex() -> None:
    """atlas_digest is lowercase hex per atlas-digest-stability contract."""
    flush()
    pipeline(SCEN_PLAIN)
    digest = read_json(ATLAS)["atlas_digest"]
    assert digest == digest.lower()
    assert all(c in string.hexdigits.lower() for c in digest)


def test_atlas_digest_matches_row_payload() -> None:
    """atlas_digest recomputes from normalized row JSON excluding metadata fields."""
    flush()
    pipeline(SCEN_PLAIN)
    atlas = read_json(ATLAS)
    want = atlas_digest(atlas["rows"])
    assert atlas["atlas_digest"] == want


def test_rows_sorted_by_trade_id() -> None:
    """Atlas rows are sorted by trade_id before digest and publish."""
    flush()
    pipeline(SCEN_MULTI)
    rows = read_json(ATLAS)["rows"]
    ids = [r["trade_id"] for r in rows]
    assert ids == sorted(ids)


def test_multi_isin_row_count() -> None:
    """Multi-bond scenario produces one accrual row per trade ticket."""
    flush()
    pipeline(SCEN_MULTI)
    atlas = read_json(ATLAS)
    assert len(atlas["rows"]) >= 2


def test_eom_coupon_schedule_reflected() -> None:
    """End-of-month issue dates yield aligned coupon period_end in accrual rows."""
    flush()
    pipeline(SCEN_EOM)
    bond, trade, cal = _load_scenario(SCEN_EOM)
    exp = reference_accrual_row(bond, trade, cal)
    atlas = read_json(ATLAS)
    assert atlas["rows"][0]["period_end"] == exp["period_end"]


def test_period_start_before_settlement() -> None:
    """Accrual period_start precedes settlement_date for active coupon periods."""
    flush()
    pipeline(SCEN_PLAIN)
    row = read_json(ATLAS)["rows"][0]
    assert row["period_start"] < row["settlement_date"]


def test_accrual_positive_when_not_ex() -> None:
    """Non-ex-coupon trades accrue positive interest through settlement date."""
    flush()
    pipeline(SCEN_PLAIN)
    row = read_json(ATLAS)["rows"][0]
    assert row["accrued_cents"] > 0


def test_sqlite_accrual_row_persisted() -> None:
    """run-accrual persists accrued_cents into accruals table inside accrual.db."""
    flush()
    pipeline(SCEN_PLAIN)
    conn = sqlite3.connect(DB)
    try:
        cur = conn.execute("SELECT accrued_cents FROM accruals LIMIT 1").fetchone()
        assert cur is not None
        assert cur[0] > 0
    finally:
        conn.close()


def test_publish_blocked_without_accrual_pass() -> None:
    """publish-atlas rejects when accrual_pass gate has not reached accrual stage."""
    flush()
    from accr_runner import run

    root = str(FIX)
    for step in (
        [ACCRCTL, "seed-schedules", "--scenario", SCEN_PLAIN, "--fixture-dir", root],
        [ACCRCTL, "apply-trades", "--scenario", SCEN_PLAIN, "--fixture-dir", root],
    ):
        proc = run(step)
        assert proc.returncode == 0
    proc = run([ACCRCTL, "publish-atlas", "--scenario", SCEN_PLAIN, "--fixture-dir", root])
    assert proc.returncode != 0


def test_decoy_couponcard_not_in_atlas() -> None:
    """Decoy couponcard preview module is not referenced in published atlas JSON."""
    flush()
    pipeline(SCEN_PLAIN)
    raw = ATLAS.read_text(encoding="utf-8")
    assert "couponcard" not in raw


def test_scenario_echoed_in_atlas() -> None:
    """Published atlas echoes scenario slug for traceability."""
    flush()
    pipeline(SCEN_PLAIN)
    assert read_json(ATLAS)["scenario"] == SCEN_PLAIN


def test_trade_id_stable_across_runs() -> None:
    """Deterministic fixtures yield stable trade_id values across reset cycles."""
    flush()
    pipeline(SCEN_PLAIN)
    first = read_json(ATLAS)["rows"][0]["trade_id"]
    flush()
    pipeline(SCEN_PLAIN)
    second = read_json(ATLAS)["rows"][0]["trade_id"]
    assert first == second
