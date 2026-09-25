"""Behavioral verifier for fc-alias-check compile/resolve/check."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from reference_resolver import (
    TB3_CONFIGS,
    expected_stage,
    resolve_request,
)

APP = Path("/app")
CLI = "/usr/local/bin/fc-alias-check"
FIXTURES = APP / "fixtures"
DOCS = APP / "docs"
OUTPUT = APP / "output"
STAGE = Path("/app/state/fc-compiled.json")
COMPILE_SEQ = Path("/app/state/compile-seq.txt")
CATALOG = json.loads((FIXTURES / "catalog.json").read_text(encoding="utf-8"))
SEEDS = CATALOG["seeds"]
RESET = APP / "scripts" / "reset-state.sh"
TB3_DEEP = TB3_CONFIGS / "tb3-deep-chain.conf"

PROTECTED_SHA256: dict[str, str] = {
    "docs/alias-dag.md": "96822998ebbc6b8ceb5122c499fb2a73d6366ff4f1f47b13443f405f49ea94a5",
    "docs/charset-registry.md": "8c2737f79f5bf4223ee0b83727323f358d1e61337422c1a8fe6bf77b868a05f4",
    "docs/cli-reference.md": "e861cdd07f2f3c6332691696087f3ed6862c26d28a75733a9900e494ea1d4928",
    "docs/fixture-catalog.md": "76ef203d647081cd6fbc4e55a1e4e1f9e9403afd8837e38560d515da19c67bb1",
    "docs/font-reject-rules.md": "7b844bb4e6989e7a5f92338413f4eaf88da7169eba34e25a161e3d5613ace27c",
    "docs/staging-compiled.md": "4f79a89a57f89e8981fd46e78513f37efac23ba997a5cc17e0a81ee79ffefc7c",
    "docs/substitute-preferences.md": "eb7e99cdf3ce1d63f1df13fcf1b8e60e7603de963646ab229913d63728fc2320",
    "fixtures/catalog.json": "a4b95055d9b94d4112abd2dc887305ab99af725f8e3a8aeb8d9eb5e6c2ba0bc3",
    "fixtures/configs/base.conf": "baff56c50ccda05c684bdf6b00e4dd7bb0a51983e8dc01acb283c16f1697145b",
    "fixtures/configs/encoding-hop.conf": "a25d16967ce6eadebbe38bb48ace369297231fe1311e62296ad46c559e2aeebc",
    "fixtures/configs/overlay.conf": "de3004b240d6a03df41693a8268194dfb7c538d6077a19f1fc4a66b223c49e1e",
    "fixtures/configs/regression.conf": "3103fa2416d6cb3b24169f5bf8f2fd05bc8d78990560f84261e11f117e3bd153",
    "fixtures/configs/reject-outline.conf": "c5fb7fa2579696b96df1c2162d537082f3924edee95b2cfa62ee2aab0699e6b4",
    "fixtures/configs/revision.conf": "14730c6dd9677004be2d10a66401f3c8061229c35a1f3d31d43307f77d5c6d89",
    "fixtures/fragments/cycle-closer.conf": "165f85c73ae0ece0c00dae73fc203e18286d541e0a54f4cac1587f314216c48f",
    "fixtures/fragments/encoding-override.conf": "99bf0bb3b535d69b8dae334621bd9acab5264ab2e17dfe5208b6c0eec128f7e9",
    "fixtures/fragments/prefer-swap.conf": "5804394c50c47548c35efaba4171293434f45dad4771f57a4457f08b92dae517",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False)


def reset() -> None:
    proc = run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def config_path(rel: str) -> Path:
    return FIXTURES / rel


def ingest_cli(config_rel: str, inject_rel: str | None = None) -> subprocess.CompletedProcess[str]:
    cmd = [CLI, "ingest", "--config", str(config_path(config_rel))]
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
    compile_proc = ingest_cli(config_rel, inject_rel)
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


@pytest.fixture(autouse=True)
def _reset_output() -> None:
    reset()


def test_docs_and_fixtures_integrity() -> None:
    """Protected /app/docs and /app/fixtures trees must remain unmodified."""
    for rel, expect in PROTECTED_SHA256.items():
        path = APP / rel
        assert path.is_file(), rel
        assert sha256_file(path) == expect, f"tampered: {rel}"
    for path in sorted(DOCS.rglob("*")):
        if path.is_file():
            rel = path.relative_to(APP).as_posix()
            assert rel in PROTECTED_SHA256, f"unexpected docs file: {rel}"
    for path in sorted(FIXTURES.rglob("*")):
        if path.is_file():
            rel = path.relative_to(APP).as_posix()
            assert rel in PROTECTED_SHA256, f"unexpected fixtures file: {rel}"


def test_hidden_verifier_fixtures_not_baked_into_agent_image() -> None:
    """Hidden TB3 configs must come from the verifier mount, not the agent image."""
    assert not (APP / "verifier-fixtures").exists()
    assert not (APP / "environment" / "verifier-fixtures").exists()
    tests_src = Path("/tests/verifier-fixtures/fc-configs/tb3-deep-chain.conf")
    assert tests_src.is_file(), "hidden fixtures must ship under /tests, not the agent image"
    assert TB3_DEEP.is_file(), "test.sh must stage hidden fixtures under /opt/verifier-fixtures"


def test_ingest_writes_staging_snapshot() -> None:
    """ingest must write normalized staging at /app/state/fc-compiled.json."""
    proc = ingest_cli("configs/base.conf")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert STAGE.is_file()
    stage = load_stage()
    assert stage["schema"] == "fc-compiled/1"
    assert "compile_meta" in stage


def test_resolve_requires_staging() -> None:
    """resolve without prior ingest must fail with staging missing."""
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


def test_resolve_uses_staging_without_rereading_source_xml() -> None:
    """resolve must read staging only and must not re-parse source XML paths."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        cfg = tmp_path / "ephemeral.conf"
        shutil.copy(config_path("configs/base.conf"), cfg)
        proc = run([CLI, "ingest", "--config", str(cfg)])
        assert proc.returncode == 0, proc.stderr or proc.stdout
        stage_meta = load_stage()["compile_meta"]
        cfg.unlink()
        assert not cfg.exists()
        export_path = OUTPUT / "staging-only-resolve.json"
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
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = json.loads(export_path.read_text(encoding="utf-8"))
        assert got["resolved_terminal"] == "unicode-bmp"
        assert got["alias_chain"] == ["latin-core"]
        assert got["compile_meta"] == stage_meta


