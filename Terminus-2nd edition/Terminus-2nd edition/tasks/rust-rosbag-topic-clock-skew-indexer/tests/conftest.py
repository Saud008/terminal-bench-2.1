"""Shared skew-cal verifier harness and workspace reset fixtures."""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

pytest_plugins = [
    "test_c8skew_cli_surface",
    "test_c8skew_manifest_lane",
    "test_c8skew_message_lane",
    "test_c8skew_atlas_emit",
    "test_c8skew_verifier_overlays",
]

APP_ROOT = Path("/app")
SKEW_CAL_BIN = APP_ROOT / "bin" / "skew-cal"
RESET_SCRIPT = APP_ROOT / "scripts" / "reset-workspace.sh"
DEFAULT_BAG_ROOT = APP_ROOT / "fixtures" / "bags"
META_LATCH_DIR = APP_ROOT / "state" / "manifest-latch"
MSG_STAGE = APP_ROOT / "work" / "timeline-ledger"
SYNC_STAGE = APP_ROOT / "work" / "sync-lattice"
OUTPUT_DIR = APP_ROOT / "output"


@dataclass
class C8SkewHarness:
    """Subprocess wrapper for skew-cal CLI stages."""

    app_root: Path = APP_ROOT
    cli: Path = SKEW_CAL_BIN

    def shell(self, cmd: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
        shell_env = os.environ.copy()
        if env:
            shell_env.update(env)
        return subprocess.run(
            cmd,
            cwd=str(self.app_root),
            capture_output=True,
            text=True,
            check=False,
            env=shell_env,
        )

    def reset_workspace(self) -> None:
        proc = self.shell(["bash", str(RESET_SCRIPT)])
        assert proc.returncode == 0, proc.stderr or proc.stdout

    def bag_path(self, bag_id: str, env: dict | None = None) -> Path:
        root = Path(env["TB3_BAG_ROOT"]) if env and env.get("TB3_BAG_ROOT") else DEFAULT_BAG_ROOT
        return root / bag_id

    def run_skew_pipeline(self, bag_id: str, env: dict | None = None) -> Path:
        bdir = self.bag_path(bag_id, env)
        stages = [
            [str(self.cli), "latch-meta", "--bag-id", bag_id, "--meta", str(bdir / "bag_meta.json")],
            [str(self.cli), "norm-stream", "--bag-id", bag_id, "--stream", str(bdir / "messages.jsonl")],
            [str(self.cli), "match-sync", "--bag-id", bag_id],
        ]
        for stage in stages:
            proc = self.shell(stage, env=env)
            assert proc.returncode == 0, proc.stderr + proc.stdout
        out = OUTPUT_DIR / f"{bag_id}-skew-atlas.json"
        proc = self.shell(
            [str(self.cli), "emit-skew", "--bag-id", bag_id, "--output", str(out)],
            env=env,
        )
        assert proc.returncode == 0, proc.stderr + proc.stdout
        return out

    def read_manifest_latch(self, bag_id: str) -> dict:
        return json.loads((META_LATCH_DIR / f"{bag_id}.json").read_text(encoding="utf-8"))

    def read_timeline_ledger_rows(self, bag_id: str) -> list[dict]:
        lines = (MSG_STAGE / f"{bag_id}.jsonl").read_text(encoding="utf-8").splitlines()[1:]
        return [json.loads(ln) for ln in lines]

    def read_sync_header(self, bag_id: str) -> dict:
        return json.loads((SYNC_STAGE / f"{bag_id}.jsonl").read_text(encoding="utf-8").splitlines()[0])


@pytest.fixture
def c8skew() -> C8SkewHarness:
    return C8SkewHarness()


@pytest.fixture(autouse=True)
def isolated_workspace(c8skew: C8SkewHarness):
    c8skew.reset_workspace()
    yield
    c8skew.reset_workspace()
