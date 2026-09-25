"""Hidden fixture traps and supplemental coverage probes."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from reagentwin_validate import reference_closure
from win_session_cli import SESSION_POOL, run_closure_pipeline, wipe

APP = Path("/app")
TB3_ROOT = Path("/opt/verifier-fixtures/reagentwin")
HIDDEN_LOCAL = Path("/tests/hidden/lab_sessions")


def test_tb3_freezer_spike_hidden_bundle() -> None:
    """TB3 freezer-spike hidden bundle exercises deep excursion integral under verifier fixtures."""
    wipe()
    sid, bundle = SESSION_POOL[0], "tb3-freezer-spike"
    out = run_closure_pipeline(sid, bundle, fixture_dir=TB3_ROOT / "lab_sessions")
    got = json.loads(out.read_text(encoding="utf-8"))
    exp = reference_closure(sid, bundle, TB3_ROOT / "lab_sessions" / f"{bundle}.json")
    assert got["summary"] == exp["summary"]
    assert got["rows"][0]["excursion_minutes"] == 150


def test_tb3_fixture_dir_env_override() -> None:
    """TB3_FIXTURE_DIR must redirect correlate bundle loading to verifier fixture root."""
    wipe()
    sid, bundle = SESSION_POOL[1], "tb3-freezer-spike"
    env = {"TB3_FIXTURE_DIR": str(TB3_ROOT)}
    out = run_closure_pipeline(sid, bundle, env=env)
    assert out.exists()


def test_hidden_alias_poison_bundle_local() -> None:
    """Local tb3-alias-poison trap verifies alias coupling independent of bundled fixtures."""
    wipe()
    sid, bundle = SESSION_POOL[2], "tb3-alias-poison"
    env = {"TB3_FIXTURE_DIR": str(HIDDEN_LOCAL.parent)}
    out = run_closure_pipeline(sid, bundle, env=env)
    rows = json.loads(out.read_text(encoding="utf-8"))["rows"]
    assert rows[0]["excursion_minutes"] > 0


def test_independent_validator_script_runs() -> None:
    """reagentwin_validate.py reference script must run offline and emit closure rows."""
    bundle = APP / "fixtures" / "lab_sessions" / "dual-lot-basic.json"
    proc = subprocess.run(
        ["python3", str(APP / "scripts" / "reagentwin_validate.py"), str(bundle)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    body = json.loads(proc.stdout)
    assert "rows" in body


def test_reset_workspace_clears_correlation() -> None:
    """reset-workspace.sh must clear correlated artifacts before cross-run verifier cases."""
    wipe()
    sid, bundle = SESSION_POOL[0], "dual-lot-basic"
    run_closure_pipeline(sid, bundle)
    wipe()
    assert not list((APP / "work" / "stability-correlation").glob("*.json"))
