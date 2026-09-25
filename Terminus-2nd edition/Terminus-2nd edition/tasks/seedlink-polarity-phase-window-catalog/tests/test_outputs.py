"""Phase-window calibration catalog verifier — subprocess seedcat CLI with reference closure math."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest
from reference_phase_windows import (
    expected_export,
    expected_stage,
    invariant_ok,
    load_catalog,
    parse_slws,
)

APP = Path("/app")
CLI = "/usr/local/bin/seedcat"
FIX = APP / "fixtures" / "slws"
OUT = APP / "output"
STATE = APP / "state" / "phase-staging"
CAT = load_catalog(FIX / "catalog.json")
CORE = APP / "crates" / "slcore" / "src"
BROKEN = Path("/opt/verifier-broken-slcore")


def _tool_path_env(env: dict[str, str] | None = None) -> dict[str, str]:
    merged = os.environ.copy()
    merged["PATH"] = "/usr/local/cargo/bin:/opt/verifier-venv/bin:/usr/local/bin:" + merged.get(
        "PATH", ""
    )
    if env:
        merged.update(env)
    return merged


def run(cmd: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd, cwd=str(APP), capture_output=True, text=True, check=False, env=_tool_path_env(env)
    )


def decode(path: Path) -> subprocess.CompletedProcess[str]:
    return run([CLI, "decode", str(path)])


def ingest(path: Path, stem: str) -> subprocess.CompletedProcess[str]:
    return run([CLI, "ingest", "--input", str(path), "--stem", stem])


def export(path: Path, stem: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return run(
        [
            CLI,
            "catalog",
            "--export",
            "--input",
            str(path),
            "--stem",
            stem,
            "--output",
            str(OUT / f"{stem}.json"),
        ],
        env=env,
    )


def rebuild() -> None:
    proc = run(["cargo", "build", "--release", "-p", "seedcat"])
    assert proc.returncode == 0, proc.stderr or proc.stdout
    target = APP / "target" / "release" / "seedcat"
    shutil.copy2(target, Path("/usr/local/bin/seedcat"))
    Path("/usr/local/bin/seedcat").chmod(0o755)


def reset() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    if STATE.parent.exists():
        shutil.rmtree(STATE.parent)
    OUT.mkdir(parents=True, exist_ok=True)
    STATE.mkdir(parents=True, exist_ok=True)


@contextmanager
def swap_broken_module(mod: str) -> Iterator[None]:
    """Swap one broken baseline module into the agent's tree, rebuild, then restore."""
    path = CORE / f"{mod}.rs"
    backup = path.read_bytes()
    shutil.copy2(BROKEN / f"{mod}.rs", path)
    rebuild()
    try:
        yield
    finally:
        path.write_bytes(backup)
        rebuild()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def _reset() -> None:
    reset()


def test_catalog_exists() -> None:
    """Catalog is generated and advertises expected fixture count."""
    assert (FIX / "catalog.json").is_file()
    assert len(CAT["stems"]) >= 6


@pytest.mark.parametrize("stem", ["calm-pwave", "leap-edge", "shuffle-picks"])
def test_decode_success_for_valid_fixtures(stem: str) -> None:
    """decode succeeds on valid bundled SLWS snippets."""
    proc = decode(FIX / f"{stem}.slws")
    assert proc.returncode == 0, proc.stderr or proc.stdout


def test_decode_rejects_bad_crc() -> None:
    """decode rejects snippets with invalid CRC."""
    proc = decode(FIX / "bad-crc.slws")
    assert proc.returncode != 0
    assert "crc mismatch" in (proc.stderr or proc.stdout).lower()


def test_decode_rejects_invariant_fixture() -> None:
    """decode enforces pick invariant rejection for duplicate indices."""
    parsed = parse_slws(FIX / "decode-invariant-fail.slws")
    assert not invariant_ok(parsed["picks"], parsed["sample_count"])
    proc = decode(FIX / "decode-invariant-fail.slws")
    assert proc.returncode != 0


@pytest.mark.parametrize(
    "stem",
    ["calm-pwave", "leap-edge", "clip-heavy", "polarity-flip", "shuffle-picks"],
)
def test_export_matches_reference(stem: str) -> None:
    """catalog export JSON matches independent reference closure math."""
    slws = FIX / f"{stem}.slws"
    proc = export(slws, stem)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert load_json(OUT / f"{stem}.json") == expected_export(slws, stem)


def test_ingest_writes_staging_without_export() -> None:
    """ingest subcommand writes staging snapshot without catalog export."""
    stem = "calm-pwave"
    proc = ingest(FIX / f"{stem}.slws", stem)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    stage = STATE / f"{stem}.json"
    assert stage.is_file()
    assert load_json(stage) == expected_stage(FIX / f"{stem}.slws", stem)
    assert not (OUT / f"{stem}.json").exists()


