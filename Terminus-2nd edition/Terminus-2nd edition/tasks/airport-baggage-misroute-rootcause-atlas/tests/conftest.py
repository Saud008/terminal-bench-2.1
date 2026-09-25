"""Bag-atlas subprocess harness — reset workspace and run pipeline stages."""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

APP = Path("/app")
CLI = APP / "bin" / "bag-atlas"
HUB_LATCH = APP / "state" / "hub-latch"
SCAN_LEDGER = APP / "work" / "scan-ledger"
ROUTE_LATTICE = APP / "work" / "route-lattice"
OUTPUT = APP / "output"
FIXTURE_HUBS = APP / "fixtures" / "hubs"


@dataclass(frozen=True)
class MisrouteHarness:
    """Run bag-atlas CLI stages against bundled or TB3 hub fixtures."""

    def run(self, cmd: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        run_env = os.environ.copy()
        if env:
            run_env.update(env)
        return subprocess.run(
            cmd,
            cwd=str(APP),
            capture_output=True,
            text=True,
            check=False,
            env=run_env,
        )

    def reset(self) -> None:
        proc = self.run(["bash", str(APP / "scripts" / "reset-workspace.sh")])
        assert proc.returncode == 0, proc.stderr or proc.stdout

    def hub_dir(self, hub_id: str, env: dict[str, str] | None = None) -> Path:
        root = Path(env["TB3_HUB_ROOT"]) if env and "TB3_HUB_ROOT" in env else FIXTURE_HUBS
        return root / hub_id

    def latch(self, hub_id: str, env: dict[str, str] | None = None) -> None:
        topo = self.hub_dir(hub_id, env) / "hub_topology.json"
        proc = self.run(
            [str(CLI), "hub-latch", "--hub-id", hub_id, "--topology", str(topo)],
            env=env,
        )
        assert proc.returncode == 0, proc.stderr + proc.stdout

    def full_pipeline(self, hub_id: str, env: dict[str, str] | None = None) -> Path:
        hdir = self.hub_dir(hub_id, env)
        self.latch(hub_id, env)
        for stage in (
            [str(CLI), "seq-scans", "--hub-id", hub_id, "--stream", str(hdir / "scans.jsonl")],
            [str(CLI), "route-belts", "--hub-id", hub_id],
        ):
            proc = self.run(stage, env=env)
            assert proc.returncode == 0, proc.stderr + proc.stdout
        atlas = OUTPUT / f"{hub_id}-rootcause-atlas.json"
        proc = self.run(
            [str(CLI), "emit-rootcause", "--hub-id", hub_id, "--output", str(atlas)],
            env=env,
        )
        assert proc.returncode == 0, proc.stderr + proc.stdout
        return atlas

    def latch_doc(self, hub_id: str) -> dict:
        return json.loads((HUB_LATCH / f"{hub_id}.json").read_text(encoding="utf-8"))

    def scan_rows(self, hub_id: str) -> list[dict]:
        body = (SCAN_LEDGER / f"{hub_id}.jsonl").read_text(encoding="utf-8").splitlines()[1:]
        return [json.loads(line) for line in body]

    def route_rows(self, hub_id: str) -> list[dict]:
        body = (ROUTE_LATTICE / f"{hub_id}.jsonl").read_text(encoding="utf-8").splitlines()[1:]
        return [json.loads(line) for line in body]


@pytest.fixture
def misroute_harness() -> MisrouteHarness:
    return MisrouteHarness()


@pytest.fixture(autouse=True)
def _clean_workspace(misroute_harness: MisrouteHarness):
    misroute_harness.reset()
    yield
    misroute_harness.reset()
