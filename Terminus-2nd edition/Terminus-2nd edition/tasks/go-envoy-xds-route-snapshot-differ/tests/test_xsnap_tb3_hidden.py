"""TB3 hidden fixture traps for xsnapctl."""

from __future__ import annotations

import os

from xsnap_refmath import read_json, reference_diff_report
from xsnap_session import XSNAP_BIN, XSNAP_OUT, XSNAP_TB3, invoke_xsnap, reset_xsnap_workspace


def test_xsnapctl_tb3_precedence_bias_hidden() -> None:
    """Hidden precedence-bias scenario diff matches xsnap_refmath."""
    reset_xsnap_workspace()
    env = {"TB3_FIXTURE_DIR": str(XSNAP_TB3)}
    invoke_xsnap(
        [XSNAP_BIN, "ingest-pair", "--scenario", "precedence-bias", "--fixture-dir", str(XSNAP_TB3)], env=env
    )
    invoke_xsnap([XSNAP_BIN, "canonicalize", "--scenario", "precedence-bias"], env=env)
    invoke_xsnap([XSNAP_BIN, "publish-diff", "--scenario", "precedence-bias"], env=env)
    assert read_json(XSNAP_OUT)["changes"] == reference_diff_report("precedence-bias", XSNAP_TB3)["changes"]


def test_xsnapctl_tb3_weight_env_trap() -> None:
    """Hidden weight-trap honors TB3_WEIGHT_SCALE during normalize."""
    reset_xsnap_workspace()
    env = {"TB3_FIXTURE_DIR": str(XSNAP_TB3), "TB3_WEIGHT_SCALE": "200"}
    invoke_xsnap([XSNAP_BIN, "ingest-pair", "--scenario", "weight-trap", "--fixture-dir", str(XSNAP_TB3)], env=env)
    invoke_xsnap([XSNAP_BIN, "canonicalize", "--scenario", "weight-trap"], env=env)
    prev = os.environ.get("TB3_WEIGHT_SCALE")
    os.environ["TB3_WEIGHT_SCALE"] = "200"
    try:
        ref = reference_diff_report("weight-trap", XSNAP_TB3)
    finally:
        if prev is None:
            os.environ.pop("TB3_WEIGHT_SCALE", None)
        else:
            os.environ["TB3_WEIGHT_SCALE"] = prev
    invoke_xsnap([XSNAP_BIN, "publish-diff", "--scenario", "weight-trap"], env=env)
    assert read_json(XSNAP_OUT)["report_digest"] == ref["report_digest"]
