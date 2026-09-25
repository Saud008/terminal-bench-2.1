"""Hidden fixture traps for seismocomply."""

from __future__ import annotations

import json

import pytest

from seismocomply_cli_support import BUFFER_PATH, HIDDEN_SURVEYS, run_pipeline, wipe
from seismocomply_contract_math import load_survey, reference_atlas


@pytest.fixture(autouse=True)
def _clean():
    wipe()
    yield
    wipe()


def test_tb3_limit_scale_night_threshold():
    """TB3_LIMIT_SCALE must scale night regulatory thresholds on hidden tb3-night-scale survey."""
    seed = "tb3-scale"
    survey = "tb3-night-scale"
    scale = "0.75"
    out = run_pipeline(
        seed,
        survey,
        fixture_dir=HIDDEN_SURVEYS,
        env={"TB3_LIMIT_SCALE": scale},
    )
    got = json.loads(out.read_text(encoding="utf-8"))
    record = load_survey(HIDDEN_SURVEYS / f"{survey}.json")
    buf = json.loads(BUFFER_PATH.read_text(encoding="utf-8"))
    exp = reference_atlas(seed, survey, record, buf["correlate_seq"], limit_scale=float(scale))
    assert got["exceedance_rows"] == exp["exceedance_rows"]
    assert got["atlas_digest"] == exp["atlas_digest"]


def test_tb3_hidden_survey_night_blast_timestamp():
    """Hidden tb3-night-scale fixture must include a night-hour blast timestamp for limit traps."""
    record = load_survey(HIDDEN_SURVEYS / "tb3-night-scale.json")
    assert "22" in record["blasts"][0]["fired_at"]
