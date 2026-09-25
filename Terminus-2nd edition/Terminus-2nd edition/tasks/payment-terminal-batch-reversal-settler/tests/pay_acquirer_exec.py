from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

TERMSET_BIN = "/app/bin/termsetctl"
APP_ROOT = Path("/app")
STATE_RESET = Path("/app/scripts/reset-state.sh")
PATH_JOURNAL = Path("/app/state/batch-journal.jsonl")
PATH_META = Path("/app/state/journal-meta.json")
PATH_BUNDLE = Path("/app/output/settlement-bundle.json")
PATH_WITNESS = Path("/app/output/settlement-witness.hmac")
BUNDLED_FIXTURES = APP_ROOT / "fixtures"
OVERLAY_FIXTURES = Path("/opt/verifier-fixtures/termsetctl")

SCEN_CLEAN = "clean-settle"
SCEN_REVERSAL = "reversal-pair"
SCEN_CUTOFF = "cutoff-window"
SCEN_SEQ = "seq-strict"
SCEN_MULTI = "multi-merchant"
SCEN_STALE = "stale-reversal"
SCEN_REPUBLISH = "hmac-republish"


def exec_termsetctl(argv: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        argv,
        cwd=str(APP_ROOT),
        capture_output=True,
        text=True,
        check=False,
        env=merged,
    )


def flush_batch_state() -> None:
    proc = exec_termsetctl(["bash", str(STATE_RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def run_settle_pipeline(
    scenario: str,
    fixture_root: Path | None = None,
    extra_env: dict | None = None,
) -> None:
    root = fixture_root or BUNDLED_FIXTURES
    env: dict[str, str] = {}
    if fixture_root is not None:
        env["TB3_FIXTURE_DIR"] = str(root)
    if extra_env:
        env.update(extra_env)
    for argv in (
        [TERMSET_BIN, "compile-journal", "--scenario", scenario, "--fixture-dir", str(root)],
        [TERMSET_BIN, "seal-bundle", "--scenario", scenario, "--fixture-dir", str(root)],
    ):
        proc = exec_termsetctl(argv, env=env or None)
        assert proc.returncode == 0, proc.stderr + proc.stdout


def read_json_object(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl_rows(path: Path) -> list[dict]:
    rows: list[dict] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if raw.strip():
            rows.append(json.loads(raw))
    return rows
