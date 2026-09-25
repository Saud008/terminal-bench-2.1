"""Hidden fixture traps and supplemental coverage probes."""

from __future__ import annotations

import json
from pathlib import Path

from rf_atlas_cli_support import SEED_POOL, run_pipeline, wipe
from rf_atlas_contract_math import expected_after_first_compile

APP = Path("/app")
TB3_ROOT = Path("/opt/verifier-fixtures/rflicat")
HIDDEN_LOCAL = Path("/tests/hidden/bundles")


def test_tb3_coastal_overlay_hidden_bundle() -> None:
    """TB3 coastal overlay bundle must exclude bluff site per hidden fixture contract."""
    wipe()
    seed, bundle = SEED_POOL[0], "tb3-coastal-overlay"
    fixture_root = TB3_ROOT
    out = run_pipeline(seed, bundle, fixture_dir=fixture_root / "bundles")
    got = json.loads(out.read_text(encoding="utf-8"))
    exp = expected_after_first_compile(seed, bundle, fixture_root / "bundles" / f"{bundle}.json")
    assert got["summary"] == exp["summary"]
    bluff = next(r for r in got["catalog_rows"] if r["site_id"] == "tx-bluff")
    assert bluff["excluded"] is True


def test_tb3_fixture_dir_env_override() -> None:
    """TB3_FIXTURE_DIR env override must redirect bundle loading for render-atlas."""
    wipe()
    seed, bundle = SEED_POOL[1], "tb3-coastal-overlay"
    env = {"TB3_FIXTURE_DIR": str(TB3_ROOT)}
    out = run_pipeline(seed, bundle, env=env)
    assert out.exists()


def test_hidden_priority_invert_bundle_local() -> None:
    """Hidden priority-invert bundle must pick lic-high when priorities invert."""
    wipe()
    seed, bundle = SEED_POOL[2], "tb3-priority-invert"
    env = {"TB3_FIXTURE_DIR": str(HIDDEN_LOCAL.parent)}
    out = run_pipeline(seed, bundle, env=env)
    rows = json.loads(out.read_text(encoding="utf-8"))["catalog_rows"]
    site = next(r for r in rows if r["site_id"] == "tx-tower")
    assert site["license_id"] == "lic-high"
    assert site["holder"] == "HighPriority Co"


def test_independent_validator_script_runs() -> None:
    """rf_grant_math.py must run standalone and emit catalog_rows for anti-cheat."""
    bundle = Path("/opt/rflicat-bundles/bundles/metro-dual-grant.json")
    import subprocess

    proc = subprocess.run(
        ["python3", str(APP / "scripts" / "rf_grant_math.py"), str(bundle)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    body = json.loads(proc.stdout)
    assert "catalog_rows" in body


def test_reset_state_clears_work_dirs() -> None:
    """Wipe helper must clear WAL and work state between independent test runs."""
    wipe()
    seed, bundle = SEED_POOL[0], "metro-dual-grant"
    run_pipeline(seed, bundle)
    wipe()
    assert not (APP / "state" / "rf-grant-wal.json").exists()