def test_compile_seq_increments() -> None:
    """Each ingest bumps compile-seq.txt per staging-compiled.md."""
    ingest_cli("configs/base.conf")
    first = int(COMPILE_SEQ.read_text(encoding="utf-8").strip())
    ingest_cli("configs/base.conf")
    second = int(COMPILE_SEQ.read_text(encoding="utf-8").strip())
    assert second == first + 1


def test_inject_changes_graph_hash() -> None:
    """Inject overlay must change graph_hash when merged config differs."""
    ingest_cli("configs/base.conf")
    base_hash = load_stage()["compile_meta"]["graph_hash"]
    ingest_cli("configs/base.conf", inject_rel="fragments/prefer-swap.conf")
    inject_hash = load_stage()["compile_meta"]["graph_hash"]
    assert base_hash != inject_hash


def test_staging_preserves_charset_declaration_order() -> None:
    """Charset rows must not be sorted by short name before staging."""
    ingest_cli("configs/revision.conf")
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
    proc = run([CLI, "ingest", "--config", str(TB3_DEEP)])
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


def test_verifier_fixtures_deep_chain_prefer_order() -> None:
    """Hidden /opt/verifier-fixtures/fc-configs tree must resolve prefer order."""
    assert TB3_DEEP.is_file()
    proc = run([CLI, "ingest", "--config", str(TB3_DEEP)])
    assert proc.returncode == 0, proc.stderr or proc.stdout
    export_path = OUTPUT / "tb3-prefer.json"
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
    assert got["substitute"]["preferred"] == ["Deep Mono A", "Deep Mono B"]
