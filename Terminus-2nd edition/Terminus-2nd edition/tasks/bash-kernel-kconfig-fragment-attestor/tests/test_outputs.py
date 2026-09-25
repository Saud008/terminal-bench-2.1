"""Bundled kcfgattest contract tests."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from kcfg_contract_math import (
    apply_deps,
    contract_manifest,
    contract_stage,
    fragment_order,
    manifest_digest,
    merge_layers,
    parse_kconfig,
    scan_policy,
    stage_digest,
    symbol_map,
)
from kcfg_runner import APP, STAGE, CLI, compile_and_emit, wipe

STAGE_SNAPSHOT_PATH = Path("/app/state/kcfg-stage.json")
OUTPUT_ROOT = Path("/app/output")
RUN_ALPHA_MANIFEST = Path("/app/output/run-alpha-manifest.json")

reference_manifest = contract_manifest
reference_stage = contract_stage


BUNDLES = APP / "fixtures" / "bundles"


def _values(manifest: dict) -> dict[str, str]:
    return symbol_map(manifest)


def test_tkcfg7a_q01():
    """Contract symbol values match independent math for minimal-net."""
    wipe()
    out = compile_and_emit("minimal-net", "run-alpha")
    assert out == RUN_ALPHA_MANIFEST
    assert STAGE == STAGE_SNAPSHOT_PATH
    assert STAGE_SNAPSHOT_PATH.is_file()
    assert OUTPUT_ROOT.is_dir()
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_manifest(BUNDLES / "minimal-net", "run-alpha")
    assert _values(rep) == _values(ref)


def test_tkcfg7a_q02():
    """Staging snapshot JSON includes run id, stage_digest, and fragment_order fields."""
    wipe()
    compile_and_emit("minimal-net", "run-bravo")
    stage = json.loads(STAGE.read_text(encoding="utf-8"))
    assert stage["run_id"] == "run-bravo"
    assert "stage_digest" in stage
    assert "fragment_order" in stage
    assert isinstance(stage["after_deps"], dict)


def test_tkcfg7a_q03():
    """CONFIG_NET is enabled after minimal-net merge."""
    wipe()
    out = compile_and_emit("minimal-net", "run-charlie")
    rep = json.loads(out.read_text(encoding="utf-8"))
    assert _values(rep)["CONFIG_NET"] == "y"


def test_tkcfg7a_q04():
    """CONFIG_INET is enabled when inet fragment applies."""
    wipe()
    out = compile_and_emit("minimal-net", "run-delta")
    rep = json.loads(out.read_text(encoding="utf-8"))
    assert _values(rep)["CONFIG_INET"] == "y"


def test_tkcfg7a_q05():
    """CONFIG_PACKET implied when CONFIG_NET enabled."""
    wipe()
    out = compile_and_emit("minimal-net", "run-echo")
    rep = json.loads(out.read_text(encoding="utf-8"))
    assert _values(rep)["CONFIG_PACKET"] == "y"


def test_tkcfg7a_q06():
    """Later fragment wins for CONFIG_FOO in fragment-override bundle."""
    wipe()
    out = compile_and_emit("fragment-override", "run-foxtrot")
    rep = json.loads(out.read_text(encoding="utf-8"))
    assert _values(rep)["CONFIG_FOO"] == "n"
    assert _values(rep)["CONFIG_BAR"] == "y"


def test_tkcfg7a_q07():
    """Fragment order in stage is basename ascending."""
    wipe()
    compile_and_emit("fragment-override", "run-golf")
    stage = json.loads(STAGE.read_text(encoding="utf-8"))
    expected = fragment_order(BUNDLES / "fragment-override" / "fragments")
    assert stage["fragment_order"] == expected


def test_tkcfg7a_q08():
    """Manifest digest stable across rebuild with same run id."""
    wipe()
    out1 = compile_and_emit("minimal-net", "run-alpha")
    d1 = json.loads(out1.read_text())["manifest_digest"]
    wipe()
    out2 = compile_and_emit("minimal-net", "run-alpha")
    d2 = json.loads(out2.read_text())["manifest_digest"]
    assert d1 == d2


def test_tkcfg7a_q09():
    """Stage digest matches contract helper output."""
    wipe()
    compile_and_emit("minimal-net", "run-hotel")
    stage = json.loads(STAGE.read_text(encoding="utf-8"))
    expected = stage_digest(
        stage["run_id"],
        stage["bundle"],
        stage["fragment_order"],
        stage["after_deps"],
    )
    assert stage["stage_digest"] == expected


def test_tkcfg7a_q10():
    """Unset kconfig lines parse as n."""
    syms = parse_kconfig(BUNDLES / "minimal-net" / "defconfig")
    assert syms.get("CONFIG_DEVMEM") == "n"


def test_tkcfg7a_q11():
    """Module-policy keeps CONFIG_BT modular not built-in."""
    wipe()
    out = compile_and_emit("module-policy", "run-india")
    rep = json.loads(out.read_text(encoding="utf-8"))
    assert _values(rep)["CONFIG_BT"] == "m"


def test_tkcfg7a_q12():
    """Forbidden policy flags DEBUG_KERNEL modular assignment."""
    wipe()
    out = compile_and_emit("module-policy", "run-juliet")
    rep = json.loads(out.read_text(encoding="utf-8"))
    codes = {v["symbol"]: v["code"] for v in rep["policy_violations"]}
    assert codes.get("CONFIG_DEBUG_KERNEL") == "forbidden_set"


def test_tkcfg7a_q13():
    """Policy violations sorted by symbol name."""
    wipe()
    out = compile_and_emit("module-policy", "run-kilo")
    rep = json.loads(out.read_text(encoding="utf-8"))
    names = [v["symbol"] for v in rep["policy_violations"]]
    assert names == sorted(names)


def test_tkcfg7a_q14():
    """Manifest symbols sorted by name ascending."""
    wipe()
    out = compile_and_emit("minimal-net", "run-lima")
    rep = json.loads(out.read_text(encoding="utf-8"))
    names = [r["name"] for r in rep["symbols"]]
    assert names == sorted(names)


def test_tkcfg7a_q15():
    """Export manifest reads staging after_deps not raw defconfig ingest files."""
    wipe()
    compile_and_emit("minimal-net", "run-mike")
    stage = json.loads(STAGE.read_text(encoding="utf-8"))
    out = APP / "output" / "run-mike-manifest.json"
    rep = json.loads(out.read_text(encoding="utf-8"))
    assert _values(rep)["CONFIG_INET"] == stage["after_deps"]["CONFIG_INET"]


def test_tkcfg7a_q16():
    """Requires closure promotes CONFIG_NET when INET enabled."""
    wipe()
    compile_and_emit("minimal-net", "run-november")
    stage = json.loads(STAGE.read_text(encoding="utf-8"))
    assert stage["after_deps"]["CONFIG_NET"] == "y"


def test_tkcfg7a_q17():
    """Totals block reports symbol and violation counts."""
    wipe()
    out = compile_and_emit("module-policy", "run-oscar")
    rep = json.loads(out.read_text(encoding="utf-8"))
    assert rep["totals"]["symbols"] == len(rep["symbols"])
    assert rep["totals"]["violations"] == len(rep["policy_violations"])


def test_tkcfg7a_q18():
    """Manifest digest matches hash of emitted symbol rows."""
    wipe()
    out = compile_and_emit("minimal-net", "run-papa")
    rep = json.loads(out.read_text(encoding="utf-8"))
    expected = manifest_digest(rep["symbols"])
    assert rep["manifest_digest"] == expected


def test_tkcfg7a_q19():
    """Contract stage after_deps matches reference merge pipeline."""
    wipe()
    compile_and_emit("fragment-override", "run-quebec")
    stage = json.loads(STAGE.read_text(encoding="utf-8"))
    ref = contract_stage(BUNDLES / "fragment-override", "run-quebec")
    assert stage["after_deps"] == ref["after_deps"]


def test_tkcfg7a_q20():
    """compile-stage exits zero for bundled module-policy via subprocess CLI."""
    wipe()
    proc = subprocess.run(
        [str(CLI), "compile-stage", "--bundle", "module-policy", "--run-id", "run-romeo"],
        cwd=str(APP),
        text=True,
        capture_output=True,
        timeout=120,
    )
    assert proc.returncode == 0, proc.stderr


def test_tkcfg7a_q21():
    """Policy scan detects max_modular when BT would be built-in."""
    bundle = BUNDLES / "module-policy"
    policy = json.loads((bundle / "policy.json").read_text(encoding="utf-8"))
    merged = merge_layers(bundle / "defconfig", bundle / "fragments")
    merged["CONFIG_BT"] = "y"
    violations = scan_policy(merged, policy)
    assert any(v["code"] == "max_modular" for v in violations)


def test_tkcfg7a_q22():
    """Dependency apply promotes implied symbols to y."""
    deps = json.loads((BUNDLES / "minimal-net" / "deps.json").read_text(encoding="utf-8"))
    base = {"CONFIG_NET": "y", "CONFIG_PACKET": "n"}
    out = apply_deps(base, deps)
    assert out["CONFIG_PACKET"] == "y"


def test_tkcfg7a_q23():
    """Raw merged map stored on stage before dependency closure."""
    wipe()
    compile_and_emit("minimal-net", "run-sierra")
    stage = json.loads(STAGE.read_text(encoding="utf-8"))
    assert "raw_merged" in stage
    assert isinstance(stage["raw_merged"], dict)
