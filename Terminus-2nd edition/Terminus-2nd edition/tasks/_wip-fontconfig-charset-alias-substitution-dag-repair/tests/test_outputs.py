"""Behavioral verifier for fc-alias-check compile/resolve/check."""

from __future__ import annotations

import json
import shutil
import subprocess
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest

from reference_resolver import (
    ReferenceCycleError,
    TB3_CONFIGS,
    compile_meta_for,
    expected_stage,
    find_cycle,
    graph_hash,
    load_merged,
    resolve_request,
)

APP = Path("/app")
CLI = "/usr/local/bin/fc-alias-check"
FIXTURES = APP / "fixtures"
OUTPUT = APP / "output"
STAGE = Path("/app/state/fc-compiled.json")
COMPILE_SEQ = Path("/app/state/compile-seq.txt")
CATALOG = json.loads((FIXTURES / "catalog.json").read_text(encoding="utf-8"))
SEEDS = CATALOG["seeds"]
RESET = APP / "scripts" / "reset-state.sh"
CORE = APP / "crates" / "fc-alias-core" / "src"
BROKEN = Path("/opt/verifier-broken-fc")
GOLDEN = Path("/tests/golden_modules")
MODULES = ("parse", "dag", "resolve", "staging")
TB3_DEEP = TB3_CONFIGS / "tb3-deep-chain.conf"


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False)


