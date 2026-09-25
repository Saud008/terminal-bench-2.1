"""Hemotherapy CLI session driver for bbreleasectl verifier runs."""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class HemotherapyPaths:
    binary: Path = Path("/app/bin/bbreleasectl")
    workspace: Path = Path("/app")
    ledger_json: Path = Path("/app/output/release-ledger.json")
    release_db: Path = Path("/app/state/release.db")
    screening_json: Path = Path("/app/state/screening-pass.json")
    fixture_root: Path = Path("/app/fixtures")
    hidden_root: Path = Path("/opt/verifier-fixtures/bbreleasectl")
    reset_script: Path = Path("/app/scripts/reset-state.sh")


PATHS = HemotherapyPaths()


class HemotherapySession:
    def __init__(self, *, fixture_dir: Path | None = None, extra_env: dict[str, str] | None = None) -> None:
        self.fixture_dir = fixture_dir or PATHS.fixture_root
        self.extra_env = dict(extra_env or {})

    def _env(self) -> dict[str, str]:
        combined_env = os.environ.copy()
        if self.fixture_dir != PATHS.fixture_root:
            combined_env["TB3_FIXTURE_DIR"] = str(self.fixture_dir)
        combined_env.update(self.extra_env)
        return combined_env

    def shell(self, argv: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            argv,
            cwd=str(PATHS.workspace),
            capture_output=True,
            text=True,
            check=False,
            env=self._env(),
        )

    def clear_workspace(self) -> None:
        proc = self.shell(["bash", str(PATHS.reset_script)])
        assert proc.returncode == 0, proc.stderr or proc.stdout

    def import_panels(self, scenario: str) -> None:
        proc = self.shell(
            [
                str(PATHS.binary),
                "import-panels",
                "--scenario",
                scenario,
                "--fixture-dir",
                str(self.fixture_dir),
            ]
        )
        assert proc.returncode == 0, proc.stderr + proc.stdout
        assert PATHS.release_db.is_file()

    def score_compatibility(self, scenario: str) -> None:
        proc = self.shell([str(PATHS.binary), "score-compatibility", "--scenario", scenario])
        assert proc.returncode == 0, proc.stderr + proc.stdout
        assert json.loads(PATHS.screening_json.read_text(encoding="utf-8"))["screening_pass"] >= 1

    def seal_releases(self, scenario: str) -> None:
        proc = self.shell([str(PATHS.binary), "seal-releases", "--scenario", scenario])
        assert proc.returncode == 0, proc.stderr + proc.stdout
        assert json.loads(PATHS.ledger_json.read_text(encoding="utf-8"))["releases"] is not None

    def run_full(self, scenario: str) -> None:
        self.import_panels(scenario)
        self.score_compatibility(scenario)
        self.seal_releases(scenario)

    def read_ledger(self) -> dict:
        return json.loads(PATHS.ledger_json.read_text(encoding="utf-8"))
