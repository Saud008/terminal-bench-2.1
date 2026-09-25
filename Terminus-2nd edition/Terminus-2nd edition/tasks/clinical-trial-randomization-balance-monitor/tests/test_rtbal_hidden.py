"""Hidden TB3 fixture traps for rtbalctl."""

from __future__ import annotations

from rtbal_helpers import HIDDEN, pipeline, read_json, reset
from rtbal_refmath import reference_pipeline


class TestHiddenTraps:
    def test_tb3_site_cap_hidden_fixture(self) -> None:
        """Hidden tb3-cap-override fixture must honor stricter site caps via TB3_FIXTURE_DIR."""
        assert HIDDEN.is_dir()
        reset()
        out = pipeline("tb3-cap-override", root=HIDDEN)
        closure = read_json(out)
        ref = reference_pipeline(HIDDEN, "tb3-cap-override")["closure"]
        assert closure["venues_at_cap"] == ref["venues_at_cap"]

    def test_tb3_withdraw_skew_hidden_fixture(self) -> None:
        """Hidden tb3-withdraw-skew fixture must exclude withdrawals from active balance skew."""
        reset()
        out = pipeline("tb3-withdraw-skew", root=HIDDEN)
        closure = read_json(out)
        ref = reference_pipeline(HIDDEN, "tb3-withdraw-skew")["closure"]
        assert closure["max_skew"] == ref["max_skew"]
        assert closure["per_stratum"] == ref["per_stratum"]

    def test_tb3_fixture_dir_env_override(self) -> None:
        """TB3_FIXTURE_DIR must redirect fixture roots without changing protocol digest math."""
        reset()
        ref = reference_pipeline(HIDDEN, "tb3-cap-override")["closure"]
        out = pipeline("tb3-cap-override", root=HIDDEN)
        closure = read_json(out)
        assert closure["protocol_digest"] == ref["protocol_digest"]