def test_stage_file_written_under_phase_staging() -> None:
    """export writes staging JSON to /app/state/phase-staging/<stem>.json."""
    stem = "calm-pwave"
    proc = export(FIX / f"{stem}.slws", stem)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    stage = STATE / f"{stem}.json"
    assert stage.is_file()
    assert load_json(stage) == expected_stage(FIX / f"{stem}.slws", stem)


def test_staging_digest_numeric_closure_sorted_picks() -> None:
    """staging digest numeric closure uses sample_idx sorted pick order."""
    stem = "shuffle-picks"
    proc = export(FIX / f"{stem}.slws", stem)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    stage = load_json(STATE / f"{stem}.json")
    assert stage["digest"] == expected_stage(FIX / f"{stem}.slws", stem)["digest"]


def test_leap_edge_calibration_closure_matches_reference() -> None:
    """leap-second calibration closure shifts pick center_us within tolerance."""
    stem = "leap-edge"
    proc = export(FIX / f"{stem}.slws", stem)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = load_json(OUT / f"{stem}.json")
    ref = expected_export(FIX / f"{stem}.slws", stem)
    assert got["windows"][0]["center_us"] == ref["windows"][0]["center_us"]


def test_polarity_calibration_sheet_overrides_body_hint() -> None:
    """polarity calibration sheet overrides body hint for effective label."""
    stem = "polarity-flip"
    proc = export(FIX / f"{stem}.slws", stem)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = load_json(OUT / f"{stem}.json")
    ref = expected_export(FIX / f"{stem}.slws", stem)
    assert got["windows"][0]["polarity"] == ref["windows"][0]["polarity"]


def test_clip_heavy_spectral_fraction_within_tolerance() -> None:
    """clip-heavy clipped_fraction spectral mask matches reference tolerance."""
    stem = "clip-heavy"
    proc = export(FIX / f"{stem}.slws", stem)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = load_json(OUT / f"{stem}.json")
    ref = expected_export(FIX / f"{stem}.slws", stem)
    assert got["windows"][0]["clipped_fraction"] == ref["windows"][0]["clipped_fraction"]


