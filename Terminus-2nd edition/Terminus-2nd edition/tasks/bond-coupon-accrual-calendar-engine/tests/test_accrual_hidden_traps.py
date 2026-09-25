"""Hidden TB3 traps for ex-days override and modified-following calendar."""

from __future__ import annotations

import json
import os

from accr_runner import ATLAS, HIDDEN, flush, pipeline, read_json
from bond_refmath import reference_accrual_row


def test_tb3_ex_days_override_env() -> None:
    """TB3_EX_DAYS env overrides ex-coupon window on hidden ex-days-trap scenario."""
    flush()
    scen = "ex-days-trap"
    os.environ["TB3_EX_DAYS"] = "3"
    try:
        pipeline(scen, fixture_root=HIDDEN, extra_env={"TB3_EX_DAYS": "3"})
        raw = json.loads((HIDDEN / "scenarios" / f"{scen}.json").read_text(encoding="utf-8"))
        bond, trade, cal = raw["bonds"][0], raw["trades"][0], raw["calendars"][0]
        bond = dict(bond)
        bond["ex_days"] = 3
        exp = reference_accrual_row(bond, trade, cal)
        atlas = read_json(ATLAS)
        assert atlas["rows"][0]["accrued_cents"] == exp["accrued_cents"]
    finally:
        os.environ.pop("TB3_EX_DAYS", None)


def test_tb3_modified_following_settlement() -> None:
    """Hidden modified-following-trap scenario settlement matches calendar-adjusted reference."""
    flush()
    scen = "modified-following-trap"
    pipeline(scen, fixture_root=HIDDEN)
    raw = json.loads((HIDDEN / "scenarios" / f"{scen}.json").read_text(encoding="utf-8"))
    bond, trade, cal = raw["bonds"][0], raw["trades"][0], raw["calendars"][0]
    exp = reference_accrual_row(bond, trade, cal)
    atlas = read_json(ATLAS)
    assert atlas["rows"][0]["settlement_date"] == exp["settlement_date"]
