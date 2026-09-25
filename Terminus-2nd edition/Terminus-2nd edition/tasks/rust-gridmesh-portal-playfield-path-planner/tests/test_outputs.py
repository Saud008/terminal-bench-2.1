"""Behavioral verifier for playfield path planner validate + path exports.

Verifiers assert playfield-staging snapshot rows after ingest validate and path export.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest

from reference_navmesh import load_mesh, reference_path, reference_validate

APP = Path("/app")
CLI = "/usr/local/bin/navmeshctl"
FIXTURES = APP / "fixtures"
MESHES = FIXTURES / "meshes"
OUTPUT = APP / "output"
STAGING = APP / "state" / "playfield-staging"
RESET = APP / "scripts/reset-state.sh"
CATALOG = json.loads((FIXTURES / "catalog.json").read_text(encoding="utf-8"))
MESH_NAMES = [m["name"] for m in CATALOG["meshes"]]
SEEDS = json.loads((FIXTURES / "seeds.json").read_text(encoding="utf-8"))["seeds"]
CATALOG_SEED = SEEDS[0]
HIDDEN_MESHES = Path("/opt/verifier-fixtures/playmesh/meshes")

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
    "docs/playfield-board-catalog.md",
]


def _sha256(rel: str) -> str:
    return hashlib.sha256((APP / rel).read_bytes()).hexdigest()


PROTECTED_SHA256 = {rel: _sha256(rel) for rel in PROTECTED}


def run(cmd: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False, env=merged)


def reset() -> None:
    proc = run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def mesh_path(name: str, env: dict[str, str] | None = None) -> Path:
    if env and env.get("TB3_MESH_DIR"):
        return Path(env["TB3_MESH_DIR"]) / f"{name}.json"
    entry = next(m for m in CATALOG["meshes"] if m["name"] == name)
    return FIXTURES / entry["path"]


def validate_cli(name: str, seed: int, env: dict[str, str] | None = None) -> dict:
    export = OUTPUT / f"validate-{name}-{seed}.json"
    proc = run(
        [
            CLI,
            "validate",
            "--mesh",
            str(mesh_path(name, env)),
            "--seed",
            str(seed),
            "--export",
            str(export),
        ],
        env=env,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    return json.loads(export.read_text(encoding="utf-8"))


def path_cli(name: str, seed: int, frm: str, to: str, env: dict[str, str] | None = None) -> dict:
    export = OUTPUT / f"path-{name}-{seed}-{frm}-{to}.json"
    proc = run(
        [
            CLI,
            "path",
            "--mesh",
            str(mesh_path(name, env)),
            "--seed",
            str(seed),
            "--from",
            frm,
            "--to",
            to,
            "--export",
            str(export),
        ],
        env=env,
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


def test_staging_snapshot_after_validate() -> None:
    """validate writes a playfield-staging snapshot under /app/state/playfield-staging/."""
    seed = CATALOG_SEED
    validate_cli("fixed-cost", seed)
    snap_path = STAGING / f"fixed-cost-{seed}.json"
    assert snap_path.is_file()
    snap = json.loads(snap_path.read_text(encoding="utf-8"))
    assert snap["mesh_id"] == "fixed-cost"
    assert snap["seed"] == seed
    assert snap["cell_count"] == 3


def test_staging_snapshot_after_path() -> None:
    """path also persists the staging snapshot before sealing the route export."""
    seed = SEEDS[1]
    path_cli("fixed-cost", seed, "a", "c")
    snap_path = STAGING / f"fixed-cost-{seed}.json"
    assert snap_path.is_file()
    snap = json.loads(snap_path.read_text(encoding="utf-8"))
    assert snap["edge_count"] == 2


def test_scout_decoy_module_exists_off_hot_path() -> None:
    """scout_decoy exists but is not imported by navmeshctl main."""
    decoy = APP / "scout_decoy" / "astar.rs"
    assert decoy.is_file()
    text = decoy.read_text(encoding="utf-8")
    assert "float_edge_weight" in text
    main = (APP / "crates" / "navmeshctl" / "src" / "main.rs").read_text(encoding="utf-8")
    assert "scout_decoy" not in main


def test_tb3_mesh_dir_overlay_diagonal_trap() -> None:
    """TB3_MESH_DIR overlay loads tb3-diagonal-trap and matches 4-connected island count."""
    env = {"TB3_MESH_DIR": str(HIDDEN_MESHES)}
    path = mesh_path("tb3-diagonal-trap", env)
    assert path.exists()
    mesh = load_mesh(path)
    expected = reference_validate(mesh, CATALOG_SEED)
    got = validate_cli("tb3-diagonal-trap", CATALOG_SEED, env=env)
    assert got == expected
    assert got["islands"] == 2


def test_tb3_portal_pin_region_reject() -> None:
    """Hidden /opt/verifier-fixtures tb3-portal-pin rejects mismatched portal regions."""
    env = {"TB3_MESH_DIR": str(HIDDEN_MESHES)}
    path = mesh_path("tb3-portal-pin", env)
    assert path.exists()
    mesh = load_mesh(path)
    expected = reference_validate(mesh, CATALOG_SEED)
    got = validate_cli("tb3-portal-pin", CATALOG_SEED, env=env)
    assert got == expected
    assert got["ok"] is False
    assert any("region mismatch" in err for err in got["errors"])


def test_unreachable_path_status() -> None:
    """Disconnected island cells must report unreachable without inventing a route."""
    seed = CATALOG_SEED
    got = path_cli("island-grid", seed, "c00", "c22")
    assert got["status"] == "unreachable"
    assert got["path"] == []


def test_validate_idempotent_replay() -> None:
    """Two validate runs on unchanged inputs must seal identical exports and staging."""
    seed = CATALOG_SEED
    first = validate_cli("fixed-cost", seed)
    snap1 = json.loads((STAGING / f"fixed-cost-{seed}.json").read_text(encoding="utf-8"))
    second = validate_cli("fixed-cost", seed)
    snap2 = json.loads((STAGING / f"fixed-cost-{seed}.json").read_text(encoding="utf-8"))
    assert first == second
    assert snap1 == snap2


def test_path_export_field_shape() -> None:
    """Path export must expose status, cost_q16, and ordered path cells."""
    got = path_cli("fixed-cost", CATALOG_SEED, "a", "c")
    assert set(got.keys()) >= {"status", "cost_q16", "path"}
    assert isinstance(got["cost_q16"], int)
    assert isinstance(got["path"], list)


def test_links_checked_positive_on_fixed_cost() -> None:
    """Seed-driven validate must count at least one checked link on fixed-cost."""
    got = validate_cli("fixed-cost", SEEDS[2] if len(SEEDS) > 2 else SEEDS[0])
    assert got["links_checked"] >= 1
    assert got["ok"] is True


def test_validate_export_field_shape() -> None:
    """Validate export must expose mesh_id, seed, ok, errors, islands, and check counters."""
    got = validate_cli("fixed-cost", CATALOG_SEED)
    assert set(got.keys()) >= {
        "mesh_id",
        "seed",
        "ok",
        "errors",
        "islands",
        "links_checked",
        "portals_checked",
    }
