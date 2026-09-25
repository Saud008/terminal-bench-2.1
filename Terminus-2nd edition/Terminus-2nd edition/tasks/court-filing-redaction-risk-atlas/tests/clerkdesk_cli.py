from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

CLERK_BIN = "/app/bin/filingatlas"
CLERK_APP = Path("/app")
CLERK_RESET = Path("/app/scripts/reset-state.sh")
CLERK_FINGERPRINT = Path("/app/state/bundle-fingerprint.json")
CLERK_GRAPH = Path("/app/state/party-graph.json")
CLERK_REV = Path("/app/state/index-revision.json")
CLERK_FINDINGS = Path("/app/state/risk-findings.json")
CLERK_ATLAS = Path("/app/output/redaction-risk-atlas.json")
CLERK_FIXTURES = CLERK_APP / "fixtures"
CLERK_HIDDEN = Path("/opt/verifier-fixtures/filingatlas")

CLERK_SCENARIO_IDS = (
    "party-alias-transitive",
    "exhibit-subref-link",
    "sealed-term-hyphen",
    "provenance-page-line",
    "docket-primary-select",
    "party-casefold-match",
    "exhibit-cross-page",
    "stable-atlas-repeat",
)


def clerkdesk_cli(cmd: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    return subprocess.run(cmd, cwd="/app", capture_output=True, text=True, check=False, env=run_env)


def clerkdesk_reset() -> None:
    subprocess.run(["bash", str(CLERK_RESET)], check=True)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def run_clerkdesk_pipeline(scenario: str, fixture_dir: Path | None = None) -> None:
    fd = str(fixture_dir or CLERK_FIXTURES)
    for cmd in (
        [CLERK_BIN, "load-bundle", "--scenario", scenario, "--fixture-dir", fd],
        [CLERK_BIN, "index-parties", "--scenario", scenario],
        [CLERK_BIN, "scan-risks", "--scenario", scenario],
        [CLERK_BIN, "emit-atlas", "--scenario", scenario],
    ):
        proc = clerkdesk_cli(cmd)
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr + proc.stdout)