def rebuild_fc() -> None:
    for mod in MODULES:
        (CORE / f"{mod}.rs").touch()
    proc = run(
        [
            "bash",
            "-lc",
            "export PATH=/usr/local/cargo/bin:/usr/local/bin:$PATH && "
            "export CARGO_NET_OFFLINE=true && "
            "cargo build --locked --release -p fc-alias-check "
            "&& install -m 0755 target/release/fc-alias-check /usr/local/bin/fc-alias-check",
        ]
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout


def restore_broken() -> None:
    for mod in MODULES:
        shutil.copy2(BROKEN / f"{mod}.rs", CORE / f"{mod}.rs")


def install_modules(only_broken: set[str]) -> None:
    for mod in MODULES:
        dest = CORE / f"{mod}.rs"
        if mod in only_broken:
            shutil.copy2(BROKEN / f"{mod}.rs", dest)
        else:
            shutil.copy2(GOLDEN / f"golden_{mod}.rs", dest)


@contextmanager
def partial_module_trap(only_broken: set[str]) -> Iterator[None]:
    install_modules(only_broken)
    rebuild_fc()
    try:
        yield
    finally:
        restore_broken()
        rebuild_fc()


def reset() -> None:
    proc = run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def config_path(rel: str) -> Path:
    return FIXTURES / rel


def compile_cli(config_rel: str, inject_rel: str | None = None) -> subprocess.CompletedProcess[str]:
    cmd = [CLI, "compile", "--config", str(config_path(config_rel))]
    if inject_rel:
        cmd.extend(["--inject", str(config_path(inject_rel))])
    return run(cmd)


def resolve_cli(
    config_rel: str,
    charset: str,
    family: str,
    seed: str,
    inject_rel: str | None = None,
) -> subprocess.CompletedProcess[str]:
    export_path = OUTPUT / f"{Path(config_rel).stem}-{charset.replace(':', '_')}-{seed}.json"
    compile_proc = compile_cli(config_rel, inject_rel)
    if compile_proc.returncode != 0:
        return compile_proc
    cmd = [
        CLI,
        "resolve",
        "--charset",
        charset,
        "--family",
        family,
        "--export",
        str(export_path),
    ]
    return run(cmd)


def load_export(
    config_rel: str, charset: str, seed: str, inject_rel: str | None = None
) -> dict:
    export_path = OUTPUT / f"{Path(config_rel).stem}-{charset.replace(':', '_')}-{seed}.json"
    return json.loads(export_path.read_text(encoding="utf-8"))


def load_stage() -> dict:
    return json.loads(STAGE.read_text(encoding="utf-8"))


def expected_from_stage(charset: str, family: str) -> dict:
    stage = load_stage()
    return resolve_request(stage["config"], charset, family, stage["compile_meta"])


def expected(
    config_rel: str, charset: str, family: str, inject_rel: str | None = None
) -> dict:
    inject = config_path(inject_rel) if inject_rel else None
    cfg = load_merged(config_path(config_rel), inject)
    find_cycle(cfg)
    seq = int(COMPILE_SEQ.read_text(encoding="utf-8").strip() or "1")
    meta = compile_meta_for(cfg, config_path(config_rel), inject, seq)
    return resolve_request(cfg, charset, family, meta)


@pytest.fixture(autouse=True)
def _reset_output() -> None:
    reset()


def test_compile_writes_staging_snapshot() -> None:
    """compile must write normalized staging at /app/state/fc-compiled.json."""
    proc = compile_cli("configs/base.conf")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert STAGE.is_file()
    stage = load_stage()
    assert stage["schema"] == "fc-compiled/1"
    assert "compile_meta" in stage


def test_resolve_requires_staging() -> None:
    """resolve without prior compile must fail with staging missing."""
    export_path = OUTPUT / "no-stage.json"
    proc = run(
        [
            CLI,
            "resolve",
            "--charset",
            "ISO8859-1:1987",
            "--family",
            "serif",
            "--export",
            str(export_path),
        ]
    )
    assert proc.returncode != 0
    assert "staging missing" in (proc.stderr or proc.stdout).lower()


def test_compile_seq_increments() -> None:
    """Each compile bumps compile-seq.txt per staging-compiled.md."""
    compile_cli("configs/base.conf")
    first = int(COMPILE_SEQ.read_text(encoding="utf-8").strip())
    compile_cli("configs/base.conf")
    second = int(COMPILE_SEQ.read_text(encoding="utf-8").strip())
    assert second == first + 1


def test_inject_changes_graph_hash() -> None:
    """Inject overlay must change graph_hash when merged config differs."""
    compile_cli("configs/base.conf")
    base_hash = load_stage()["compile_meta"]["graph_hash"]
    compile_cli("configs/base.conf", inject_rel="fragments/prefer-swap.conf")
    inject_hash = load_stage()["compile_meta"]["graph_hash"]
    assert base_hash != inject_hash


def test_staging_preserves_charset_declaration_order() -> None:
    """Charset rows must not be sorted by short name before staging."""
    compile_cli("configs/revision.conf")
    stage = load_stage()
    names = [cs["name"] for cs in stage["config"]["charsets"]]
    ref = expected_stage(config_path("configs/revision.conf"))
    assert names == [cs["name"] for cs in ref["config"]["charsets"]]


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("scenario", CATALOG["scenarios"], ids=lambda s: s["name"])
def test_catalog_resolve_matches_reference(scenario: dict, seed: str) -> None:
    """Every catalog scenario must match the independent reference."""
    proc = resolve_cli(scenario["config"], scenario["charset"], scenario["family"], seed)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert load_export(scenario["config"], scenario["charset"], seed) == expected_from_stage(
        scenario["charset"], scenario["family"]
    )


@pytest.mark.parametrize("seed", SEEDS[:1])
@pytest.mark.parametrize("scenario", CATALOG["inject_scenarios"], ids=lambda s: s["name"])
def test_inject_resolve_matches_reference(scenario: dict, seed: str) -> None:
    """Inject overlays must merge before resolution."""
    proc = resolve_cli(
        scenario["base"],
        scenario["charset"],
        scenario["family"],
        seed,
        inject_rel=scenario["inject"],
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert load_export(
        scenario["base"], scenario["charset"], seed, inject_rel=scenario["inject"]
    ) == expected_from_stage(scenario["charset"], scenario["family"])


def test_overlay_cycle_exits_two() -> None:
    """Alias cycles in overlay.conf must make check exit with code 2."""
    cycle_path = config_path(CATALOG["cycle_config"])
    proc = run([CLI, "check", "--config", str(cycle_path)])
    assert proc.returncode == 2, proc.stderr or proc.stdout
    assert "alias cycle detected" in (proc.stderr or proc.stdout)


def test_inject_cycle_exits_two() -> None:
    """Injected fragment must participate in cycle detection."""
    base = config_path(CATALOG["cycle_inject_base"])
    fragment = config_path(CATALOG["cycle_inject_fragment"])
    proc = run([CLI, "check", "--config", str(base), "--inject", str(fragment)])
    assert proc.returncode == 2, proc.stderr or proc.stdout


def test_alias_chain_multi_hop() -> None:
    """latin-core must expand through unicode-bmp terminal."""
    seed = SEEDS[0]
    proc = resolve_cli("configs/base.conf", "ISO8859-1:1987", "serif", seed)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = load_export("configs/base.conf", "ISO8859-1:1987", seed)
    assert got["alias_chain"] == ["latin-core"]
    assert got["resolved_terminal"] == "unicode-bmp"
    assert got["encoding"] == "utf-8"


def test_prefer_order_preserved() -> None:
    """First prefer entry must remain highest priority."""
    seed = SEEDS[0]
    proc = resolve_cli("configs/base.conf", "ISO8859-1:1987", "serif", seed)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = load_export("configs/base.conf", "ISO8859-1:1987", seed)
    assert got["substitute"]["preferred"][0] == "DejaVu Serif"
    assert got["substitute"]["preferred"][-1] == "FreeSerif"


def test_duplicate_short_charset_distinct() -> None:
    """ISO8859-1:1987 and ISO8859-1:1998 must remain distinct registry entries."""
    seed = SEEDS[0]
    for charset, local_enc in (
        ("ISO8859-1:1987", "8859-1"),
        ("ISO8859-1:1998", "8859-1-rev2"),
    ):
        proc = resolve_cli("configs/revision.conf", charset, "mono", seed)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = load_export("configs/revision.conf", charset, seed)
        assert got["charset"]["name"] == charset
        assert got["charset"]["encoding"] == local_enc


def test_encoding_propagates_from_terminal() -> None:
    """Resolved encoding must come from terminal charset, not query node."""
    seed = SEEDS[0]
    proc = resolve_cli("configs/encoding-hop.conf", "ISO8859-4:1988", "serif", seed)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = load_export("configs/encoding-hop.conf", "ISO8859-4:1988", seed)
    assert got["encoding"] == "utf-16le"
    assert got["charset"]["encoding"] == "8859-4"


def test_reject_outline_independent() -> None:
    """reject-outline alone must still allow outline fonts."""
    seed = SEEDS[0]
    proc = resolve_cli("configs/reject-outline.conf", "ASCII:1963", "sans", seed)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = load_export("configs/reject-outline.conf", "ASCII:1963", seed)
    assert got["reject_bitmap"] is False
    assert got["reject_outline"] is True
    assert got["font_kinds_allowed"] == ["bitmap"]


def test_regression_both_rejects_empty_kinds() -> None:
    """Both reject tags must yield empty font_kinds_allowed."""
    seed = SEEDS[0]
    proc = resolve_cli("configs/regression.conf", "UNICODE:2024", "serif", seed)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = load_export("configs/regression.conf", "UNICODE:2024", seed)
    assert got["font_kinds_allowed"] == []
    assert got["alias_chain"] == ["latin-core", "regression-terminal"]


def test_tb3_deep_alias_chain_four_hops() -> None:
    """Hidden TB3 config requires full multi-hop expansion."""
    assert TB3_DEEP.is_file(), "TB3 fixture missing"
    proc = run([CLI, "compile", "--config", str(TB3_DEEP)])
    assert proc.returncode == 0, proc.stderr or proc.stdout
    export_path = OUTPUT / "tb3-deep.json"
    proc = run(
        [
            CLI,
            "resolve",
            "--charset",
            "DEEP:2026",
            "--family",
            "mono",
            "--export",
            str(export_path),
        ]
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = json.loads(export_path.read_text(encoding="utf-8"))
    assert got["alias_chain"] == ["hop1", "hop2", "hop3", "hop4"]
    assert got["resolved_terminal"] == "deep-terminal"
    assert got["encoding"] == "utf-8-deep"


def test_reference_independent_of_cli() -> None:
    """Reference must resolve fixtures without invoking fc-alias-check."""
    cfg = load_merged(config_path("configs/base.conf"))
    doc = resolve_request(
        cfg, "ISO8859-2:1987", "sans", compile_meta_for(cfg, config_path("configs/base.conf"), None)
    )
    assert doc["resolved_terminal"] == "unicode-bmp"


def test_reference_detects_alias_cycle() -> None:
    """Reference find_cycle must raise on overlay.conf."""
    cfg = load_merged(config_path(CATALOG["cycle_config"]))
    with pytest.raises(ReferenceCycleError):
        find_cycle(cfg)


def test_reference_graph_hash_matches_staging_contract() -> None:
    """Reference graph_hash must match golden staging digest contract."""
    cfg = load_merged(config_path("configs/base.conf"))
    base = config_path("configs/base.conf")
    ref_hash = graph_hash(cfg, base, None)
    compile_cli("configs/base.conf")
    assert load_stage()["compile_meta"]["graph_hash"] == ref_hash


def test_partial_broken_dag_fails_cycle_check() -> None:
    """Golden parse/resolve cannot mask missing alias cycle detection."""
    with partial_module_trap({"dag"}):
        proc = run([CLI, "check", "--config", str(config_path(CATALOG["cycle_config"]))])
        assert proc.returncode != 2


def test_partial_broken_parse_fails_duplicate_short() -> None:
    """Golden dag/resolve cannot mask charset merge by short name."""
    with partial_module_trap({"parse"}):
        seed = SEEDS[0]
        proc1987 = resolve_cli("configs/revision.conf", "ISO8859-1:1987", "mono", seed)
        assert proc1987.returncode != 0
        proc1998 = resolve_cli("configs/revision.conf", "ISO8859-1:1998", "mono", seed)
        assert proc1998.returncode == 0, proc1998.stderr or proc1998.stdout
        ref1987 = expected("configs/revision.conf", "ISO8859-1:1987", "mono")
        assert ref1987["charset"]["name"] == "ISO8859-1:1987"


def test_partial_broken_resolve_fails_prefer_order() -> None:
    """Correct parse/dag cannot mask reversed prefer list."""
    with partial_module_trap({"resolve"}):
        seed = SEEDS[0]
        proc = resolve_cli("configs/base.conf", "ISO8859-1:1987", "serif", seed)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = load_export("configs/base.conf", "ISO8859-1:1987", seed)
        assert got["substitute"]["preferred"] != expected_from_stage(
            "ISO8859-1:1987", "serif"
        )["substitute"]["preferred"]


def test_partial_broken_dag_fails_multi_hop() -> None:
    """Golden parse/resolve cannot mask single-hop alias expansion."""
    with partial_module_trap({"dag"}):
        seed = SEEDS[0]
        cfg = load_merged(config_path("configs/regression.conf"))
        golden = resolve_request(
            cfg,
            "UNICODE:2024",
            "serif",
            compile_meta_for(cfg, config_path("configs/regression.conf"), None),
        )
        proc = resolve_cli("configs/regression.conf", "UNICODE:2024", "serif", seed)
        if proc.returncode == 0:
            got = load_export("configs/regression.conf", "UNICODE:2024", seed)
            assert got["alias_chain"] != golden["alias_chain"]
        else:
            assert len(golden["alias_chain"]) > 1


def test_partial_broken_resolve_fails_reject_outline() -> None:
    """Correct parse/dag cannot mask conflated bitmap/outline rejection."""
    with partial_module_trap({"resolve"}):
        seed = SEEDS[0]
        proc = resolve_cli("configs/reject-outline.conf", "ASCII:1963", "sans", seed)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = load_export("configs/reject-outline.conf", "ASCII:1963", seed)
        assert got["font_kinds_allowed"] != ["bitmap"]


def test_partial_broken_staging_fails_inject_graph_hash() -> None:
    """Golden parse/dag/resolve cannot mask inject-blind graph_hash."""
    with partial_module_trap({"staging"}):
        compile_cli("configs/base.conf")
        base_hash = load_stage()["compile_meta"]["graph_hash"]
        compile_cli("configs/base.conf", inject_rel="fragments/prefer-swap.conf")
        inject_hash = load_stage()["compile_meta"]["graph_hash"]
        assert base_hash == inject_hash


def test_partial_broken_staging_fails_charset_order() -> None:
    """Golden core modules cannot mask charset sort before staging."""
    with partial_module_trap({"staging"}):
        compile_cli("configs/revision.conf")
        names = [cs["name"] for cs in load_stage()["config"]["charsets"]]
        ref = expected_stage(config_path("configs/revision.conf"))
        assert names != [cs["name"] for cs in ref["config"]["charsets"]]
