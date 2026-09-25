from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

OIDCGOV_BIN = "/app/bin/oidcgov"
OIDCGOV_APP = Path("/app")
OIDCGOV_RESET = Path("/app/scripts/reset-state.sh")
OIDCGOV_STAGE = Path("/app/state/transcript-vault.json")
OIDCGOV_CACHE = Path("/app/state/jwks-cache-snapshot.json")
OIDCGOV_REV = Path("/app/state/hydrate-revision.json")
OIDCGOV_DEC = Path("/app/state/verification-decisions.json")
OIDCGOV_REPORT = Path("/app/output/verification-governance-report.json")
OIDCGOV_FIXTURES = OIDCGOV_APP / "fixtures"
OIDCGOV_HIDDEN = Path("/opt/verifier-fixtures/oidcgov")

BUNDLED_SCENARIOS = (
    "kid-casefold-lookup",
    "issuer-audience-bind",
    "cache-max-age-expiry",
    "stale-key-grace-window",
    "revoked-key-reject",
    "rollover-timeline-order",
    "stable-decision-batch",
    "repeat-governance-report",
)


def oidcgov_cli(cmd: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(cmd, cwd="/app", capture_output=True, text=True, check=False, env=merged)


def oidcgov_reset_workspace() -> None:
    subprocess.run(["bash", str(OIDCGOV_RESET)], check=True)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def run_oidcgov_pipeline(scenario: str, fixture_dir: Path | None = None) -> None:
    fd = str(fixture_dir or OIDCGOV_FIXTURES)
    for cmd in (
        [OIDCGOV_BIN, "load-transcript", "--scenario", scenario, "--fixture-dir", fd],
        [OIDCGOV_BIN, "hydrate-cache", "--scenario", scenario],
        [OIDCGOV_BIN, "decide-batch", "--scenario", scenario],
        [OIDCGOV_BIN, "emit-report", "--scenario", scenario],
    ):
        proc = oidcgov_cli(cmd)
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr + proc.stdout)
