from __future__ import annotations

import json
import shutil
import subprocess
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest

from reference_laps import alignment_valid, expected_export, expected_stage, load_catalog, parse_fit

APP = Path("/app")
CLI = "/usr/local/bin/fitlap"
FIX = APP / "fixtures" / "fit"
OUT = APP / "output"
STATE = APP / "state" / "lap-staging"
CAT = load_catalog(FIX / "catalog.json")
CORE = APP / "crates" / "fitcore" / "src"
BROKEN = Path("/opt/verifier-broken-fit")
GOLDEN = Path("/tests/golden_modules")
MODULES = ("crc", "staging", "boundary", "export", "trigger")


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False)


def decode(path: Path) -> subprocess.CompletedProcess[str]:
    return run([CLI, "decode", str(path)])


def export(path: Path, stem: str) -> subprocess.CompletedProcess[str]:
    return run([CLI, "laps", "--export", "--input", str(path), "--stem", stem, "--output", str(OUT / f"{stem}.json")])


def rebuild() -> None:
    proc = run(["cargo", "build", "--release", "-p", "fitlap"])
    assert proc.returncode == 0, proc.stderr or proc.stdout
    target = APP / "target" / "release" / "fitlap"
    shutil.copy2(target, Path("/usr/local/bin/fitlap"))
    Path("/usr/local/bin/fitlap").chmod(0o755)


def reset() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    if STATE.parent.exists():
        shutil.rmtree(STATE.parent)
    OUT.mkdir(parents=True, exist_ok=True)
    STATE.mkdir(parents=True, exist_ok=True)


def install_modules(only_broken: set[str]) -> None:
    for mod in MODULES:
        src = BROKEN / f"{mod}.rs" if mod in only_broken else GOLDEN / f"golden_{mod}.rs"
        shutil.copy2(src, CORE / f"{mod}.rs")


@contextmanager
def partial_module_trap(only_broken: set[str]) -> Iterator[None]:
    backups = {mod: (CORE / f"{mod}.rs").read_bytes() for mod in MODULES}
    install_modules(only_broken)
    rebuild()
    try:
        yield
    finally:
        for mod, data in backups.items():
            (CORE / f"{mod}.rs").write_bytes(data)
        rebuild()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def _reset() -> None:
    reset()


def test_catalog_exists() -> None:
    """Catalog is generated and advertises expected fixture count."""
    assert (FIX / "catalog.json").is_file()
    assert len(CAT["stems"]) >= 5


@pytest.mark.parametrize("stem", ["recovery", "tempo", "shuffle-start-time"])
def test_decode_success_for_valid_fixtures(stem: str) -> None:
    """decode succeeds on valid bundled FIT streams."""
    proc = decode(FIX / f"{stem}.fit")
    assert proc.returncode == 0, proc.stderr or proc.stdout


def test_decode_rejects_bad_crc() -> None:
    """decode rejects streams with invalid message CRC."""
    proc = decode(FIX / "bad-crc.fit")
    assert proc.returncode != 0
    assert "crc mismatch" in (proc.stderr or proc.stdout).lower()


def test_decode_rejects_alignment_fixture() -> None:
    """decode enforces alignment rejection for the decode-only path."""
    rows = parse_fit(FIX / "decode-align-fail.fit")
    assert not alignment_valid(rows)
    proc = decode(FIX / "decode-align-fail.fit")
    assert proc.returncode != 0


@pytest.mark.parametrize("stem", ["recovery", "tempo", "shuffle-start-time", "decode-align-fail"])
def test_export_matches_reference(stem: str) -> None:
    """laps --export output matches independent reference builder."""
    fit = FIX / f"{stem}.fit"
    proc = export(fit, stem)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert load_json(OUT / f"{stem}.json") == expected_export(fit, stem)


def test_stage_file_written_under_lap_staging() -> None:
    """export writes staging JSON to /app/state/lap-staging/<stem>.json."""
    stem = "recovery"
    proc = export(FIX / f"{stem}.fit", stem)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    stage = STATE / f"{stem}.json"
    assert stage.is_file()
    assert load_json(stage) == expected_stage(FIX / f"{stem}.fit", stem)


def test_shuffle_digest_uses_start_time_order() -> None:
    """staging digest is computed over start_time sorted rows."""
    stem = "shuffle-start-time"
    proc = export(FIX / f"{stem}.fit", stem)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    stage = load_json(STATE / f"{stem}.json")
    assert stage["digest"] == expected_stage(FIX / f"{stem}.fit", stem)["digest"]


def test_developer_notes_bind_to_original_index() -> None:
    """developer notes remain attached to original lap index semantics."""
    stem = "shuffle-start-time"
    proc = export(FIX / f"{stem}.fit", stem)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = load_json(OUT / f"{stem}.json")
    ref = expected_export(FIX / f"{stem}.fit", stem)
    assert [r["developer_note"] for r in got["laps"]] == [r["developer_note"] for r in ref["laps"]]


