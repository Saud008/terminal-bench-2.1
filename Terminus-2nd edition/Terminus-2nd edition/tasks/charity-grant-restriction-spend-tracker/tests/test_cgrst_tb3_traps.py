"""Hidden fixture traps via verify-time TB3 fixture directory."""

from __future__ import annotations

from pathlib import Path

from cgrst_refmath import reference_atlas
from cgrst_driver import read_atlas, run_pipeline, wipe_state

TB3_FIXTURE_DIR = "/opt/verifier-fixtures/grantctl"
TESTS_FIXTURE_DIR = Path("/tests/verifier-fixtures/grantctl")


def test_cgrst_tb3_hidden_specificity_alias() -> None:
    """Verify-time fixture combines specificity ranking with alias resolution."""
    wipe_state()
    root = Path(TB3_FIXTURE_DIR)
    run_pipeline("hidden-specificity-alias", fixture_root=root)
    assert read_atlas() == reference_atlas("hidden-specificity-alias", root)


def test_cgrst_tb3_hidden_future_category_gate() -> None:
    """Verify-time fixture enforces temporal windows and category allow-list together."""
    wipe_state()
    root = Path(TB3_FIXTURE_DIR)
    run_pipeline("hidden-future-category", fixture_root=root)
    assert read_atlas() == reference_atlas("hidden-future-category", root)


def test_cgrst_hidden_fixtures_not_baked_into_agent_image() -> None:
    """Hidden grant scenarios ship under /tests and must not be baked into /app."""
    assert TESTS_FIXTURE_DIR.is_dir()
    assert (TESTS_FIXTURE_DIR / "scenarios" / "hidden-specificity-alias.json").is_file()
    assert (TESTS_FIXTURE_DIR / "scenarios" / "hidden-future-category.json").is_file()
    assert not Path("/app/hidden").exists()
    assert not Path("/app/fixtures/scenarios/hidden-specificity-alias.json").exists()
    assert not Path("/app/fixtures/scenarios/hidden-future-category.json").exists()
