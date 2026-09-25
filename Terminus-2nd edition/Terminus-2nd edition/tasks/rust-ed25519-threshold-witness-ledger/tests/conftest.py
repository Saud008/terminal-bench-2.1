"""Shared twctl subprocess harness and path constants."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import pytest
from tw1_independent_math import read_json_stage

TWCTL_BIN = "/app/bin/twctl"
STAGE_PATH = Path("/app/state/tw-approval-stage.json")
ALT_STAGE_PATH = Path("/app/state/alt-tw-approval-stage.json")
VERDICT_PATH = Path("/app/state/quorum-verdict.json")
LEDGER_PATH = Path("/app/output/release-witness-ledger.json")
ALPHA_BUNDLE = Path("/app/data/bundles/release-alpha")
TB3_BUNDLE = Path("/opt/verifier-fixtures/witness-bundles/tb3-bundle")
EDGE_BUNDLE = Path("/opt/verifier-fixtures/witness-bundles/revoke-edge-bundle")


@dataclass
class TwctlRunner:
    """Thin wrapper around twctl subprocess calls."""

    def invoke(self, args: list[str], *, env: dict | None = None, check: bool = True) -> subprocess.CompletedProcess:
        merged = os.environ.copy()
        if env:
            merged.update(env)
        return subprocess.run(
            [TWCTL_BIN, *args],
            check=check,
            capture_output=True,
            text=True,
            env=merged,
        )

    def wipe_outputs(self) -> None:
        for path in (STAGE_PATH, ALT_STAGE_PATH, VERDICT_PATH, LEDGER_PATH):
            if path.exists():
                path.unlink()

    def load_bundle(self, bundle_dir: Path) -> None:
        self.invoke(["load", str(bundle_dir)])

    def check_epoch(
        self,
        epoch: int,
        *,
        staging: Path | str | None = None,
        env: dict | None = None,
    ) -> None:
        args = ["check", "--epoch", str(epoch)]
        if staging is not None:
            args.extend(["--staging", str(staging)])
        self.invoke(args, env=env)

    def emit_ledger(self) -> None:
        self.invoke(["emit"])

    def full_cycle(self, bundle_dir: Path, epoch: int, *, env: dict | None = None) -> None:
        self.wipe_outputs()
        self.load_bundle(bundle_dir)
        self.check_epoch(epoch, env=env)
        self.emit_ledger()


@pytest.fixture
def twctl() -> TwctlRunner:
    runner = TwctlRunner()
    runner.wipe_outputs()
    yield runner
    runner.wipe_outputs()


@pytest.fixture
def stage_reader():
    return read_json_stage


@pytest.fixture
def isolated_bundle():
    """Copy a bundle tree into a temp dir for mutation-safe runs."""
    created: list[Path] = []

    def clone(src: Path) -> Path:
        tmp = Path(tempfile.mkdtemp(prefix="tw-bundle-"))
        shutil.copytree(src, tmp, dirs_exist_ok=True)
        created.append(tmp)
        return tmp

    yield clone
    for path in created:
        shutil.rmtree(path, ignore_errors=True)
