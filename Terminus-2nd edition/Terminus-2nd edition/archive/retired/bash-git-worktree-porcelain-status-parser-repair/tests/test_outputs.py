"""Behavioral verifier for wtstatus-export porcelain parser repair."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

import pytest

from reference_porcelain import (
    PAIR_POOL,
    generate_fixture_bytes,
    reference_export,
    scenario_porcelain_path,
)

APP = Path("/app")
CLI = "/app/bin/wtstatus-export"
CONFIG = APP / "config/export.json"
FIXTURES = APP / "fixtures"
OUTPUT = APP / "output"
GEN = APP / "scripts/gen_porcelain_fixture.sh"
CATALOG = json.loads((FIXTURES / "catalog.json").read_text(encoding="utf-8"))
SEEDS = json.loads((FIXTURES / "seeds.json").read_text(encoding="utf-8"))["seeds"]
RESET = APP / "scripts/reset-state.sh"

PROTECTED_SHA256 = {
    "fixtures/catalog.json": "46cc92fad39fd46876426dbdc77a6c4eb14336716904eb4f0aa7b8adabc11b69",
    "fixtures/seeds.json": "d0d52efc377a74f5e5dbcedf7f2d5ebcf8774496638533f84fa7d93dc63e4aed",
    "config/export.json": "f3249880be8a3f69db2fc2d80cebf70ccf739f3cd2fcf73552ea2666420b516b",
    "fixtures/porcelain/nul-paths.bin": "04326e55349e0db7a61466b618a0aabf8467002566152ac1b1e776a305d7993b",
    "fixtures/porcelain/submodule-gitlink.bin": "ad65845dd55471674fc0de18dfff27979ab50205652e62c008ca52d5a6bb4cfd",
}


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False)


def reset() -> None:
    proc = run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def parse_cli(porcelain: Path, export_path: Path) -> subprocess.CompletedProcess[str]:
    return run(
        [
            CLI,
            "parse",
            "--porcelain",
            str(porcelain),
            "--config",
            str(CONFIG),
            "--export",
            str(export_path),
        ]
    )


def load_export(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def _reset_output() -> None:
    reset()


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("scenario_name", [s["name"] for s in CATALOG["scenarios"]])
def test_catalog_parse_matches_reference(scenario_name: str, seed: str) -> None:
    """Every catalog scenario must match the independent reference export."""
    with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
        porcelain = scenario_porcelain_path(scenario_name, seed, Path(tmp))
        expected = reference_export(str(porcelain), str(CONFIG))
        export_path = OUTPUT / f"{scenario_name}-{seed}.json"
        proc = parse_cli(porcelain, export_path)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = load_export(export_path)
        assert got == expected


def test_rename_pair_not_split_into_two_ordinary() -> None:
    """Tag 2 rename records must export as one rename/copy entry, not two ordinary paths."""
    seed = SEEDS[0]
    with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
        porcelain = scenario_porcelain_path("rename-threshold", seed, Path(tmp))
        expected = reference_export(str(porcelain), str(CONFIG))
        rename_entries = [e for e in expected["entries"] if e["kind"] in {"rename", "copy"}]
        assert rename_entries
        proc = parse_cli(porcelain, OUTPUT / "rename-check.json")
        assert proc.returncode == 0
        got = load_export(OUTPUT / "rename-check.json")
        got_renames = [e for e in got["entries"] if e["kind"] in {"rename", "copy"}]
        assert len(got_renames) == len(rename_entries)
        assert {e["path"] for e in got_renames} == {e["path"] for e in rename_entries}


def test_uu_unmerged_not_ordinary() -> None:
    """UU unmerged conflicts must not be exported as ordinary modifications."""
    seed = SEEDS[1]
    with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
        porcelain = scenario_porcelain_path("unmerged-matrix", seed, Path(tmp))
        expected = reference_export(str(porcelain), str(CONFIG))
        uu = next(e for e in expected["entries"] if e.get("unmerged_xy") == "UU")
        assert uu["kind"] == "unmerged"
        proc = parse_cli(porcelain, OUTPUT / "unmerged-check.json")
        assert proc.returncode == 0
        got = load_export(OUTPUT / "unmerged-check.json")
        got_uu = next(e for e in got["entries"] if e["path"] == uu["path"])
        assert got_uu["kind"] == "unmerged"
        assert got_uu.get("unmerged_xy") == "UU"


def test_nul_delimited_paths_with_spaces() -> None:
    """Static NUL stream with spaced paths must parse without line splitting."""
    porcelain = FIXTURES / "porcelain/nul-paths.bin"
    expected = reference_export(str(porcelain), str(CONFIG))
    assert any(" " in e["path"] for e in expected["entries"])
    proc = parse_cli(porcelain, OUTPUT / "nul-paths.json")
    assert proc.returncode == 0
    got = load_export(OUTPUT / "nul-paths.json")
    assert got == expected


def test_submodule_gitlink_modes() -> None:
    """Mode 160000 on any stage must set submodule true."""
    porcelain = FIXTURES / "porcelain/submodule-gitlink.bin"
    expected = reference_export(str(porcelain), str(CONFIG))
    assert all(e["submodule"] for e in expected["entries"])
    proc = parse_cli(porcelain, OUTPUT / "submodule.json")
    assert proc.returncode == 0
    got = load_export(OUTPUT / "submodule.json")
    assert got == expected


def test_rename_score_threshold_inclusive() -> None:
    """Scores equal to rename_score_min must be kept; lower scores omitted."""
    records: list[str] = []
    for letter, score, new_path, old_path in PAIR_POOL:
        xy = "R." if letter == "R" else "C."
        records.append(
            f"2 {xy} N 100644 100644 100644 abc def {letter}{score} {new_path}\t{old_path}"
        )
    porcelain = OUTPUT / "threshold-edge.bin"
    porcelain.write_bytes(("\0".join(records) + "\0").encode("utf-8"))
    expected = reference_export(str(porcelain), str(CONFIG))
    expected_scores = {e["score"] for e in expected["entries"] if "score" in e}
    assert expected_scores == {50, 62, 88}
    assert 49 not in expected_scores
    proc = parse_cli(porcelain, OUTPUT / "threshold.json")
    assert proc.returncode == 0
    got = load_export(OUTPUT / "threshold.json")
    got_scores = {e["score"] for e in got["entries"] if "score" in e}
    assert got_scores == expected_scores


def test_parse_is_idempotent() -> None:
    """Repeated parse on the same porcelain stream must yield identical export JSON."""
    porcelain = FIXTURES / "porcelain/nul-paths.bin"
    first = OUTPUT / "idempotent-first.json"
    second = OUTPUT / "idempotent-second.json"
    proc1 = parse_cli(porcelain, first)
    proc2 = parse_cli(porcelain, second)
    assert proc1.returncode == 0, proc1.stderr or proc1.stdout
    assert proc2.returncode == 0, proc2.stderr or proc2.stdout
    assert load_export(first) == load_export(second)


def test_generator_script_matches_reference() -> None:
    """Fixture generator must emit the same bytes as the reference generator."""
    seed = SEEDS[3]
    with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
        tmp_path = Path(tmp)
        out_b = tmp_path / "gen.bin"
        ref_bytes = generate_fixture_bytes("mixed-worktree", seed)
        proc = run(
            [
                "bash",
                str(GEN),
                "--scenario",
                "mixed-worktree",
                "--seed",
                seed,
                "--output",
                str(out_b),
            ]
        )
        assert proc.returncode == 0, proc.stderr or proc.stdout
        assert out_b.read_bytes() == ref_bytes


def test_protected_fixtures_unchanged() -> None:
    """Protected catalog/config/fixture metadata must not be edited by agents."""
    for rel, expected in PROTECTED_SHA256.items():
        path = APP / rel
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest == expected, rel
