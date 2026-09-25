"""Bundled grantctl output tests."""

from __future__ import annotations

import json
import sqlite3

from cgrst_refmath import reference_atlas
from cgrst_driver import (
    ATLAS_JSON,
    BIN,
    DB_PATH,
    FIXTURE_ROOT,
    PASS_JSON,
    invoke,
    read_atlas,
    run_pipeline,
    subprocess,
    wipe_state,
)


def test_t076943_grant_smoke_load_creates_sqlite() -> None:
    """load-portfolio must create /app/state/grant-portfolio.db with scenario rows."""
    wipe_state()
    proc = invoke([BIN, "load-portfolio", "--scenario", "specificity-rank", "--fixture-dir", str(FIXTURE_ROOT)])
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert DB_PATH.is_file()
    assert DB_PATH.as_posix() == "/app/state/grant-portfolio.db"


def test_t076943_grant_subprocess_cli_contract() -> None:
    """grantctl tests invoke the CLI through subprocess.run helpers."""
    assert subprocess.run is not None
    wipe_state()
    invoke([BIN, "load-portfolio", "--scenario", "staging-gate", "--fixture-dir", str(FIXTURE_ROOT)])
    assert PASS_JSON.as_posix() == "/app/state/amendment-pass.json"
    assert PASS_JSON.is_file()


def test_t076943_grant_load_resets_pass_zero() -> None:
    """load-portfolio must reset amendment_pass to zero in /app/state/amendment-pass.json"""
    wipe_state()
    invoke([BIN, "load-portfolio", "--scenario", "specificity-rank", "--fixture-dir", str(FIXTURE_ROOT)])
    body = json.loads(PASS_JSON.read_text(encoding="utf-8"))
    assert body["amendment_pass"] == 0


def test_t076943_grant_publish_requires_positive_pass() -> None:
    """publish-spend-atlas must fail when /app/state/amendment-pass.json is zero."""
    wipe_state()
    invoke([BIN, "load-portfolio", "--scenario", "staging-gate", "--fixture-dir", str(FIXTURE_ROOT)])
    proc = invoke([BIN, "publish-spend-atlas"])
    assert proc.returncode != 0


def test_t076943_grant_apply_increments_pass() -> None:
    """apply-amendments must increment amendment_pass in /app/state/amendment-pass.json"""
    wipe_state()
    invoke([BIN, "load-portfolio", "--scenario", "staging-gate", "--fixture-dir", str(FIXTURE_ROOT)])
    invoke([BIN, "apply-amendments"])
    body = json.loads(PASS_JSON.read_text(encoding="utf-8"))
    assert body["amendment_pass"] == 1


def test_t076943_grant_export_writes_expected_path() -> None:
    """publish-spend-atlas must write /app/output/spend-atlas.json"""
    wipe_state()
    run_pipeline("staging-gate")
    assert ATLAS_JSON.is_file()
    assert ATLAS_JSON.as_posix() == "/app/output/spend-atlas.json"


def test_t076943_grant_specificity_rank_matches_reference() -> None:
    """specificity-rank atlas must match independent reference math."""
    wipe_state()
    run_pipeline("specificity-rank")
    assert read_atlas() == reference_atlas("specificity-rank", FIXTURE_ROOT)


def test_t076943_grant_future_amendment_respects_effective_date() -> None:
    """future-amendment must honor temporal amendment windows."""
    wipe_state()
    run_pipeline("future-amendment")
    assert read_atlas() == reference_atlas("future-amendment", FIXTURE_ROOT)


def test_t076943_grant_category_rejection_present() -> None:
    """category-reject must emit category_rejected rows in atlas rejections."""
    wipe_state()
    run_pipeline("category-reject")
    assert read_atlas() == reference_atlas("category-reject", FIXTURE_ROOT)


def test_t076943_grant_alias_project_maps_to_canonical() -> None:
    """alias-project must resolve legacy project codes before matching grants."""
    wipe_state()
    run_pipeline("alias-project")
    assert read_atlas() == reference_atlas("alias-project", FIXTURE_ROOT)


def test_t076943_grant_multi_grant_balance_matches_reference() -> None:
    """multi-grant-balance must roll up remaining cents per grant."""
    wipe_state()
    run_pipeline("multi-grant-balance")
    assert read_atlas() == reference_atlas("multi-grant-balance", FIXTURE_ROOT)


def test_t076943_grant_mixed_rejections_match_reference() -> None:
    """mixed-rejections must combine accept and reject rows fairly."""
    wipe_state()
    run_pipeline("mixed-rejections")
    assert read_atlas() == reference_atlas("mixed-rejections", FIXTURE_ROOT)


def test_t076943_grant_staged_balances_row_count() -> None:
    """apply-amendments must populate staged_balances in /app/state/grant-portfolio.db"""
    wipe_state()
    invoke([BIN, "load-portfolio", "--scenario", "multi-grant-balance", "--fixture-dir", str(FIXTURE_ROOT)])
    invoke([BIN, "apply-amendments"])
    con = sqlite3.connect(DB_PATH)
    try:
        count = con.execute("SELECT COUNT(*) FROM staged_balances").fetchone()[0]
    finally:
        con.close()
    assert count == 2


def test_t076943_grant_rejections_table_populated() -> None:
    """apply-amendments must populate staged_rejections for ineligible expenses."""
    wipe_state()
    invoke([BIN, "load-portfolio", "--scenario", "mixed-rejections", "--fixture-dir", str(FIXTURE_ROOT)])
    invoke([BIN, "apply-amendments"])
    con = sqlite3.connect(DB_PATH)
    try:
        count = con.execute("SELECT COUNT(*) FROM staged_rejections").fetchone()[0]
    finally:
        con.close()
    assert count == 1


def test_t076943_grant_publish_contains_digest() -> None:
    """spend-atlas.json must include a 64-char atlas_digest field."""
    wipe_state()
    run_pipeline("staging-gate")
    atlas = read_atlas()
    assert len(atlas["atlas_digest"]) == 64


def test_t076943_grant_empty_rejections_is_array_not_null() -> None:
    """When no expenses are rejected, rejections must be [] not null."""
    wipe_state()
    run_pipeline("staging-gate")
    atlas = read_atlas()
    assert "rejections" in atlas
    assert isinstance(atlas["rejections"], list)
    assert atlas["rejections"] == []
    assert atlas["rejections"] is not None
    raw = ATLAS_JSON.read_text(encoding="utf-8")
    assert '"rejections": null' not in raw
    assert '"rejections": []' in raw or '"rejections":[]' in raw


def test_t076943_grant_amendment_pass_in_output() -> None:
    """spend-atlas.json must echo amendment_pass from the pass gate file."""
    wipe_state()
    run_pipeline("staging-gate")
    assert read_atlas()["amendment_pass"] == 1


def test_t076943_grant_rerun_idempotent_digest() -> None:
    """repeat publish-spend-atlas must keep atlas_digest stable per publish-repeat-guard."""
    wipe_state()
    run_pipeline("rerun-idempotent")
    first = read_atlas()
    proc = invoke([BIN, "publish-spend-atlas"])
    assert proc.returncode == 0
    second = read_atlas()
    assert first["atlas_digest"] == second["atlas_digest"]
