"""Hidden kcfgattest trap tests."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from kcfg_contract_math import contract_manifest, symbol_map
from kcfg_runner import APP, STAGE, compile_and_emit, wipe


def _overlay(bundle: str) -> Path:
    tmp = APP / "work" / "tb3-root"
    if tmp.exists():
        shutil.rmtree(tmp)
    src = Path("/opt/verifier-fixtures/kcfg/bundles") / bundle
    dst_root = tmp
    dst_root.mkdir(parents=True)
    shutil.copytree(src, dst_root / bundle)
    return dst_root


def test_tkcfg7a_q24():
    """Hidden overlay from /opt/verifier-fixtures/kcfg/bundles selects CRC32."""
    wipe()
    root = _overlay("tb3-imply-trap")
    bundle_dir = root / "tb3-imply-trap"
    out = compile_and_emit("tb3-imply-trap", "run-hidden", bundle_root=root)
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = contract_manifest(bundle_dir, "run-hidden")
    assert symbol_map(rep) == symbol_map(ref)
    assert symbol_map(rep)["CONFIG_CRC32"] == "y"


def test_tkcfg7a_q25():
    """TB3 overlay from /opt/verifier-fixtures/kcfg preserves BLOCK requirement for EXT4."""
    wipe()
    root = _overlay("tb3-imply-trap")
    compile_and_emit("tb3-imply-trap", "run-h2", bundle_root=root)
    stage = json.loads(STAGE.read_text(encoding="utf-8"))
    assert stage["after_deps"]["CONFIG_BLOCK"] == "y"
    assert stage["after_deps"]["CONFIG_EXT4_FS"] == "y"