def test_export_from_staging_not_second_parse() -> None:
    """second export reuses staging picks instead of reparsing source."""
    stem = "calm-pwave"
    slws = FIX / f"{stem}.slws"
    proc = export(slws, stem)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    stage_path = STATE / f"{stem}.json"
    stage = load_json(stage_path)
    stage["picks"][0]["phase_code"] = 2
    stage["digest"] = "feedf00dfeedf00d"
    stage_path.write_text(json.dumps(stage, indent=2), encoding="utf-8")
    proc = run(
        [
            CLI,
            "catalog",
            "--export",
            "--input",
            str(slws),
            "--stem",
            stem,
            "--output",
            str(OUT / f"{stem}-again.json"),
        ]
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = load_json(OUT / f"{stem}-again.json")
    assert got["windows"][0]["phase"] == "X"
    assert got["digest"] == "feedf00dfeedf00d"


def test_public_api_staging_version_in_snapshot() -> None:
    """staging_version in snapshot equals STAGING_VERSION contract."""
    stem = "calm-pwave"
    proc = export(FIX / f"{stem}.slws", stem)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    stage = load_json(STATE / f"{stem}.json")
    assert stage["staging_version"] == 1


def test_tb3_shuffle_fixture_from_opt_verifier() -> None:
    """hidden verifier fixture under /opt/verifier-fixtures exports successfully."""
    tb3 = Path("/opt/verifier-fixtures/slws/tb3-shuffle.slws")
    assert tb3.is_file()
    stem = "tb3-shuffle"
    proc = export(tb3, stem)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert load_json(OUT / f"{stem}.json")["window_count"] >= 2


def test_tb3_invariant_export_path_allows_fixture() -> None:
    """TB3 duplicate-pick fixture fails decode but succeeds on export path."""
    tb3 = Path("/opt/verifier-fixtures/slws/tb3-invariant-fail.slws")
    assert tb3.is_file()
    assert decode(tb3).returncode != 0
    proc = export(tb3, "tb3-invariant-export")
    assert proc.returncode == 0, proc.stderr or proc.stdout


def test_tb3_leap_hidden_calibration_table() -> None:
    """TB3 leap fixture uses hidden chronology calibration table under /opt."""
    tb3 = Path("/opt/verifier-fixtures/slws/tb3-leap.slws")
    assert tb3.is_file()
    stem = "tb3-leap"
    env = {"TB3_LEAP_ROOT": "/opt/verifier-fixtures/leap"}
    proc = export(tb3, stem, env=env)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    ref = expected_export(
        tb3,
        stem,
        leap_root=Path("/opt/verifier-fixtures/leap"),
    )
    got = load_json(OUT / f"{stem}.json")
    assert got["windows"][0]["center_us"] == ref["windows"][0]["center_us"]


def test_tb3_polarity_hidden_sheet() -> None:
    """TB3 HV network uses hidden polarity sheet."""
    tb3 = Path("/opt/verifier-fixtures/slws/tb3-polarity.slws")
    assert tb3.is_file()
    stem = "tb3-polarity"
    env = {"TB3_POLARITY_ROOT": "/opt/verifier-fixtures/polarity"}
    proc = export(tb3, stem, env=env)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    ref = expected_export(
        tb3,
        stem,
        config_root=Path("/opt/verifier-fixtures/polarity"),
    )
    got = load_json(OUT / f"{stem}.json")
    assert got["windows"][0]["polarity"] == ref["windows"][0]["polarity"]


def test_verifier_alternate_kernel_crc_swapped() -> None:
    """Swapping the broken crc kernel makes valid decode fail."""
    with swap_broken_module("crc"):
        proc = decode(FIX / "calm-pwave.slws")
        assert proc.returncode != 0


def test_verifier_alternate_kernel_leap_swapped() -> None:
    """Swapping the broken leap kernel breaks leap-edge center_us closure."""
    stem = "leap-edge"
    slws = FIX / f"{stem}.slws"
    ref = expected_export(slws, stem)
    with swap_broken_module("leap"):
        proc = export(slws, stem)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = load_json(OUT / f"{stem}.json")
        assert got["windows"][0]["center_us"] != ref["windows"][0]["center_us"]


def test_verifier_alternate_kernel_polarity_swapped() -> None:
    """Swapping the broken polarity kernel ignores the station sheet."""
    stem = "polarity-flip"
    slws = FIX / f"{stem}.slws"
    ref = expected_export(slws, stem)
    with swap_broken_module("polarity"):
        proc = export(slws, stem)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = load_json(OUT / f"{stem}.json")
        assert got["windows"][0]["polarity"] != ref["windows"][0]["polarity"]


def test_verifier_alternate_kernel_digest_swapped() -> None:
    """Swapping the broken digest kernel breaks sample_idx-sorted digest closure."""
    stem = "shuffle-picks"
    slws = FIX / f"{stem}.slws"
    ref_digest = expected_stage(slws, stem)["digest"]
    with swap_broken_module("digest"):
        proc = export(slws, stem)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        stage = load_json(STATE / f"{stem}.json")
        assert stage["digest"] != ref_digest


def test_verifier_alternate_kernel_export_swapped() -> None:
    """Swapping the broken export kernel ignores on-disk staging edits."""
    stem = "calm-pwave"
    slws = FIX / f"{stem}.slws"
    with swap_broken_module("export"):
        proc = export(slws, stem)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        stage_path = STATE / f"{stem}.json"
        stage = load_json(stage_path)
        stage["picks"][0]["phase_code"] = 2
        stage["digest"] = "feedf00dfeedf00d"
        stage_path.write_text(json.dumps(stage, indent=2), encoding="utf-8")
        proc = run(
            [
                CLI,
                "catalog",
                "--export",
                "--input",
                str(slws),
                "--stem",
                stem,
                "--output",
                str(OUT / f"{stem}-again.json"),
            ]
        )
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = load_json(OUT / f"{stem}-again.json")
        assert got["windows"][0]["phase"] != "X" or got["digest"] != "feedf00dfeedf00d"


def test_decode_and_export_create_output_files() -> None:
    """decode and export create the expected output artifact path."""
    assert decode(FIX / "calm-pwave.slws").returncode == 0
    assert export(FIX / "calm-pwave.slws", "calm-out").returncode == 0
    assert (OUT / "calm-out.json").is_file()


def test_stage_contains_source_and_stem_fields() -> None:
    """staging snapshot preserves source and stem public fields."""
    stem = "shuffle-picks"
    slws = FIX / f"{stem}.slws"
    proc = export(slws, stem)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    stage = load_json(STATE / f"{stem}.json")
    assert stage["source"] == str(slws)
    assert stage["stem"] == stem


def test_calm_pwave_phase_window_tolerance_bounds() -> None:
    """P and S phase windows respect pre/post microsecond tolerance bounds."""
    stem = "calm-pwave"
    proc = export(FIX / f"{stem}.slws", stem)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = load_json(OUT / f"{stem}.json")
    ref = expected_export(FIX / f"{stem}.slws", stem)
    for g, r in zip(got["windows"], ref["windows"], strict=True):
        assert g["start_us"] == r["start_us"]
        assert g["end_us"] == r["end_us"]
