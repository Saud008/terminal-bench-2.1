"""Output path contract tests."""

from __future__ import annotations

from cgrst_driver import ATLAS_JSON, BIN, DB_PATH, FIXTURE_ROOT, PASS_JSON, invoke, run_pipeline, wipe_state


def test_cgrst_output_paths_named_in_instruction() -> None:
    """Instruction output paths must exist after the documented grantctl pipeline stages."""
    wipe_state()
    assert DB_PATH.as_posix() == "/app/state/grant-portfolio.db"
    assert PASS_JSON.as_posix() == "/app/state/amendment-pass.json"
    assert ATLAS_JSON.as_posix() == "/app/output/spend-atlas.json"
    invoke([BIN, "load-portfolio", "--scenario", "staging-gate", "--fixture-dir", str(FIXTURE_ROOT)])
    assert DB_PATH.is_file()
    invoke([BIN, "apply-amendments"])
    assert PASS_JSON.is_file()
    run_pipeline("staging-gate")
    assert ATLAS_JSON.is_file()
