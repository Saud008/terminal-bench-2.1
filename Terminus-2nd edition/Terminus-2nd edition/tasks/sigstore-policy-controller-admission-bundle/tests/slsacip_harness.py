"""Harness for slsacip attestation admission verifier suite."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

APP = Path("/app")
SLSACIP_BIN = "/usr/local/bin/slsacip"
CONFIG_PATH = APP / "config" / "slsacip.json"
OUTPUT_DIR = APP / "output"
STATE_DIR = APP / "state" / "slsacip"
WITNESS_PATH = STATE_DIR / "trust-witness.json"
DEFAULT_LEDGER = OUTPUT_DIR / "slsa-admission-ledger.json"

_TESTS_DIR = Path(__file__).resolve().parent
MATH_MODULE_PATH = _TESTS_DIR / "slsacip_batch_math.py"
INCOMPLETE_DIR = _TESTS_DIR / "verifier-incomplete-slsa" / "cipkernel"
LAYERS_DIR = _TESTS_DIR / "verifier-patches" / "layers"
VERIFIER_CONFIG_PATH = Path("/opt/verifier-slsacip/slsacip.json")

LAYER_TARGETS = {
    "layer_rootbind.go": "cipkernel/rootbind/glob.go",
    "layer_quorumadmit.go": "cipkernel/quorumadmit/evaluate.go",
    "layer_witnesswrite.go": "cipkernel/witnesswrite/snapshot.go",
    "layer_sealhex.go": "cipkernel/sealhex/audit.go",
}


def _load_math_module():
    spec = importlib.util.spec_from_file_location("slsacip_batch_math", MATH_MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


_MATH = _load_math_module()


def reset_state() -> None:
    subprocess.run(["bash", str(APP / "scripts" / "reset-state.sh")], check=True)


def go_build() -> None:
    subprocess.run(
        ["go", "build", "-mod=mod", "-o", SLSACIP_BIN, "./cmd/slsacip"],
        cwd=str(APP),
        check=True,
    )


def run_attest(pulls: str, output: Optional[str] = None, config: Optional[str] = None) -> Dict[str, Any]:
    """Run slsacip attest and return the sealed ledger JSON."""
    out_path = Path(output) if output else DEFAULT_LEDGER
    cfg_path = Path(config) if config else CONFIG_PATH
    out_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            SLSACIP_BIN,
            "attest",
            "--config",
            str(cfg_path),
            "--pulls",
            str(pulls),
            "--output",
            str(out_path),
        ],
        check=True,
    )
    with open(out_path, "r", encoding="utf-8") as f:
        return json.load(f)


def reference_report(
    pulls_path: str,
    config_path: Optional[str] = None,
    roots_dir: Optional[str] = None,
    policies_root: Optional[str] = None,
    envelopes_dir: Optional[str] = None,
) -> Dict[str, Any]:
    cfg = str(config_path) if config_path else str(CONFIG_PATH)
    return _MATH.run_batch(
        cfg,
        str(pulls_path),
        roots_dir=roots_dir,
        policies_root=policies_root,
        envelopes_dir=envelopes_dir,
    )


def read_witness_snapshot() -> Dict[str, Any]:
    with open(WITNESS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def fixture_sha256(*parts: str) -> str:
    p = APP.joinpath(*parts)
    return hashlib.sha256(p.read_bytes()).hexdigest()


def swap_layers(layer_names: List[str]) -> None:
    """Restore buggy incomplete baseline, overlay named layers, rebuild."""
    for pkg_dir in sorted(INCOMPLETE_DIR.iterdir()):
        if not pkg_dir.is_dir():
            continue
        for src_file in sorted(pkg_dir.glob("*.go")):
            dst = APP / "cipkernel" / pkg_dir.name / src_file.name
            shutil.copyfile(src_file, dst)

    for name in layer_names:
        if name not in LAYER_TARGETS:
            raise ValueError(f"unknown layer {name!r}")
        src = LAYERS_DIR / name
        dst = APP / LAYER_TARGETS[name]
        shutil.copyfile(src, dst)

    go_build()
