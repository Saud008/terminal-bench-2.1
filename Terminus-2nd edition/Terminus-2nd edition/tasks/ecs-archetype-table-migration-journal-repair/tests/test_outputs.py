"""Behavioral verifier for archectl migrate/query."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from reference_planner import (
    build_component_map,
    procedural_migrate,
    query_cache_refresh_worlds,
    reference_migrate,
    reference_query,
    reference_query_batch,
    reference_snapshot,
    registration_order,
    tombstone_add_component_world,
)

APP = Path("/app")
CLI = "/usr/local/bin/archectl"
WORLDS = APP / "fixtures/worlds"
BATCHES = APP / "fixtures/batches"
OUTPUT = APP / "output"
STAGING_PATH = "/app/state/archectl-migrate-snapshot.json"
REPLAY_LEDGER_PATH = "/app/state/archectl-replay-ledger.json"
STAGING = Path(STAGING_PATH)
REPLAY_LEDGER = Path(REPLAY_LEDGER_PATH)
RESET = APP / "scripts/reset-state.sh"
REBUILD = APP / "scripts/verifier-rebuild.sh"
SEEDS = json.loads((APP / "fixtures/seeds.json").read_text(encoding="utf-8"))
PRIMARY_SEED = SEEDS[0]
VERIFIER_SEED = os.environ.get("VERIFIER_SEED", "gamma-9001")

CORE = APP / "crates/archecore/src"
BROKEN = Path("/opt/verifier-broken-archecore")
GOLDEN = Path(__file__).resolve().parent / "golden_lib"
MODULES = ("runner", "ledger", "world", "component", "sparse", "archetype", "cache", "planner", "staging", "publish", "wrap")
MODULE_DEST = {
    "runner": CORE / "migrate/runner/mod.rs",
    "ledger": CORE / "migrate/ledger/mod.rs",
    "world": CORE / "storage/world.rs",
    "component": CORE / "storage/component.rs",
    "sparse": CORE / "storage/sparse.rs",
    "archetype": CORE / "storage/archetype.rs",
    "cache": CORE / "query/cache.rs",
    "planner": CORE / "query/planner.rs",
    "staging": CORE / "staging/snapshot.rs",
    "publish": CORE / "export/publish.rs",
    "wrap": CORE / "export/wrap.rs",
}
BROKEN_NAME = {
    "runner": "runner.rs",
    "ledger": "ledger.rs",
    "world": "world.rs",
    "component": "component.rs",
    "sparse": "sparse.rs",
    "archetype": "archetype.rs",
    "cache": "cache.rs",
    "planner": "planner.rs",
    "staging": "snapshot.rs",
    "publish": "publish.rs",
    "wrap": "wrap.rs",
}

STRICT_MIGRATE_WORLDS = [
    "tombstone-respawn",
    "alignment-split",
    "dense-twelve",
    "sparse-recycle",
    "shuffle-four",
]
STRICT_QUERY_WORLDS = ["tombstone-respawn", "alignment-split"]

PROTECTED_SHA256: dict[str, str] = {
    "batches/query-cache-isolation.json": "91eac1527d0499051c9c0d9f9a61b00151f906f79104b501c81c7979e10fef00",
    "seeds.json": "c440e9aef6d59f797bfff83cf17b547f66076446bb2df96bfaf76a513093bf64",
    "worlds/alignment-split/world.json": "cd56a1456e02d2ed50050e9c78b2addb1d8693961399ba3d5085b239015b0ed9",
    "worlds/dense-twelve/world.json": "64a98943bb33bbd86db90a57870bd2647953f4741bfdd7a04a8fd0f01dc314c7",
    "worlds/query-cache-alpha/world.json": "cea220d1d1d289b5fb8b6b09e21cc1d66f3989b81cef01ba50d6b89273b0dfc3",
    "worlds/query-cache-beta/world.json": "77b8058d8d51237dcaa4bb4cc2bf89fd58f01588cee914c6b88914edeca23201",
    "worlds/shuffle-four/world.json": "d311a9475ded1adad3e6198b697b0da76d75ef069c6dfe22e7ad5776892820af",
    "worlds/sparse-recycle/world.json": "277cd8654bece7dd141fe6f17ba73a3da9d17b4413e9ce72a4d45633631c1bcd",
    "worlds/tombstone-respawn/world.json": "89433c10b554e10121e743a92a793fbdc3fbfb7210cc67e80a98b50e0df8e0f0",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(
    cmd: list[str],
    *,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(APP),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


def reset() -> None:
    proc = run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def build_cli() -> None:
    build_env = {**os.environ, "CARGO_NET_OFFLINE": "true"}
    proc = run(
        [
            "cargo",
            "build",
            "--offline",
            "--release",
            "--locked",
            "-p",
            "archectl",
        ],
        env=build_env,
    )
    assert proc.returncode == 0, proc.stderr
    run(["install", "-m", "0755", str(APP / "target/release/archectl"), CLI])


def norm_components(obj: dict) -> dict:
    out = dict(obj)
    if "entities" in out:
        for ent in out["entities"]:
            ent["components"] = {int(k): v for k, v in ent["components"].items()}
    if "component_map" in out:
        out["component_map"] = {k: int(v) for k, v in out["component_map"].items()}
    return out


def norm_query_result(item: dict) -> dict:
    out = dict(item)
    out["entities"] = [int(e) for e in out["entities"]]
    out["query"] = [int(q) for q in out["query"]]
    return out


def migrate_cli(world: str, seed: str, out_name: str) -> dict:
    replay_world_cli(world, seed)
    out = OUTPUT / out_name
    proc = run(
        [
            CLI,
            "migrate",
            "--world",
            str(WORLDS / world / "world.json"),
            "--export",
            str(out),
            "--seed",
            seed,
        ]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return norm_components(json.loads(out.read_text(encoding="utf-8")))


def replay_world_cli(world: str, seed: str) -> None:
    proc = run(
        [
            CLI,
            "replay-world",
            "--world",
            str(WORLDS / world / "world.json"),
            "--seed",
            seed,
        ]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout


def run_migrate_only(world: str, seed: str, out_name: str) -> subprocess.CompletedProcess[str]:
    out = OUTPUT / out_name
    return run(
        [
            CLI,
            "migrate",
            "--world",
            str(WORLDS / world / "world.json"),
            "--export",
            str(out),
            "--seed",
            seed,
        ]
    )


def generation_digest_from_snapshot(snap: dict) -> str:
    entities = sorted(snap.get("entities", []), key=lambda row: row["id"])
    payload = {
        "seed": snap["seed"],
        "generation": snap["generation"],
        "component_map": snap["component_map"],
        "entity_ids": [row["id"] for row in entities],
    }
    raw = json.dumps(payload, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


def query_cli(world: str, seed: str, component_ids: list[int], out_name: str) -> dict:
    out = OUTPUT / out_name
    proc = run(
        [
            CLI,
            "query",
            "--world",
            str(WORLDS / world / "world.json"),
            "--components",
            ",".join(str(c) for c in component_ids),
            "--export",
            str(out),
            "--seed",
            seed,
        ]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return norm_query_result(json.loads(out.read_text(encoding="utf-8")))


def query_batch_cli(batch: Path, seed: str, out_name: str) -> dict:
    out = OUTPUT / out_name
    proc = run(
        [
            CLI,
            "query-batch",
            "--batch",
            str(batch),
            "--export",
            str(out),
            "--seed",
            seed,
        ]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    payload = json.loads(out.read_text(encoding="utf-8"))
    payload["results"] = [norm_query_result(r) for r in payload["results"]]
    return payload


def module_src(mod: str, *, broken: bool) -> Path:
    root = BROKEN if broken else GOLDEN
    if broken:
        return root / BROKEN_NAME[mod]
    for name in (f"golden_{mod}.rs", f"{mod}.rs"):
        path = root / name
        if path.is_file():
            return path
    raise FileNotFoundError(f"missing golden module {mod}")


def install_modules(only_broken: set[str]) -> None:
    for mod in MODULES:
        src = module_src(mod, broken=mod in only_broken)
        shutil.copy2(src, MODULE_DEST[mod])
        MODULE_DEST[mod].touch()
    build_cli()


def install_golden_all() -> None:
    install_modules(set())


def same_generation_query_isolation_batch() -> Path:
    """Two worlds with identical generation but different entity ids (cache-key collision probe)."""
    spec_a = {
        "component_names": ["Marker"],
        "components": {"Marker": {"size": 4, "align": 4}},
        "entities": [{"id": 1, "components": {"Marker": "aa"}}],
        "journal": [],
        "queries": [],
    }
    spec_b = {
        "component_names": ["Marker"],
        "components": {"Marker": {"size": 4, "align": 4}},
        "entities": [{"id": 9, "components": {"Marker": "bb"}}],
        "journal": [],
        "queries": [],
    }
    path_a = OUTPUT / "cache-trap-alpha.json"
    path_b = OUTPUT / "cache-trap-beta.json"
    batch_path = OUTPUT / "cache-trap-isolation.json"
    path_a.write_text(json.dumps(spec_a), encoding="utf-8")
    path_b.write_text(json.dumps(spec_b), encoding="utf-8")
    batch_path.write_text(
        json.dumps(
            {
                "steps": [
                    {"world_path": str(path_a), "components": [0]},
                    {"world_path": str(path_b), "components": [0]},
                ]
            }
        ),
        encoding="utf-8",
    )
    return batch_path


def publish_migrate_cli(out_name: str) -> dict:
    out = OUTPUT / out_name
    proc = run(
        [
            CLI,
            "publish-migrate",
            "--snapshot",
            str(STAGING),
            "--export",
            str(out),
        ]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return norm_components(json.loads(out.read_text(encoding="utf-8")))


class TestArchectlEnvironment:
    """Preinstalled toolchain; must not require network or apt."""

    def test_rust_toolchain_preinstalled(self) -> None:
        """Cargo and rustc must be on PATH without apt-get or rustup downloads."""
        cargo_which = run(["which", "cargo"]).stdout.strip()
        rustc_which = run(["which", "rustc"]).stdout.strip()
        assert cargo_which == "/usr/local/cargo/bin/cargo", cargo_which
        assert rustc_which == "/usr/local/cargo/bin/rustc", rustc_which
        ver = run(["cargo", "--version"])
        assert ver.returncode == 0, ver.stderr


class TestArchectl:
    """ECS archetype migrate and query requirements."""

    def setup_method(self) -> None:
        reset()
        build_cli()

    def test_fixture_integrity(self) -> None:
        """Bundled worlds and seeds must match pinned digests."""
        for rel, digest in PROTECTED_SHA256.items():
            path = APP / "fixtures" / rel
            assert sha256_file(path) == digest, rel

    def test_cli_missing_args_fails(self) -> None:
        """Migrate requires world and export."""
        proc = run([CLI, "migrate"])
        assert proc.returncode != 0

    def test_replay_ledger_written_on_replay_world(self) -> None:
        """replay-world must seal /app/state/archectl-replay-ledger.json during stage 1."""
        replay_world_cli("tombstone-respawn", PRIMARY_SEED)
        assert REPLAY_LEDGER.is_file(), f"{REPLAY_LEDGER_PATH} missing"
        ledger = json.loads(REPLAY_LEDGER.read_text(encoding="utf-8"))
        assert ledger["ledger_version"] == 1
        assert ledger["seed"] == PRIMARY_SEED
        assert ledger["sealed"] is True
        assert ledger["journal_op_count"] >= 1

    def test_replay_ledger_digest_matches_snapshot(self) -> None:
        """The replay ledger digest must match the staged snapshot payload for the recorded state files."""
        replay_world_cli("alignment-split", PRIMARY_SEED)
        assert STAGING.is_file(), f"{STAGING_PATH} missing"
        assert REPLAY_LEDGER.is_file(), f"{REPLAY_LEDGER_PATH} missing"
        snap = json.loads(STAGING.read_text(encoding="utf-8"))
        ledger = json.loads(REPLAY_LEDGER.read_text(encoding="utf-8"))
        assert ledger["generation_digest"] == generation_digest_from_snapshot(snap)

    def test_migrate_without_replay_fails(self) -> None:
        """migrate must not succeed before replay-world materializes staged artifacts."""
        proc = run_migrate_only("tombstone-respawn", PRIMARY_SEED, "no-replay.json")
        assert proc.returncode != 0

    def test_migrate_rejects_tampered_replay_ledger(self) -> None:
        """Tampering with the sealed ledger after replay must fail migrate."""
        replay_world_cli("sparse-recycle", PRIMARY_SEED)
        ledger = json.loads(REPLAY_LEDGER.read_text(encoding="utf-8"))
        ledger["generation_digest"] = "0" * 64
        REPLAY_LEDGER.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
        proc = run_migrate_only("sparse-recycle", PRIMARY_SEED, "tampered-ledger.json")
        assert proc.returncode != 0

    @pytest.mark.parametrize("seed", json.loads((Path(__file__).resolve().parent / "hidden_seeds.json").read_text()))
    def test_hidden_seed_dense_twelve_matches_reference(self, seed: str) -> None:
        """Hidden seeds from verifier-fixtures must pass the two-stage migrate pipeline."""
        hidden_fixture = Path(__file__).resolve().parent / "hidden_seeds.json"
        assert hidden_fixture.is_file(), "verifier-fixtures hidden seed list missing"
        exp = norm_components(reference_migrate(WORLDS / "dense-twelve" / "world.json", seed))
        got = migrate_cli("dense-twelve", seed, f"hidden-dense-{seed}.json")
        assert got == exp

    @pytest.mark.parametrize("world", STRICT_MIGRATE_WORLDS)
    def test_migrate_matches_reference(self, world: str) -> None:
        """Core migrate exports must match the independent reference for the default seed."""
        exp = norm_components(reference_migrate(WORLDS / world / "world.json", PRIMARY_SEED))
        got = migrate_cli(world, PRIMARY_SEED, f"migrate-{world}-{PRIMARY_SEED}.json")
        assert got == exp

    @pytest.mark.parametrize("world", STRICT_QUERY_WORLDS)
    def test_query_matches_reference(self, world: str) -> None:
        """Query export entities must match reference for core worlds (ignoring cache_hit)."""
        spec = json.loads((WORLDS / world / "world.json").read_text(encoding="utf-8"))
        qids = spec["queries"][0]["component_ids"]
        exp = reference_query(WORLDS / world / "world.json", PRIMARY_SEED, qids)
        got = query_cli(world, PRIMARY_SEED, qids, f"query-{world}-{PRIMARY_SEED}.json")
        assert got["entities"] == exp["entities"]
        assert got["generation"] == exp["generation"]

    def test_tombstone_blocks_respawn(self) -> None:
        """Entity id 2 must stay dead after tombstone despite spawn journal entry."""
        got = migrate_cli("tombstone-respawn", PRIMARY_SEED, "tomb.json")
        ids = [e["id"] for e in got["entities"]]
        assert 2 not in ids
        assert 1 in ids

    def test_alignment_split_two_archetypes(self) -> None:
        """Different instance alignments must produce distinct archetype hashes."""
        got = migrate_cli("alignment-split", PRIMARY_SEED, "align.json")
        assert len(got["archetypes"]) == 2
        hashes = {a["hash"] for a in got["archetypes"]}
        assert len(hashes) == 2

    def test_dense_twelve_registration_order(self) -> None:
        """Stable ids must follow seeded shuffle for twelve components."""
        got = migrate_cli("dense-twelve", SEEDS[1], "dense.json")
        names = json.loads((WORLDS / "dense-twelve" / "world.json").read_text())["component_names"]
        order = registration_order(names, SEEDS[1])
        expected = build_component_map(order)
        assert got["component_map"] == expected
        assert len(got["component_map"]) == 12

    def test_sparse_recycle_generation(self) -> None:
        """Reused sparse slot must expose generation > 0 for recycled entity."""
        got = migrate_cli("sparse-recycle", PRIMARY_SEED, "sparse.json")
        ent = {e["id"]: e for e in got["entities"]}[99]
        assert ent["slot_generation"] >= 1

    def test_query_cache_not_stale_across_worlds(self) -> None:
        """Query-batch in one process must not return alpha entities for beta world."""
        batch = BATCHES / "query-cache-isolation.json"
        exp = reference_query_batch(batch, PRIMARY_SEED)
        got = query_batch_cli(batch, PRIMARY_SEED, "cache-batch.json")
        assert len(got["results"]) == 2
        assert got["results"][0]["entities"] == exp["results"][0]["entities"]
        assert got["results"][1]["entities"] == exp["results"][1]["entities"]
        assert got["results"][0]["entities"] == [1]
        assert got["results"][1]["entities"] == [9]

    def test_query_cache_refreshes_after_generation_change(self) -> None:
        """Repeated component query must refresh when storage generation changes."""
        seed = PRIMARY_SEED
        before_spec, after_spec = query_cache_refresh_worlds()
        before_path = OUTPUT / f"cache-refresh-before-{seed}.json"
        after_path = OUTPUT / f"cache-refresh-after-{seed}.json"
        before_path.write_text(json.dumps(before_spec), encoding="utf-8")
        after_path.write_text(json.dumps(after_spec), encoding="utf-8")
        batch_path = OUTPUT / f"cache-refresh-batch-{seed}.json"
        batch_path.write_text(
            json.dumps(
                {
                    "steps": [
                        {"world_path": str(before_path), "components": [0]},
                        {"world_path": str(after_path), "components": [0]},
                    ]
                }
            ),
            encoding="utf-8",
        )
        exp = reference_query_batch(batch_path, seed)
        got = query_batch_cli(batch_path, seed, f"cache-refresh-out-{seed}.json")
        assert got["results"][0]["entities"] == exp["results"][0]["entities"] == [1]
        assert got["results"][1]["entities"] == exp["results"][1]["entities"] == [1, 2]
        assert got["results"][1]["generation"] > got["results"][0]["generation"]

    def test_tombstone_ignores_add_component(self) -> None:
        """add_component targeting a tombstoned entity must not resurrect it."""
        seed = PRIMARY_SEED
        spec = tombstone_add_component_world()
        world_path = OUTPUT / f"tomb-add-{seed}.json"
        out_path = OUTPUT / f"tomb-add-out-{seed}.json"
        world_path.write_text(json.dumps(spec), encoding="utf-8")
        exp = norm_components(procedural_migrate(spec, seed))
        proc = run(
            [
                CLI,
                "replay-world",
                "--world",
                str(world_path),
                "--seed",
                seed,
            ]
        )
        assert proc.returncode == 0, proc.stderr + proc.stdout
        proc = run(
            [
                CLI,
                "migrate",
                "--world",
                str(world_path),
                "--export",
                str(out_path),
                "--seed",
                seed,
            ]
        )
        assert proc.returncode == 0, proc.stderr + proc.stdout
        got = norm_components(json.loads(out_path.read_text(encoding="utf-8")))
        assert 1 not in [e["id"] for e in got["entities"]]
        assert got["entities"] == exp["entities"]

    def test_registration_map_primary_seed(self) -> None:
        """alpha-7 registration must use seeded shuffle, not alphabetical order."""
        got = migrate_cli("tombstone-respawn", PRIMARY_SEED, "reg-map.json")
        names = json.loads((WORLDS / "tombstone-respawn" / "world.json").read_text())[
            "component_names"
        ]
        expected = build_component_map(registration_order(names, PRIMARY_SEED))
        assert got["component_map"] == expected
        assert got["component_map"] != build_component_map(sorted(names))

    def test_shuffle_four_registration_and_hash(self) -> None:
        """Four-component shuffle world must match reference migrate export."""
        exp = norm_components(reference_migrate(WORLDS / "shuffle-four" / "world.json", PRIMARY_SEED))
        got = migrate_cli("shuffle-four", PRIMARY_SEED, "shuffle-four.json")
        assert got == exp
        assert len(got["archetypes"]) == 1

    def test_sparse_recycle_reference_export(self) -> None:
        """Sparse recycle slot generation must match full reference migrate export."""
        exp = norm_components(reference_migrate(WORLDS / "sparse-recycle" / "world.json", PRIMARY_SEED))
        got = migrate_cli("sparse-recycle", PRIMARY_SEED, "sparse-ref.json")
        assert got == exp

    def test_procedural_verifier_seed_migrate(self) -> None:
        """Seed-derived journal must match reference migrate export."""
        spec = {
            "component_names": ["One", "Two", "Three"],
            "components": {
                "One": {"size": 4, "align": 4},
                "Two": {"size": 4, "align": 8},
                "Three": {"size": 4, "align": 4},
            },
            "entities": [{"id": 5, "components": {"One": "11", "Two": "22"}}],
            "journal": [
                {"op": "remove_component", "entity": 5, "component": "One"},
                {"op": "spawn", "entity": 8, "components": {"Two": "88", "Three": "33"}},
            ],
            "queries": [],
        }
        exp = norm_components(procedural_migrate(spec, VERIFIER_SEED))
        world_path = OUTPUT / f"proc-seed-{VERIFIER_SEED}.json"
        world_path.write_text(json.dumps(spec), encoding="utf-8")
        proc = run(
            [
                CLI,
                "replay-world",
                "--world",
                str(world_path),
                "--seed",
                VERIFIER_SEED,
            ]
        )
        assert proc.returncode == 0, proc.stderr + proc.stdout
        proc = run(
            [
                CLI,
                "migrate",
                "--world",
                str(world_path),
                "--export",
                str(OUTPUT / f"proc-seed-out-{VERIFIER_SEED}.json"),
                "--seed",
                VERIFIER_SEED,
            ]
        )
        assert proc.returncode == 0, proc.stderr + proc.stdout
        got = norm_components(
            json.loads((OUTPUT / f"proc-seed-out-{VERIFIER_SEED}.json").read_text())
        )
        assert got == exp

    def test_property_component_sequence(self) -> None:
        """Procedural add/remove journal must match reference migrate export."""
        seed = PRIMARY_SEED
        spec = {
            "component_names": ["A", "B", "C"],
            "components": {
                "A": {"size": 4, "align": 4},
                "B": {"size": 4, "align": 8},
                "C": {"size": 4, "align": 4},
            },
            "entities": [{"id": 1, "components": {"A": "01", "B": "02"}}],
            "journal": [
                {"op": "add_component", "entity": 1, "component": "C", "data": "03", "align": 4},
                {"op": "remove_component", "entity": 1, "component": "B"},
                {"op": "spawn", "entity": 2, "components": {"A": "aa", "C": "bb"}},
            ],
            "queries": [],
        }
        world_path = OUTPUT / f"proc-{seed}.json"
        world_path.write_text(json.dumps(spec), encoding="utf-8")
        exp = norm_components(procedural_migrate(spec, seed))
        proc = run(
            [
                CLI,
                "replay-world",
                "--world",
                str(world_path),
                "--seed",
                seed,
            ]
        )
        assert proc.returncode == 0, proc.stderr
        proc = run(
            [
                CLI,
                "migrate",
                "--world",
                str(world_path),
                "--export",
                str(OUTPUT / f"proc-out-{seed}.json"),
                "--seed",
                seed,
            ]
        )
        assert proc.returncode == 0, proc.stderr
        got = norm_components(json.loads((OUTPUT / f"proc-out-{seed}.json").read_text()))
        assert got == exp

    def test_migrate_snapshot_written(self) -> None:
        """Migrate must write /app/state/archectl-migrate-snapshot.json matching migrate-snapshot-schema.md."""
        migrate_cli("tombstone-respawn", PRIMARY_SEED, "snap-check.json")
        assert STAGING.is_file(), f"{STAGING_PATH} missing"
        got = norm_components(json.loads(STAGING.read_text(encoding="utf-8")))
        expect = reference_snapshot(WORLDS / "tombstone-respawn" / "world.json", PRIMARY_SEED)
        assert got == expect

    def test_snapshot_entity_order_ascending(self) -> None:
        """Snapshot entities must sort by id ascending."""
        migrate_cli("shuffle-four", PRIMARY_SEED, "snap-order.json")
        snap = json.loads(STAGING.read_text(encoding="utf-8"))
        ids = [row["id"] for row in snap["entities"]]
        assert ids == sorted(ids)

    def test_publish_reads_snapshot_not_rereload(self) -> None:
        """Publish-migrate must consume /app/state/archectl-migrate-snapshot.json without re-reading the world fixture."""
        first = migrate_cli("tombstone-respawn", PRIMARY_SEED, "pub-a.json")
        snapshot_copy = json.loads(STAGING.read_text(encoding="utf-8"))
        second = publish_migrate_cli("pub-b.json")
        assert json.loads(STAGING.read_text(encoding="utf-8")) == snapshot_copy
        assert second == first


class TestModuleTraps:
    def setup_method(self) -> None:
        reset()
        build_cli()

    def teardown_method(self) -> None:
        run(["bash", str(REBUILD)])

    @pytest.mark.parametrize(
        "broken_only,world,check",
        [
            ("runner", "dense-twelve", "migrate"),
            ("ledger", "alignment-split", "ledger_digest"),
            ("world", "tombstone-respawn", "migrate"),
            ("component", "dense-twelve", "migrate"),
            ("sparse", "sparse-recycle", "migrate"),
            ("archetype", "alignment-split", "migrate"),
            ("staging", "alignment-split", "snapshot"),
            ("publish", "alignment-split", "migrate"),
            ("wrap", "sparse-recycle", "migrate"),
        ],
    )
    def test_single_module_trap_fails_with_broken_only(
        self, broken_only: str, world: str, check: str
    ) -> None:
        """Each /opt/verifier-broken-archecore module alone must fail at least one check."""
        broken_root = Path("/opt/verifier-broken-archecore")
        assert (broken_root / BROKEN_NAME[broken_only]).is_file()
        install_modules({broken_only})
        if check == "ledger_digest":
            replay_world_cli(world, PRIMARY_SEED)
            proc = run_migrate_only(world, PRIMARY_SEED, f"trap-{broken_only}.json")
            assert proc.returncode != 0
            return
        if check == "snapshot":
            migrate_cli(world, PRIMARY_SEED, f"trap-{broken_only}.json")
            got = norm_components(json.loads(STAGING.read_text(encoding="utf-8")))
            expect = reference_snapshot(WORLDS / world / "world.json", PRIMARY_SEED)
            assert got != expect
            return
        if check == "query_batch":
            batch = BATCHES / "query-cache-isolation.json"
            got = query_batch_cli(batch, PRIMARY_SEED, f"trap-{broken_only}.json")
            expect = reference_query_batch(batch, PRIMARY_SEED)
            assert got != expect
            return
        exp = norm_components(reference_migrate(WORLDS / world / "world.json", PRIMARY_SEED))
        got = migrate_cli(world, PRIMARY_SEED, f"trap-{broken_only}.json")
        assert got != exp

    def test_verifier_rebuild_restores_broken_baseline(self) -> None:
        """verifier-rebuild.sh must restore the broken archecore baseline after a golden install."""
        install_golden_all()
        exp = norm_components(reference_migrate(WORLDS / "tombstone-respawn" / "world.json", PRIMARY_SEED))
        got = migrate_cli("tombstone-respawn", PRIMARY_SEED, "rebuild-golden.json")
        assert got == exp
        proc = run(["bash", str(REBUILD)])
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = migrate_cli("tombstone-respawn", PRIMARY_SEED, "rebuild-broken.json")
        assert got != exp

    def test_baseline_is_broken(self) -> None:
        """The verifier rebuild baseline must still fail the migrate reference contract before fixes."""
        proc = run(["bash", str(REBUILD)])
        assert proc.returncode == 0, proc.stderr or proc.stdout
        exp = norm_components(reference_migrate(WORLDS / "tombstone-respawn" / "world.json", PRIMARY_SEED))
        got = migrate_cli("tombstone-respawn", PRIMARY_SEED, "broken-baseline.json")
        assert got != exp

    def test_single_module_trap_cache_fails_query_isolation(self) -> None:
        """A broken cache module alone must still violate the query-batch isolation contract."""
        batch = same_generation_query_isolation_batch()
        install_modules({"cache"})
        got = query_batch_cli(batch, PRIMARY_SEED, "trap-cache.json")
        expect = reference_query_batch(batch, PRIMARY_SEED)
        assert got != expect

    def test_single_module_trap_planner_fails_query_isolation(self) -> None:
        """A broken planner module alone must still violate the generation-aware query plan contract."""
        batch = same_generation_query_isolation_batch()
        install_modules({"planner"})
        got = query_batch_cli(batch, PRIMARY_SEED, "trap-planner.json")
        expect = reference_query_batch(batch, PRIMARY_SEED)
        assert got != expect


class TestPartialFixTraps:
    def setup_method(self) -> None:
        reset()
        build_cli()

    def teardown_method(self) -> None:
        run(["bash", str(REBUILD)])

    def test_partial_golden_replay_only_still_fails_sparse_slot(self) -> None:
        """Replay-only partial fixes must still fail sparse slot generation behavior."""
        install_modules({"staging", "publish", "wrap", "ledger", "runner"})
        exp = norm_components(reference_migrate(WORLDS / "sparse-recycle" / "world.json", PRIMARY_SEED))
        got = migrate_cli("sparse-recycle", PRIMARY_SEED, "partial-replay.json")
        assert got != exp

    def test_partial_golden_staging_only_still_fails_export_order(self) -> None:
        """Staging-only partial fixes must still fail the sorted export entity order requirement."""
        install_modules({"runner", "ledger", "world", "component", "sparse", "archetype", "cache", "planner", "publish", "wrap"})
        migrate_cli("alignment-split", PRIMARY_SEED, "partial-staging.json")
        got = json.loads((OUTPUT / "partial-staging.json").read_text(encoding="utf-8"))
        ids = [row["id"] for row in got["entities"]]
        assert ids != sorted(ids)

    def test_partial_golden_wrap_only_still_fails_journal_order(self) -> None:
        """Wrap-only partial fixes must still fail full migrate replay correctness."""
        install_modules({"runner", "ledger", "world", "component", "sparse", "archetype", "cache", "planner", "staging", "publish"})
        exp = norm_components(reference_migrate(WORLDS / "tombstone-respawn" / "world.json", PRIMARY_SEED))
        got = migrate_cli("tombstone-respawn", PRIMARY_SEED, "partial-wrap.json")
        assert got != exp

    def test_partial_golden_cache_only_still_fails_query_isolation(self) -> None:
        """Golden planner cannot compensate for generation-blind cache keys."""
        batch = same_generation_query_isolation_batch()
        install_modules({"runner", "ledger", "world", "component", "sparse", "archetype", "cache", "staging", "publish", "wrap"})
        got = query_batch_cli(batch, PRIMARY_SEED, "partial-cache.json")
        expect = reference_query_batch(batch, PRIMARY_SEED)
        assert got != expect

    def test_partial_golden_planner_only_still_fails_query_isolation(self) -> None:
        """Golden cache keys cannot fix planner cache hits that skip generation guards."""
        batch = same_generation_query_isolation_batch()
        install_modules({"runner", "ledger", "world", "component", "sparse", "archetype", "planner", "staging", "publish", "wrap"})
        got = query_batch_cli(batch, PRIMARY_SEED, "partial-planner.json")
        expect = reference_query_batch(batch, PRIMARY_SEED)
        assert got != expect

    def test_partial_golden_ledger_only_still_fails_digest(self) -> None:
        """Ledger-only partial fixes must still reject migrate when replay staging stays broken."""
        install_modules({"ledger"})
        replay_world_cli("alignment-split", PRIMARY_SEED)
        proc = run_migrate_only("alignment-split", PRIMARY_SEED, "partial-ledger.json")
        assert proc.returncode != 0

    def test_partial_golden_runner_only_still_fails_without_replay(self) -> None:
        """Runner-only partial fixes must still fail migrate before staged replay artifacts exist."""
        install_modules({"runner"})
        proc = run_migrate_only("tombstone-respawn", PRIMARY_SEED, "partial-runner.json")
        assert proc.returncode != 0

    def test_golden_modules_pass_full_matrix(self) -> None:
        """Installing the full golden module set must satisfy the strict migrate matrix."""
        install_golden_all()
        for world in STRICT_MIGRATE_WORLDS:
            exp = norm_components(reference_migrate(WORLDS / world / "world.json", PRIMARY_SEED))
            got = migrate_cli(world, PRIMARY_SEED, f"golden-{world}.json")
            assert got == exp