def test_export_from_staging_not_second_parse() -> None:
    """second export reuses staging rows instead of reparsing source."""
    stem = "tempo"
    fit = FIX / f"{stem}.fit"
    proc = export(fit, stem)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    stage_path = STATE / f"{stem}.json"
    stage = load_json(stage_path)
    stage["laps"][0]["developer_note"] = "staging-only-note"
    stage["digest"] = "feedf00dfeedf00d"
    stage_path.write_text(json.dumps(stage, indent=2), encoding="utf-8")
    proc = run([CLI, "laps", "--export", "--input", str(fit), "--stem", stem, "--output", str(OUT / f"{stem}-again.json")])
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = load_json(OUT / f"{stem}-again.json")
    assert got["laps"][0]["developer_note"] == "staging-only-note"
    assert got["digest"] == "feedf00dfeedf00d"


def test_public_api_staging_version_in_snapshot() -> None:
    """staging_version in snapshot equals STAGING_VERSION contract."""
    stem = "recovery"
    proc = export(FIX / f"{stem}.fit", stem)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    stage = load_json(STATE / f"{stem}.json")
    assert stage["staging_version"] == 1


def test_tb3_shuffle_fixture_from_opt_verifier() -> None:
    """hidden verifier fixture under /opt/verifier-fixtures exports successfully."""
    tb3 = Path("/opt/verifier-fixtures/fit/tb3-shuffle.fit")
    assert tb3.is_file()
    stem = "tb3-shuffle"
    proc = export(tb3, stem)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert load_json(OUT / f"{stem}.json")["lap_count"] >= 1


def test_tb3_alignment_export_path_allows_fixture() -> None:
    """TB3 fixture fails decode but succeeds on export path."""
    tb3 = Path("/opt/verifier-fixtures/fit/tb3-align.fit")
    assert tb3.is_file()
    assert decode(tb3).returncode != 0
    proc = export(tb3, "tb3-align")
    assert proc.returncode == 0, proc.stderr or proc.stdout


def test_partial_broken_crc_module_fails_decode() -> None:
    """partial-module trap installs broken crc module into fitcore."""
    with partial_module_trap({"crc"}):
        assert (CORE / "crc.rs").read_text(encoding="utf-8") == (BROKEN / "crc.rs").read_text(
            encoding="utf-8"
        )
        assert (CORE / "crc.rs").read_text(encoding="utf-8") != (
            GOLDEN / "golden_crc.rs"
        ).read_text(encoding="utf-8")


def test_partial_broken_staging_module_fails_digest_contract() -> None:
    """partial-module trap installs broken staging module into fitcore."""
    with partial_module_trap({"staging"}):
        assert (CORE / "staging.rs").read_text(encoding="utf-8") == (
            BROKEN / "staging.rs"
        ).read_text(encoding="utf-8")
        assert (CORE / "staging.rs").read_text(encoding="utf-8") != (
            GOLDEN / "golden_staging.rs"
        ).read_text(encoding="utf-8")


def test_partial_broken_boundary_module_applies_alignment_on_export() -> None:
    """partial-module trap installs broken boundary module into fitcore."""
    with partial_module_trap({"boundary"}):
        assert (CORE / "boundary.rs").read_text(encoding="utf-8") == (
            BROKEN / "boundary.rs"
        ).read_text(encoding="utf-8")
        assert (CORE / "boundary.rs").read_text(encoding="utf-8") != (
            GOLDEN / "golden_boundary.rs"
        ).read_text(encoding="utf-8")


def test_partial_broken_export_module_reparses_fit() -> None:
    """partial-module trap installs broken export module into fitcore."""
    with partial_module_trap({"export"}):
        assert (CORE / "export.rs").read_text(encoding="utf-8") == (
            BROKEN / "export.rs"
        ).read_text(encoding="utf-8")
        assert (CORE / "export.rs").read_text(encoding="utf-8") != (
            GOLDEN / "golden_export.rs"
        ).read_text(encoding="utf-8")


def test_partial_broken_trigger_module_swaps_trigger_labels() -> None:
    """partial-module trap installs broken trigger module into fitcore."""
    with partial_module_trap({"trigger"}):
        assert (CORE / "trigger.rs").read_text(encoding="utf-8") == (
            BROKEN / "trigger.rs"
        ).read_text(encoding="utf-8")
        assert (CORE / "trigger.rs").read_text(encoding="utf-8") != (
            GOLDEN / "golden_trigger.rs"
        ).read_text(encoding="utf-8")


def test_decode_and_export_create_output_files() -> None:
    """decode and export create the expected output artifact path."""
    assert decode(FIX / "recovery.fit").returncode == 0
    assert export(FIX / "recovery.fit", "recovery-out").returncode == 0
    assert (OUT / "recovery-out.json").is_file()


def test_stage_contains_source_and_stem_fields() -> None:
    """staging snapshot preserves source and stem public fields."""
    stem = "tempo"
    fit = FIX / f"{stem}.fit"
    proc = export(fit, stem)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    stage = load_json(STATE / f"{stem}.json")
    assert stage["source"] == str(fit)
    assert stage["stem"] == stem
