from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

SPIFFE_BIN = "/app/bin/spiffectl"
SPIFFE_APP = Path("/app")
SPIFFE_RESET = Path("/app/scripts/reset-state.sh")
SPIFFE_CAPTURE = Path("/app/state/pair-capture.json")
SPIFFE_LEFT = Path("/app/state/trust-left-normalized.json")
SPIFFE_RIGHT = Path("/app/state/trust-right-normalized.json")
SPIFFE_SEAL = Path("/app/state/trust-seal-counter.json")
SPIFFE_ATLAS = Path("/app/output/federation-atlas.json")
SPIFFE_FIXTURES = SPIFFE_APP / "fixtures"
SPIFFE_HIDDEN = Path("/opt/verifier-fixtures/spiffectl")

FIXTURE_SCENARIOS = (
    "trust-domain-hostfold",
    "jwks-key-order",
    "x509-serial-normalize",
    "rotation-window",
    "federation-allowlist",
    "stale-identity",
    "stable-diff-pair",
    "repeat-atlas",
)


def run_spiffe_cli(cmd: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        cmd,
        cwd=str(SPIFFE_APP),
        capture_output=True,
        text=True,
        check=False,
        env=merged,
    )


def reset_spiffe_workspace() -> None:
    proc = run_spiffe_cli(["bash", str(SPIFFE_RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def run_spiffe_pipeline(
    scenario: str,
    fixture_root: Path | None = None,
    extra_env: dict | None = None,
) -> None:
    root = fixture_root or SPIFFE_FIXTURES
    env: dict[str, str] = {}
    if fixture_root:
        env["TB3_FIXTURE_DIR"] = str(root)
    if extra_env:
        env.update(extra_env)
    for step in (
        [SPIFFE_BIN, "bind-pair", "--scenario", scenario, "--fixture-dir", str(root)],
        [SPIFFE_BIN, "normalize-trust", "--scenario", scenario],
        [SPIFFE_BIN, "emit-atlas", "--scenario", scenario],
    ):
        proc = run_spiffe_cli(step, env=env or None)
        assert proc.returncode == 0, proc.stderr + proc.stdout


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
