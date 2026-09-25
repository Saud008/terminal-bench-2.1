"""Subprocess harness for dbtsent manifest lineage freshness verifier cases."""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

APP_ROOT = Path("/app")
DBTSENT_BIN = Path("/usr/local/bin/dbtsent")
MANIFEST_SNAP = APP_ROOT / "state" / "manifest-checkpoint.json"
SCAN_DB = APP_ROOT / "work" / "freshness-scans.db"
BUNDLE_ROOT = APP_ROOT / "fixtures" / "bundles"
SEED_POOL = json.loads((APP_ROOT / "fixtures" / "seeds.json").read_text(encoding="utf-8"))["seeds"]


@dataclass
class FreshnessSentinelSession:
    """Drive ingest, evaluate, and export through documented dbtsent subcommands."""

    cwd: Path = APP_ROOT

    def _run(self, cmd: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
        merged = os.environ.copy()
        if env:
            merged.update(env)
        return subprocess.run(
            cmd,
            cwd=str(self.cwd),
            capture_output=True,
            text=True,
            check=False,
            env=merged,
        )

    def clear_state(self) -> None:
        proc = self._run(["bash", str(APP_ROOT / "scripts" / "reset-state.sh")])
        assert proc.returncode == 0, proc.stderr or proc.stdout

    def ingest_manifest(self, seed: str, bundle: str, **env: str) -> subprocess.CompletedProcess[str]:
        return self._run([str(DBTSENT_BIN), "ingest", "--seed", seed, "--bundle", bundle], env=env or None)

    def evaluate_freshness(self, seed: str, bundle: str, **env: str) -> subprocess.CompletedProcess[str]:
        return self._run(
            [str(DBTSENT_BIN), "evaluate", "scan", "--seed", seed, "--bundle", bundle],
            env=env or None,
        )

    def export_alerts(self, seed: str, bundle: str, output: Path, **env: str) -> subprocess.CompletedProcess[str]:
        return self._run(
            [
                str(DBTSENT_BIN),
                "export",
                "alerts",
                "--seed",
                seed,
                "--bundle",
                bundle,
                "--output",
                str(output),
            ],
            env=env or None,
        )

    def run_full_sentinel(
        self,
        seed: str,
        bundle: str,
        *,
        bundle_dir: Path | None = None,
        extra_env: dict[str, str] | None = None,
    ) -> Path:
        merged: dict[str, str] = dict(extra_env or {})
        if bundle_dir is not None:
            merged["TB3_BUNDLE_DIR"] = str(bundle_dir)
        for step in (
            self.ingest_manifest(seed, bundle, **merged),
            self.evaluate_freshness(seed, bundle, **merged),
        ):
            assert step.returncode == 0, step.stderr + step.stdout
        report = APP_ROOT / "output" / f"{seed}-{bundle}-freshness-report.json"
        exported = self.export_alerts(seed, bundle, report, **merged)
        assert exported.returncode == 0, exported.stderr + exported.stdout
        return report


SESSION = FreshnessSentinelSession()


def wipe() -> None:
    SESSION.clear_state()
