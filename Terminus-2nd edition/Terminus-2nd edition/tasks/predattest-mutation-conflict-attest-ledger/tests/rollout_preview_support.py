"""Shared helpers for the wavehold rollout hold-preview verifier suite.

These helpers drive the installed `wavehold` CLI through its scan -> compile
-> publish stages and recompute the expected rollout atlas with the independent
reference math under /tests.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

APP = Path("/app")
CLI = APP / "bin" / "wavehold"
CONFIG_PATH = APP / "config" / "wavehold.json"
STATE_ROOT = APP / "state" / "wavehold"
RUNS_ROOT = STATE_ROOT / "runs"
WITNESS_PATH = STATE_ROOT / "hold-witness.json"
DEFAULT_ATLAS = APP / "output" / "mutation-rollout-atlas.json"
WAVES_DIR = APP / "fixtures" / "waves"

SUPPORT_DIR = Path(__file__).resolve().parent
MATH_MODULE_PATH = SUPPORT_DIR / "wavehold_math.py"
HIDDEN_DIR = SUPPORT_DIR / "hidden_waves"
PINNED_CONFIG_PATH = SUPPORT_DIR / "pinned_wavehold.json"


def _load_reference_math():
    spec = importlib.util.spec_from_file_location("wavehold_math", MATH_MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


_MATH = _load_reference_math()


def reset_state() -> None:
    subprocess.run(["bash", str(APP / "scripts" / "reset-state.sh")], check=True)


def wave_path(name: str) -> str:
    return str(WAVES_DIR / name)


def _invoke(args: List[str]) -> subprocess.CompletedProcess:
    return subprocess.run([str(CLI), *args], capture_output=True, text=True)


def run_preview(wave: str, run_id: str = "probe", output: Optional[str] = None) -> Dict[str, Any]:
    """Run scan -> compile -> publish and return the published atlas."""
    out = output or str(DEFAULT_ATLAS)
    scan = _invoke(["scan", "--wave", str(wave), "--run-id", run_id])
    assert scan.returncode == 0, f"scan failed: {scan.stderr}"
    comp = _invoke(["compile", "--run-id", run_id])
    assert comp.returncode == 0, f"compile failed: {comp.stderr}"
    pub = _invoke(["publish", "--run-id", run_id, "--output", out])
    assert pub.returncode == 0, f"publish failed: {pub.stderr}"
    with open(out, "r", encoding="utf-8") as f:
        return json.load(f)


def run_scan_rc(wave: str, run_id: str = "rc") -> int:
    return _invoke(["scan", "--wave", str(wave), "--run-id", run_id]).returncode


def invoke_rc(args: List[str]) -> int:
    return _invoke(args).returncode


def reference_atlas(wave: str, config: Optional[str] = None) -> Dict[str, Any]:
    cfg = str(config) if config else str(CONFIG_PATH)
    return _MATH.compile_atlas(cfg, str(wave))


def reference_witness(wave: str, config: Optional[str] = None) -> Dict[str, Any]:
    return _MATH.witness_of(reference_atlas(wave, config))


def read_witness() -> Dict[str, Any]:
    with open(WITNESS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def read_json(path: Path | str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def nodes_by_uid(atlas: Dict[str, Any]) -> Dict[str, Any]:
    return {n["uid"]: n for n in atlas["nodes"]}
