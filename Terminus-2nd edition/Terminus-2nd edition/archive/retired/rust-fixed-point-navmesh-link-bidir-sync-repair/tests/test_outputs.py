"""Behavioral verifier for navmeshctl validate + path."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from reference_navmesh import load_mesh, reference_path, reference_validate

APP = Path("/app")
CLI = "/usr/local/bin/navmeshctl"
FIXTURES = APP / "fixtures"
MESHES = FIXTURES / "meshes"
OUTPUT = APP / "output"
RESET = APP / "scripts/reset-state.sh"
CATALOG = json.loads((FIXTURES / "catalog.json").read_text(encoding="utf-8"))
MESH_NAMES = [m["name"] for m in CATALOG["meshes"]]
SEEDS = json.loads((FIXTURES / "seeds.json").read_text(encoding="utf-8"))["seeds"]
CATALOG_SEED = SEEDS[0]

PROTECTED = [
    "fixtures/catalog.json",
    "fixtures/seeds.json",
    "fixtures/meshes/fixed-cost.json",
    "fixtures/meshes/q16-return-gate.json",
    "fixtures/meshes/region-mismatch.json",
    "fixtures/meshes/snap-radius.json",
    "fixtures/meshes/island-grid.json",
    "docs/spec.md",
    "docs/mesh-format.md",
    "docs/validate-contract.md",
]


def _sha256(rel: str) -> str:
    return hashlib.sha256((APP / rel).read_bytes()).hexdigest()


PROTECTED_SHA256 = {rel: _sha256(rel) for rel in PROTECTED}


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False)


def reset() -> None:
    proc = run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def mesh_path(name: str) -> Path:
    entry = next(m for m in CATALOG["meshes"] if m["name"] == name)
    return FIXTURES / entry["path"]


def validate_cli(name: str, seed: int) -> dict:
    export = OUTPUT / f"validate-{name}-{seed}.json"
    proc = run(
        [
            CLI,
            "validate",
            "--mesh",
            str(mesh_path(name)),
            "--seed",
            str(seed),
            "--export",
            str(export),
        ]
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    return json.loads(export.read_text(encoding="utf-8"))


def path_cli(name: str, seed: int, frm: str, to: str) -> dict:
    export = OUTPUT / f"path-{name}-{seed}-{frm}-{to}.json"
    proc = run(
        [
            CLI,
            "path",
            "--mesh",
            str(mesh_path(name)),
            "--seed",
            str(seed),
            "--from",
            frm,
            "--to",
            to,
            "--export",
            str(export),
        ]
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    return json.loads(export.read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def _reset_output() -> None:
    reset()


def test_fixture_integrity() -> None:
    """Protected docs and mesh bytes must remain unchanged."""
    for rel, expected in PROTECTED_SHA256.items():
        assert _sha256(rel) == expected


@pytest.mark.parametrize("mesh_name", MESH_NAMES)
def test_validate_matches_reference(mesh_name: str) -> None:
    """Every catalog mesh validate export must match the reference."""
    mesh = load_mesh(mesh_path(mesh_name))
    expected = reference_validate(mesh, CATALOG_SEED)
    got = validate_cli(mesh_name, CATALOG_SEED)
    assert got == expected


@pytest.mark.parametrize("mesh_name", ["fixed-cost", "q16-return-gate", "snap-radius"])
@pytest.mark.parametrize("seed", SEEDS)
def test_path_queries_match_reference(mesh_name: str, seed: int) -> None:
    """Bundled path queries must match the independent reference pathfinder."""
    mesh = load_mesh(mesh_path(mesh_name))
    for query in mesh["path_queries"]:
        expected = reference_path(mesh, seed, query["from"], query["to"])
        got = path_cli(mesh_name, seed, query["from"], query["to"])
        assert got == expected


def test_fixed_cost_q16_total_not_float_truncation() -> None:
    """Path totals must preserve Q16.16 scale across chained edges."""
    seed = SEEDS[1]
    got = path_cli("fixed-cost", seed, "a", "c")
    assert got["status"] == "ok"
    assert got["cost_q16"] > 65536


def test_reverse_portal_path_reachable() -> None:
    """Bidirectional graph edges must allow return paths across the portal gate."""
    seed = SEEDS[0]
    got = path_cli("q16-return-gate", seed, "yard", "west")
    assert got["status"] == "ok"
    assert got["path"][0] == "yard"
    assert got["path"][-1] == "west"


def test_reverse_path_cost_matches_forward_q16() -> None:
    """Forward and reverse queries on the return gate must share the same Q16.16 total."""
    seed = SEEDS[0]
    mesh = load_mesh(mesh_path("q16-return-gate"))
    forward = reference_path(mesh, seed, "west", "yard")
    reverse = reference_path(mesh, seed, "yard", "west")
    got_forward = path_cli("q16-return-gate", seed, "west", "yard")
    got_reverse = path_cli("q16-return-gate", seed, "yard", "west")
    assert got_forward["cost_q16"] == forward["cost_q16"]
    assert got_reverse["cost_q16"] == reverse["cost_q16"]
    assert got_forward["cost_q16"] == got_reverse["cost_q16"]


def test_region_mismatch_fails_validate() -> None:
    """Portals with require_region_match must fail when regions differ."""
    got = validate_cli("region-mismatch", CATALOG_SEED)
    assert got["ok"] is False
    assert any("region mismatch" in err for err in got["errors"])


def test_snap_radius_rejects_far_offmesh() -> None:
    """Linear snap radius must reject off-mesh links beyond threshold."""
    got = validate_cli("snap-radius", CATALOG_SEED)
    assert got["ok"] is False
    assert any("snap radius exceeded" in err for err in got["errors"])


def test_island_grid_four_connected_count() -> None:
    """Island flood fill must use 4-connected adjacency."""
    got = validate_cli("island-grid", CATALOG_SEED)
    assert got["islands"] == 2


@pytest.mark.parametrize("seed", SEEDS)
def test_procedural_seed_validate_and_path(seed: int) -> None:
    """Seed-derived adjacent off-mesh links must validate and path on fixed-cost."""
    mesh = load_mesh(mesh_path("fixed-cost"))
    expected_val = reference_validate(mesh, seed)
    got_val = validate_cli("fixed-cost", seed)
    assert got_val == expected_val
    expected_path = reference_path(mesh, seed, "a", "c")
    got_path = path_cli("fixed-cost", seed, "a", "c")
    assert got_path == expected_path
