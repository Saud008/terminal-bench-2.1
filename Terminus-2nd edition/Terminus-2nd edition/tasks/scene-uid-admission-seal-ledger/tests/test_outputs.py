"""Behavioral verifier for scenectl apply and sealed admission export."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from reference_merge import effective_base, reference_apply

APP = Path("/app")
CLI = "/app/bin/scenectl"
FIXTURES = APP / "fixtures"
VERIFIER_FIXTURES = Path("/opt/verifier-fixtures")
VERIFIER_DOCS = Path("/opt/verifier-contract-docs")
OUTPUT = APP / "output"
CATALOG = json.loads((VERIFIER_FIXTURES / "catalog.json").read_text(encoding="utf-8"))
SEEDS_CFG = json.loads((VERIFIER_FIXTURES / "seeds.json").read_text(encoding="utf-8"))
SEEDS = SEEDS_CFG["seeds"]
CATALOG_DEFAULT = SEEDS_CFG["catalog_seed"]
RESET = APP / "scripts" / "reset-state.sh"

PROTECTED_DOCS = [
    "uid-admission-contract.md",
    "sealed-export-obligations.md",
    "tscn-uid-format.md",
    "ledger-schema.md",
    "exit-codes.md",
]


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _verifier_fixture_hashes() -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in sorted(VERIFIER_FIXTURES.rglob("*")):
        if path.is_file():
            rel = path.relative_to(VERIFIER_FIXTURES).as_posix()
            hashes[rel] = _sha256_file(path)
    return hashes


VERIFIER_FIXTURE_SHA256 = _verifier_fixture_hashes()
DOC_SHA256 = {name: _sha256_file(VERIFIER_DOCS / name) for name in PROTECTED_DOCS}
FIXTURE_META_SHA256 = {
    "catalog.json": _sha256_file(VERIFIER_FIXTURES / "catalog.json"),
    "seeds.json": _sha256_file(VERIFIER_FIXTURES / "seeds.json"),
}


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False)


def reset() -> None:
    proc = run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def scenario_entry(name: str) -> dict:
    return next(s for s in CATALOG["scenarios"] if s["name"] == name)


def reference_tree_path(name: str) -> Path:
    entry = scenario_entry(name)
    return VERIFIER_FIXTURES / entry["tree"]


def apply_cli(name: str, seed: int) -> subprocess.CompletedProcess[str]:
    entry = scenario_entry(name)
    tree = FIXTURES / entry["tree"]
    base = effective_base(entry, seed, SEEDS_CFG)
    export_path = OUTPUT / f"{name}-{seed}.json"
    return run(
        [
            CLI,
            "apply",
            "--tree",
            str(tree),
            "--base",
            base,
            "--left",
            entry["branches"]["left"],
            "--right",
            entry["branches"]["right"],
            "--seed",
            str(seed),
            "--export",
            str(export_path),
        ]
    )


def load_export(name: str, seed: int) -> dict:
    return json.loads((OUTPUT / f"{name}-{seed}.json").read_text(encoding="utf-8"))


def expected_apply(name: str, seed: int) -> dict:
    entry = scenario_entry(name)
    tree = reference_tree_path(name)
    base = effective_base(entry, seed, SEEDS_CFG)
    expected = reference_apply(
        tree,
        base,
        entry["branches"]["left"],
        entry["branches"]["right"],
        seed,
        VERIFIER_FIXTURES,
    )
    expected["tree"] = str(FIXTURES / entry["tree"])
    return expected


@pytest.fixture(autouse=True)
def _reset_output() -> None:
    reset()


def test_verifier_fixture_archive_integrity() -> None:
    """Immutable verifier fixture archive under /opt must never change."""
    for rel, expected in VERIFIER_FIXTURE_SHA256.items():
        path = VERIFIER_FIXTURES / rel
        assert path.is_file(), rel
        assert _sha256_file(path) == expected


def test_fixture_integrity() -> None:
    """Protected docs and catalog bytes must remain unchanged after reset."""
    for name, expected in DOC_SHA256.items():
        assert _sha256_file(APP / "docs" / name) == expected
    for name, expected in FIXTURE_META_SHA256.items():
        assert _sha256_file(FIXTURES / name) == expected
    for rel, expected in VERIFIER_FIXTURE_SHA256.items():
        if rel.startswith("trees/"):
            assert _sha256_file(FIXTURES / rel) == expected


@pytest.mark.parametrize("scenario_name", [s["name"] for s in CATALOG["scenarios"] if s["name"] != "cycle-trap"])
@pytest.mark.parametrize("seed", SEEDS)
def test_apply_matches_reference(scenario_name: str, seed: int) -> None:
    """Sealed exports must match the independent reference authority."""
    expected = expected_apply(scenario_name, seed)
    proc = apply_cli(scenario_name, seed)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = load_export(scenario_name, seed)
    assert got == expected


@pytest.mark.parametrize("seed", SEEDS)
def test_village_remap_applies_uid_tokens(seed: int) -> None:
    """Remap must rewrite ext_resource uid tokens, not only res paths."""
    proc = apply_cli("village-remap", seed)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = load_export("village-remap", seed)
    suffix_mod = int(SEEDS_CFG["remap_suffix_mod"])
    expected_uid = f'{SEEDS_CFG["remap_prefix"]}_{seed % suffix_mod}'
    player = got["merged_files"]["player.tscn"]
    assert expected_uid in player
    main = got["merged_files"]["main.tscn"]
    assert expected_uid in main
    assert "uid://player_old" not in main


def test_village_sub_resource_uid_remap() -> None:
    """Remap must rewrite sub_resource uid tokens per merge contract."""
    seed = CATALOG_DEFAULT
    proc = apply_cli("village-remap", seed)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = load_export("village-remap", seed)
    player = got["merged_files"]["player.tscn"]
    assert "uid://collider_new" in player
    assert "uid://collider_old" not in player
    expected = expected_apply("village-remap", seed)
    assert got["merged_files"]["player.tscn"] == expected["merged_files"]["player.tscn"]


def test_village_conflict_prefers_base_branch() -> None:
    """Three-way conflicts must keep the --base branch content (not newer mtime)."""
    seed = 4
    entry = scenario_entry("village-remap")
    base = effective_base(entry, seed, SEEDS_CFG)
    assert base == "base"
    proc = apply_cli("village-remap", seed)
    assert proc.returncode == 0
    main = load_export("village-remap", seed)["merged_files"]["main.tscn"]
    assert "LeftMarker" not in main
    assert "RightMarker" not in main


@pytest.mark.parametrize("seed", SEEDS)
def test_cycle_trap_exits_two(seed: int) -> None:
    """Circular UID graphs must exit 2 while still writing export JSON."""
    proc = apply_cli("cycle-trap", seed)
    assert proc.returncode == 2, proc.stderr or proc.stdout
    got = load_export("cycle-trap", seed)
    expected = expected_apply("cycle-trap", seed)
    assert got["uid_graph_ok"] is False
    assert got["cycles"] == expected["cycles"]
    assert got["cycles"]


def test_texture_ring_ignores_non_packed_scene_edges() -> None:
    """Texture2D uid references must not create graph edges or false cycles."""
    seed = CATALOG_DEFAULT
    proc = apply_cli("texture-ring-trap", seed)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = load_export("texture-ring-trap", seed)
    expected = expected_apply("texture-ring-trap", seed)
    assert got["uid_graph_ok"] is True
    assert got["cycles"] == []
    assert got == expected


def test_orphan_trap_reports_dangling_uid() -> None:
    """Deleted scenes must surface orphan uid references."""
    seed = CATALOG_DEFAULT
    proc = apply_cli("orphan-trap", seed)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = load_export("orphan-trap", seed)
    assert "enemy.tscn" not in got["merged_files"]
    assert any(o["uid"] == "uid://enemy_old" for o in got["orphans"])


def test_crlf_ledger_uses_lf_normalized_hash() -> None:
    """Ledger entry hashes must use LF-normalized content."""
    seed = CATALOG_DEFAULT
    proc = apply_cli("crlf-trap", seed)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = load_export("crlf-trap", seed)
    expected = expected_apply("crlf-trap", seed)
    assert got["ledger"] == expected["ledger"]
    assert "\r" not in got["merged_files"]["town.tscn"]


def test_seed_base_branch_flip() -> None:
    """Seed must swap which branch is passed as --base for conflict resolution."""
    entry = scenario_entry("village-remap")
    seed = 7  # 7 % 2 == 1 -> left base
    base = effective_base(entry, seed, SEEDS_CFG)
    assert base == "left"
    expected = expected_apply("village-remap", seed)
    proc = apply_cli("village-remap", seed)
    assert proc.returncode == 0
    assert load_export("village-remap", seed) == expected


def test_hidden_verifier_fixtures_drive_catalog() -> None:
    """Catalog scenarios must come from /opt/verifier-fixtures, not a mutable /app copy alone."""
    assert VERIFIER_FIXTURES.is_dir()
    assert (VERIFIER_FIXTURES / "catalog.json").is_file()
    assert len(CATALOG["scenarios"]) >= 4


def test_hidden_opt_docs_match_app_docs() -> None:
    """Contract docs under /opt/verifier-contract-docs must match /app/docs after reset."""
    for name in PROTECTED_DOCS:
        assert _sha256_file(VERIFIER_DOCS / name) == _sha256_file(APP / "docs" / name)


def test_apply_staging_snapshot_matches_export_payload() -> None:
    """Apply staging snapshot fields must match the sealed export JSON payload."""
    seed = CATALOG_DEFAULT
    proc = apply_cli("village-remap", seed)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = load_export("village-remap", seed)
    staging = {
        "tree": got["tree"],
        "seed": got["seed"],
        "ledger": got["ledger"],
        "uid_graph_ok": got["uid_graph_ok"],
    }
    assert staging["seed"] == seed
    assert staging["ledger"] == expected_apply("village-remap", seed)["ledger"]


def test_ingest_seed_overlay_before_export() -> None:
    """Seed overlay ingest into remap must land before sealed export is written."""
    seed = CATALOG_DEFAULT
    proc = apply_cli("village-remap", seed)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = load_export("village-remap", seed)
    suffix_mod = int(SEEDS_CFG["remap_suffix_mod"])
    expected_uid = f'{SEEDS_CFG["remap_prefix"]}_{seed % suffix_mod}'
    assert any(expected_uid in text for text in got["merged_files"].values())


def test_decoy_sidecar_not_on_apply_path() -> None:
    """Decoy sidecar under lib/tscn/decoy must not be sourced by apply exports."""
    decoy = APP / "lib" / "tscn" / "decoy" / "sidecar.sh"
    assert decoy.is_file()
    apply_src = (APP / "lib" / "tscn" / "apply.sh").read_text(encoding="utf-8")
    assert "decoy/sidecar" not in apply_src
    assert "tscn_decoy_sidecar_noop" not in apply_src


def test_exit_codes_doc_matches_cycle_trap() -> None:
    """Cycle trap must use exit code 2 per /opt/verifier-contract-docs/exit-codes.md."""
    seed = CATALOG_DEFAULT
    proc = apply_cli("cycle-trap", seed)
    assert proc.returncode == 2
    doc = (VERIFIER_DOCS / "exit-codes.md").read_text(encoding="utf-8")
    assert "2" in doc


def test_ledger_schema_keys_present_on_export() -> None:
    """Sealed export ledger object must carry schema keys from ledger-schema.md."""
    seed = CATALOG_DEFAULT
    proc = apply_cli("village-remap", seed)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    ledger = load_export("village-remap", seed)["ledger"]
    expected = expected_apply("village-remap", seed)["ledger"]
    assert set(ledger.keys()) == set(expected.keys())
    assert ledger == expected
