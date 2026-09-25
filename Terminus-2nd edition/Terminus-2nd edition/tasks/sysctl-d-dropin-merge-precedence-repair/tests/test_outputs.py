"""Behavioral verifier for sysctlmerge apply CLI."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

import pytest


def _tests_root() -> Path:
    """Resolve mounted verifier test dir (handles CRLF temp copy in test.sh)."""
    env = Path(os.environ.get("TEST_DIR", "/tests"))
    if (env / "reference_merger.py").is_file():
        return env
    fallback = Path("/tests")
    if (fallback / "reference_merger.py").is_file():
        return fallback
    return env


TESTS = _tests_root()
sys.path.insert(0, str(TESTS))
from bundle_builder import procedural_tree  # noqa: E402
from reference_merger import reference_apply, reference_staging, reference_staging_path, snapshot_digest  # noqa: E402

APP = Path("/app")
CLI = Path("/usr/local/bin/sysctlmerge")
BUNDLES = APP / "fixtures" / "bundles"
OUTPUT = APP / "output"
RESET = APP / "scripts" / "reset-state.sh"
SEEDS = json.loads((APP / "fixtures" / "seeds.json").read_text(encoding="utf-8"))["seeds"]
VERIFIER_SEED = os.environ.get("VERIFIER_SEED", SEEDS[0])
BROKEN = TESTS / "verifier-broken"
GOLDEN = TESTS / "verifier-golden"
HIDDEN_BUNDLES = TESTS / "hidden_bundles"
LIB = APP / "lib"
STATE = APP / "state"
SNAPSHOT = STATE / "sysctlmerge-snapshot.json"
REPLAY_LEDGER = STATE / "sysctlmerge.replay.jsonl"

INGEST_CORE_GOLDEN = {
    "parse.sh": GOLDEN / "golden_parse.sh",
    "order.sh": GOLDEN / "golden_order.sh",
    "layers.sh": GOLDEN / "golden_layers.sh",
    "merge.sh": GOLDEN / "golden_merge.sh",
}

EXPORT_GATE_GOLDEN = {
    "staging.sh": GOLDEN / "golden_staging.sh",
    "replay.sh": GOLDEN / "golden_replay.sh",
    "export.sh": GOLDEN / "golden_export.sh",
    "guard.sh": GOLDEN / "golden_guard.sh",
}

SUCCESS_TREES = [
    "layered-precedence",
    "whitespace-sep",
    "comment-values",
    "key-collision",
    "override-stack",
    "intra-duplicate",
    "sparse-main",
    "cascade-retain",
    "quoted-values",
]


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False)


def reset() -> None:
    proc = run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def apply(tree: Path, seed: str, out: Path) -> subprocess.CompletedProcess[str]:
    out.parent.mkdir(parents=True, exist_ok=True)
    return run(
        [
            str(CLI),
            "apply",
            "--tree",
            str(tree),
            "--seed",
            seed,
            "--output",
            str(out),
        ]
    )


def ingest(tree: Path, seed: str, snap: Path) -> subprocess.CompletedProcess[str]:
    snap.parent.mkdir(parents=True, exist_ok=True)
    return run(
        [
            str(CLI),
            "ingest",
            "--tree",
            str(tree),
            "--seed",
            seed,
            "--snapshot",
            str(snap),
        ]
    )


def export_snapshot(snap: Path, out: Path) -> subprocess.CompletedProcess[str]:
    out.parent.mkdir(parents=True, exist_ok=True)
    return run(
        [
            str(CLI),
            "export",
            "--snapshot",
            str(snap),
            "--output",
            str(out),
        ]
    )


def verify_snapshot(snap: Path) -> tuple[int, dict]:
    proc = run([str(CLI), "verify", "--snapshot", str(snap)])
    body = json.loads((proc.stdout or "{}").strip() or "{}")
    return proc.returncode, body


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def protected_hashes() -> dict[str, str]:
    out: dict[str, str] = {}
    for tree_dir in sorted(BUNDLES.iterdir()):
        if not tree_dir.is_dir():
            continue
        for path in sorted(tree_dir.rglob("*")):
            if path.is_file():
                rel = path.relative_to(tree_dir).as_posix()
                out[f"{tree_dir.name}/{rel}"] = sha256(path)
    return out


PROTECTED = protected_hashes()


def restore_libs(saved: dict[str, str]) -> None:
    for name, content in saved.items():
        (LIB / name).write_text(content, encoding="utf-8")


def _copy_lib_script(src: Path, dest: Path) -> None:
    text = src.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    dest.write_text(text, encoding="utf-8")


def with_partial_patch(golden_files: dict[str, Path], fn) -> None:
    saved = {p.name: p.read_text(encoding="utf-8") for p in sorted(LIB.glob("*.sh"))}
    try:
        for src in BROKEN.glob("*.sh"):
            _copy_lib_script(src, LIB / src.name)
        for lib_name, patch in golden_files.items():
            _copy_lib_script(patch, LIB / lib_name)
        fn()
    finally:
        restore_libs(saved)


@contextmanager
def hidden_bundle(name: str):
    src = HIDDEN_BUNDLES / name
    dest = Path(tempfile.mkdtemp(prefix=f"hidden-{name}-"))
    shutil.copytree(src, dest, dirs_exist_ok=True)
    try:
        yield dest
    finally:
        shutil.rmtree(dest, ignore_errors=True)


class TestSysctlMerge:
    """sysctlmerge apply contract checks."""

    def setup_method(self) -> None:
        reset()

    def test_fixture_integrity(self) -> None:
        """Public fixture trees must remain unchanged."""
        for rel, digest in PROTECTED.items():
            tree, _, rest = rel.partition("/")
            path = BUNDLES / tree / rest
            assert path.is_file(), rel
            assert sha256(path) == digest, rel

    @pytest.mark.parametrize("tree_name", SUCCESS_TREES)
    @pytest.mark.parametrize("seed", SEEDS)
    def test_apply_matches_reference(self, tree_name: str, seed: str) -> None:
        """Each tree/seed export must match the independent reference merger."""
        tree = BUNDLES / tree_name
        out = OUTPUT / f"{tree_name}-{seed}.json"
        proc = apply(tree, seed, out)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        got = json.loads(out.read_text(encoding="utf-8"))
        expect = reference_apply(tree, seed)
        assert got == expect

    def test_verifier_seed_collision_matches_reference(self) -> None:
        """VERIFIER_SEED-derived collision tree must match reference (anti hardcode)."""
        tree = BUNDLES / "key-collision"
        out = OUTPUT / f"key-collision-{VERIFIER_SEED}.json"
        proc = apply(tree, VERIFIER_SEED, out)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        got = json.loads(out.read_text(encoding="utf-8"))
        expect = reference_apply(tree, VERIFIER_SEED)
        assert got == expect

    def test_seed_permutation_changes_collision_winner(self) -> None:
        """Ten drop-ins colliding on one key resolve differently per seed."""
        tree = BUNDLES / "key-collision"
        winners: set[str] = set()
        for seed in SEEDS:
            out = OUTPUT / f"collision-{seed}.json"
            proc = apply(tree, seed, out)
            assert proc.returncode == 0, proc.stderr
            doc = json.loads(out.read_text(encoding="utf-8"))
            winners.add(doc["effective"]["shared.collision.key"])
        assert len(winners) >= 2

    def test_layered_precedence_retains_main_only_keys(self) -> None:
        """Per-key merge must keep main-only keys when drop-ins override other names."""
        tree = BUNDLES / "layered-precedence"
        out = OUTPUT / "layered-main-keys.json"
        proc = apply(tree, SEEDS[0], out)
        assert proc.returncode == 0, proc.stderr
        doc = json.loads(out.read_text(encoding="utf-8"))
        expect = reference_apply(tree, SEEDS[0])
        assert doc["effective"] == expect["effective"]
        assert "vm.swappiness" in doc["effective"]

    def test_dropin_invalid_key_apply_fails(self) -> None:
        """Invalid keys in drop-in fragments abort apply with exit code 3."""
        tree = BUNDLES / "dropin-invalid"
        out = OUTPUT / "dropin-invalid-spot.json"
        proc = apply(tree, SEEDS[0], out)
        assert proc.returncode == 3, proc.stderr + proc.stdout
        assert not out.exists()

    def test_processing_order_varies_by_seed(self) -> None:
        """Seed-keyed drop-in ordering must differ across seeds for key-collision."""
        tree = BUNDLES / "key-collision"
        orders: set[tuple[str, ...]] = set()
        for seed in SEEDS:
            out = OUTPUT / f"order-{seed}.json"
            proc = apply(tree, seed, out)
            assert proc.returncode == 0, proc.stderr
            doc = json.loads(out.read_text(encoding="utf-8"))
            orders.add(tuple(doc["processing_order"]))
        assert len(orders) >= 2

    def test_export_schema_top_level_fields(self) -> None:
        """Successful apply export must include every documented top-level field."""
        tree = BUNDLES / "layered-precedence"
        out = OUTPUT / "schema-keys.json"
        proc = apply(tree, SEEDS[0], out)
        assert proc.returncode == 0, proc.stderr
        doc = json.loads(out.read_text(encoding="utf-8"))
        required = {
            "apply_version",
            "tree",
            "seed",
            "processing_order",
            "effective",
            "sources",
            "stats",
            "apply_digest",
        }
        assert required <= set(doc.keys())
        expect = reference_apply(tree, SEEDS[0])
        assert doc["apply_digest"] == expect["apply_digest"]
        assert len(doc["apply_digest"]) == 64

    def test_sources_provenance_matches_reference(self) -> None:
        """Winning file/line provenance must match the reference merger."""
        tree = BUNDLES / "override-stack"
        out = OUTPUT / "sources-provenance.json"
        proc = apply(tree, SEEDS[0], out)
        assert proc.returncode == 0, proc.stderr
        got = json.loads(out.read_text(encoding="utf-8"))
        expect = reference_apply(tree, SEEDS[0])
        assert got["sources"] == expect["sources"]
        assert got["stats"] == expect["stats"]

    def test_partial_golden_parse_and_tree_still_wrong_override_stack(self) -> None:
        """Fixing parse.sh and tree.sh without merge.sh still drops earlier keys."""
        def check() -> None:
            tree = BUNDLES / "layered-precedence"
            out = OUTPUT / "partial-parse-tree.json"
            proc = apply(tree, SEEDS[0], out)
            assert proc.returncode == 0, proc.stderr
            got = json.loads(out.read_text(encoding="utf-8"))
            expect = reference_apply(tree, SEEDS[0])
            assert got != expect

        with_partial_patch(
            {"parse.sh": GOLDEN / "golden_parse.sh", "tree.sh": GOLDEN / "golden_tree.sh"},
            check,
        )

    def test_wrong_dropin_hash_still_wrong_collision_winner(self) -> None:
        """Golden parse/merge/layers with broken order.sh still picks wrong winners."""
        def check() -> None:
            tree = BUNDLES / "key-collision"
            seed = "base"
            out = OUTPUT / "partial-wrong-hash.json"
            proc = apply(tree, seed, out)
            assert proc.returncode == 0, proc.stderr
            got = json.loads(out.read_text(encoding="utf-8"))
            expect = reference_apply(tree, seed)
            assert got["effective"]["shared.collision.key"] != expect["effective"]["shared.collision.key"]

        with_partial_patch(
            {
                "parse.sh": GOLDEN / "golden_parse.sh",
                "merge.sh": GOLDEN / "golden_merge.sh",
                "layers.sh": GOLDEN / "golden_layers.sh",
            },
            check,
        )

    def test_partial_golden_decoy_tree_only_still_wrong_collision(self) -> None:
        """Fixing legacy tree.sh without order.sh must not change ingest processing_order."""
        def check() -> None:
            tree = BUNDLES / "key-collision"
            seed = "base"
            out = OUTPUT / "partial-decoy-tree.json"
            proc = apply(tree, seed, out)
            assert proc.returncode == 0, proc.stderr
            got = json.loads(out.read_text(encoding="utf-8"))
            expect = reference_apply(tree, seed)
            assert got["processing_order"] != expect["processing_order"]

        with_partial_patch(
            {
                "parse.sh": GOLDEN / "golden_parse.sh",
                "merge.sh": GOLDEN / "golden_merge.sh",
                "layers.sh": GOLDEN / "golden_layers.sh",
                "tree.sh": GOLDEN / "golden_tree.sh",
            },
            check,
        )

    def test_partial_golden_merge_orchestrator_only_still_wrong_cascade_retain(self) -> None:
        """Golden merge.sh orchestrator alone still delegates to broken layers.sh."""
        def check() -> None:
            tree = BUNDLES / "cascade-retain"
            out = OUTPUT / "partial-merge-orchestrator.json"
            proc = apply(tree, SEEDS[0], out)
            assert proc.returncode == 0, proc.stderr
            got = json.loads(out.read_text(encoding="utf-8"))
            expect = reference_apply(tree, SEEDS[0])
            assert got != expect
            assert "retain.unique.main" not in got["effective"]

        with_partial_patch({"merge.sh": GOLDEN / "golden_merge.sh"}, check)

    def test_invalid_keys_apply_fails(self) -> None:
        """Malformed sysctl keys abort apply with exit code 3."""
        tree = BUNDLES / "invalid-keys"
        out = OUTPUT / "invalid-spot.json"
        proc = apply(tree, SEEDS[0], out)
        assert proc.returncode == 3, proc.stderr + proc.stdout
        assert not out.exists()

    def test_partial_golden_parse_only_still_wrong_comment_values(self) -> None:
        """Fixing only parse.sh still loses keys when merge replaces the whole map."""
        def check() -> None:
            tree = BUNDLES / "comment-values"
            out = OUTPUT / "partial-parse.json"
            proc = apply(tree, SEEDS[0], out)
            assert proc.returncode == 0, proc.stderr
            got = json.loads(out.read_text(encoding="utf-8"))
            expect = reference_apply(tree, SEEDS[0])
            assert got != expect

        with_partial_patch({"parse.sh": GOLDEN / "golden_parse.sh"}, check)

    def test_partial_golden_merge_only_still_wrong_override_stack(self) -> None:
        """Fixing only merge.sh still fails parse-sensitive trees with broken parse/tree."""
        def check() -> None:
            tree = BUNDLES / "comment-values"
            out = OUTPUT / "partial-merge.json"
            proc = apply(tree, SEEDS[0], out)
            assert proc.returncode == 0, proc.stderr
            got = json.loads(out.read_text(encoding="utf-8"))
            expect = reference_apply(tree, SEEDS[0])
            assert got != expect

        with_partial_patch({"merge.sh": GOLDEN / "golden_merge.sh"}, check)

    def test_partial_golden_tree_only_still_wrong_override_stack(self) -> None:
        """Fixing only legacy tree.sh does not repair ingest order or fragment accumulation."""
        def check() -> None:
            tree = BUNDLES / "override-stack"
            out = OUTPUT / "partial-tree.json"
            proc = apply(tree, SEEDS[0], out)
            assert proc.returncode == 0, proc.stderr
            got = json.loads(out.read_text(encoding="utf-8"))
            expect = reference_apply(tree, SEEDS[0])
            assert got != expect

        with_partial_patch({"tree.sh": GOLDEN / "golden_tree.sh"}, check)

    def test_intra_file_duplicate_last_line_wins(self) -> None:
        """Duplicate keys within one fragment must keep the last assignment and line."""
        tree = BUNDLES / "intra-duplicate"
        out = OUTPUT / "intra-dup-spot.json"
        proc = apply(tree, SEEDS[0], out)
        assert proc.returncode == 0, proc.stderr
        got = json.loads(out.read_text(encoding="utf-8"))
        expect = reference_apply(tree, SEEDS[0])
        assert got["effective"]["vm.swappiness"] == "15"
        assert got["sources"]["vm.swappiness"] == {"file": "sysctl.conf", "line": 2}
        assert got["sources"]["net.ipv4.ip_forward"] == {"file": "sysctl.d/10-dup.conf", "line": 2}
        assert got == expect

    @pytest.mark.parametrize("seed", SEEDS)
    def test_error_mid_stack_apply_fails(self, seed: str) -> None:
        """Invalid middle drop-in must abort even when earlier fragments parsed cleanly."""
        tree = BUNDLES / "error-mid-stack"
        out = OUTPUT / f"error-mid-{seed}.json"
        proc = apply(tree, seed, out)
        assert proc.returncode == 3, proc.stderr + proc.stdout
        assert not out.exists()

    def test_partial_golden_parse_tree_still_wrong_sources(self) -> None:
        """Per-key effective merge without provenance merge still fails override-stack."""
        def check() -> None:
            tree = BUNDLES / "override-stack"
            out = OUTPUT / "partial-sources.json"
            proc = apply(tree, SEEDS[0], out)
            assert proc.returncode == 0, proc.stderr
            got = json.loads(out.read_text(encoding="utf-8"))
            expect = reference_apply(tree, SEEDS[0])
            assert got["sources"] != expect["sources"]

        with_partial_patch(
            {"parse.sh": GOLDEN / "golden_parse.sh", "tree.sh": GOLDEN / "golden_tree.sh"},
            check,
        )

    def test_partial_golden_core_libs_broken_export_still_masks_exit_three(self) -> None:
        """Golden parse/tree/merge with broken export.sh still hides apply exit code 3."""
        def check() -> None:
            tree = BUNDLES / "invalid-keys"
            out = OUTPUT / "partial-export-mask.json"
            proc = apply(tree, SEEDS[0], out)
            assert proc.returncode == 0, proc.stderr + proc.stdout
            assert not out.exists()

        with_partial_patch(
            {
                "parse.sh": GOLDEN / "golden_parse.sh",
                "tree.sh": GOLDEN / "golden_tree.sh",
                "merge.sh": GOLDEN / "golden_merge.sh",
                "layers.sh": GOLDEN / "golden_layers.sh",
                "order.sh": GOLDEN / "golden_order.sh",
            },
            check,
        )

    def test_partial_golden_parse_tree_export_still_wrong_replace_merge(self) -> None:
        """Golden parse/tree/staging/export with replace-merge still drops retained keys."""
        def check() -> None:
            tree = BUNDLES / "cascade-retain"
            out = OUTPUT / "partial-replace-merge.json"
            proc = apply(tree, SEEDS[0], out)
            assert proc.returncode == 0, proc.stderr + proc.stdout
            got = json.loads(out.read_text(encoding="utf-8"))
            expect = reference_apply(tree, SEEDS[0])
            assert got != expect
            assert "retain.unique.main" not in got["effective"]

        with_partial_patch(
            {
                "parse.sh": GOLDEN / "golden_parse.sh",
                "tree.sh": GOLDEN / "golden_tree.sh",
                "staging.sh": GOLDEN / "golden_staging.sh",
                "export.sh": GOLDEN / "golden_export.sh",
                "guard.sh": GOLDEN / "golden_guard.sh",
                "replay.sh": GOLDEN / "golden_replay.sh",
            },
            check,
        )

    def test_cascade_retain_keeps_unrelated_keys(self) -> None:
        """Each drop-in overrides one key without dropping unrelated retained values."""
        tree = BUNDLES / "cascade-retain"
        out = OUTPUT / "cascade-retain-spot.json"
        proc = apply(tree, SEEDS[0], out)
        assert proc.returncode == 0, proc.stderr
        got = json.loads(out.read_text(encoding="utf-8"))
        expect = reference_apply(tree, SEEDS[0])
        assert got == expect
        assert got["effective"]["retain.unique.main"] == "keep"
        assert got["effective"]["retain.beta"] == "drop-b"
        assert got["effective"]["retain.gamma"] == "drop-c"

    def test_sparse_main_counts_main_in_stats(self) -> None:
        """Comment-only main still counts toward files_processed and processing_order."""
        tree = BUNDLES / "sparse-main"
        out = OUTPUT / "sparse-main-spot.json"
        proc = apply(tree, SEEDS[0], out)
        assert proc.returncode == 0, proc.stderr
        got = json.loads(out.read_text(encoding="utf-8"))
        expect = reference_apply(tree, SEEDS[0])
        assert got == expect
        assert got["processing_order"][0] == "sysctl.conf"
        assert got["stats"]["files_processed"] == len(got["processing_order"])

    def test_procedural_verifier_seed_tree_matches_reference(self) -> None:
        """VERIFIER_SEED procedural tree must match independent reference (anti hardcode)."""
        tree = procedural_tree(VERIFIER_SEED)
        out = OUTPUT / f"procedural-{VERIFIER_SEED}.json"
        proc = apply(tree, VERIFIER_SEED, out)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        got = json.loads(out.read_text(encoding="utf-8"))
        expect = reference_apply(tree, VERIFIER_SEED)
        assert got == expect

    def test_repeat_apply_is_deterministic(self) -> None:
        """Two applies with the same tree/seed must emit identical exports."""
        tree = BUNDLES / "key-collision"
        seed = SEEDS[1]
        first = OUTPUT / "repeat-a.json"
        second = OUTPUT / "repeat-b.json"
        proc_a = apply(tree, seed, first)
        proc_b = apply(tree, seed, second)
        assert proc_a.returncode == 0, proc_a.stderr
        assert proc_b.returncode == 0, proc_b.stderr
        assert json.loads(first.read_text(encoding="utf-8")) == json.loads(second.read_text(encoding="utf-8"))

    def test_partial_golden_merge_tree_export_still_wrong_first_duplicate(self) -> None:
        """Golden merge/tree/export with first-wins parse still keeps wrong intra-file winners."""
        def check() -> None:
            tree = BUNDLES / "intra-duplicate"
            out = OUTPUT / "partial-first-dup.json"
            proc = apply(tree, SEEDS[0], out)
            assert proc.returncode == 0, proc.stderr
            got = json.loads(out.read_text(encoding="utf-8"))
            expect = reference_apply(tree, SEEDS[0])
            assert got["effective"]["net.ipv4.ip_forward"] != expect["effective"]["net.ipv4.ip_forward"]
            assert got["effective"]["net.ipv4.ip_forward"] == "1"

        with_partial_patch(
            {
                "merge.sh": GOLDEN / "golden_merge.sh",
                "layers.sh": GOLDEN / "golden_layers.sh",
                "tree.sh": GOLDEN / "golden_tree.sh",
                "export.sh": GOLDEN / "golden_export.sh",
                "guard.sh": GOLDEN / "golden_guard.sh",
                "staging.sh": GOLDEN / "golden_staging.sh",
                "replay.sh": GOLDEN / "golden_replay.sh",
            },
            check,
        )

    def test_ingest_writes_snapshot_schema(self) -> None:
        """Ingest must write snapshot_version and merge fields per snapshot-schema.md."""
        tree = BUNDLES / "layered-precedence"
        snap = SNAPSHOT
        proc = ingest(tree, SEEDS[0], snap)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        doc = json.loads(snap.read_text(encoding="utf-8"))
        required = {
            "snapshot_version",
            "tree_path",
            "tree",
            "seed",
            "processing_order",
            "effective",
            "sources",
            "stats",
        }
        assert required <= set(doc.keys())
        assert doc["tree"] == tree.name
        assert doc["seed"] == SEEDS[0]

    def test_export_reads_snapshot_only(self) -> None:
        """Golden ingest snapshot plus broken export must still emit wrong apply_digest."""
        tree = BUNDLES / "layered-precedence"
        snap = SNAPSHOT
        out = OUTPUT / "snapshot-export-chain.json"

        def check() -> None:
            ing = ingest(tree, SEEDS[0], snap)
            assert ing.returncode == 0, ing.stderr
            exp = export_snapshot(snap, out)
            assert exp.returncode == 0, exp.stderr
            got = json.loads(out.read_text(encoding="utf-8"))
            expect = reference_apply(tree, SEEDS[0])
            assert got["effective"] == expect["effective"]
            assert got["apply_digest"] != expect["apply_digest"]

        with_partial_patch(dict(INGEST_CORE_GOLDEN), check)

    def test_apply_chains_ingest_export(self) -> None:
        """Apply output must match ingest then export with the same tree and seed."""
        tree = BUNDLES / "override-stack"
        snap = STATE / "chain-snapshot.json"
        chained = OUTPUT / "chained-export.json"
        direct = OUTPUT / "direct-apply.json"
        ing = ingest(tree, SEEDS[0], snap)
        assert ing.returncode == 0, ing.stderr
        exp = export_snapshot(snap, chained)
        assert exp.returncode == 0, exp.stderr
        proc = apply(tree, SEEDS[0], direct)
        assert proc.returncode == 0, proc.stderr
        assert json.loads(chained.read_text(encoding="utf-8")) == json.loads(
            direct.read_text(encoding="utf-8")
        )

    def test_partial_golden_merge_only_export_wrong_digest(self) -> None:
        """Correct snapshot with broken export still binds the wrong apply_digest."""
        def check() -> None:
            tree = BUNDLES / "layered-precedence"
            out = OUTPUT / "partial-merge-export-digest.json"
            proc = apply(tree, SEEDS[0], out)
            assert proc.returncode == 0, proc.stderr
            got = json.loads(out.read_text(encoding="utf-8"))
            expect = reference_apply(tree, SEEDS[0])
            assert got["effective"] == expect["effective"]
            assert got["apply_digest"] != expect["apply_digest"]

        with_partial_patch(
            {
                **INGEST_CORE_GOLDEN,
                "staging.sh": GOLDEN / "golden_staging.sh",
                "replay.sh": GOLDEN / "golden_replay.sh",
            },
            check,
        )

    def test_ingest_aborts_without_snapshot_on_error(self) -> None:
        """Invalid-keys ingest must exit 3 and leave no snapshot file."""
        tree = BUNDLES / "invalid-keys"
        snap = STATE / "should-not-exist.json"
        if snap.exists():
            snap.unlink()
        proc = ingest(tree, SEEDS[0], snap)
        assert proc.returncode == 3, proc.stderr + proc.stdout
        assert not snap.exists()
        assert not reference_staging_path(snap).exists()

    def test_ingest_writes_merge_staging_digest(self) -> None:
        """Successful ingest must write sibling merge-staging with matching digest."""
        tree = BUNDLES / "override-stack"
        snap = STATE / "staging-check.json"

        def check() -> None:
            proc = ingest(tree, SEEDS[0], snap)
            assert proc.returncode == 0, proc.stderr + proc.stdout
            meta = json.loads(snap.read_text(encoding="utf-8"))
            staging_path = reference_staging_path(snap)
            assert staging_path.is_file()
            got = json.loads(staging_path.read_text(encoding="utf-8"))
            expect = reference_staging(tree, meta)
            assert got == expect
            assert got["snapshot_digest"] == snapshot_digest(meta)

        with_partial_patch(
            {
                "merge.sh": GOLDEN / "golden_merge.sh",
                "digest.sh": GOLDEN / "golden_digest.sh",
                "staging.sh": GOLDEN / "golden_staging.sh",
            },
            check,
        )

    def test_export_fails_when_staging_missing(self) -> None:
        """Export must exit 4 when merge-staging is absent for a valid snapshot."""
        tree = BUNDLES / "layered-precedence"
        snap = STATE / "no-staging.json"
        out = OUTPUT / "missing-staging.json"

        def check() -> None:
            ing = ingest(tree, SEEDS[0], snap)
            assert ing.returncode == 0, ing.stderr
            staging_path = reference_staging_path(snap)
            staging_path.unlink()
            exp = export_snapshot(snap, out)
            assert exp.returncode == 4, exp.stderr + exp.stdout
            assert not out.exists()

        with_partial_patch(
            {
                "merge.sh": GOLDEN / "golden_merge.sh",
                "staging.sh": GOLDEN / "golden_staging.sh",
                "export.sh": GOLDEN / "golden_export.sh",
                "guard.sh": GOLDEN / "golden_guard.sh",
                "replay.sh": GOLDEN / "golden_replay.sh",
            },
            check,
        )

    def test_partial_golden_merge_export_broken_staging_fails_export(self) -> None:
        """Golden merge/export with wrong staging digest must abort export with exit 4."""
        def check() -> None:
            tree = BUNDLES / "layered-precedence"
            snap = STATE / "bad-staging-digest.json"
            out = OUTPUT / "bad-staging-export.json"
            ing = ingest(tree, SEEDS[0], snap)
            assert ing.returncode == 0, ing.stderr
            exp = export_snapshot(snap, out)
            assert exp.returncode == 4, exp.stderr + exp.stdout
            assert not out.exists()

        with_partial_patch(
            {
                "merge.sh": GOLDEN / "golden_merge.sh",
                "digest.sh": GOLDEN / "golden_digest.sh",
                "export.sh": GOLDEN / "golden_export.sh",
                "guard.sh": GOLDEN / "golden_guard.sh",
                "replay.sh": GOLDEN / "golden_replay.sh",
            },
            check,
        )

    def test_partial_golden_merge_staging_broken_export_wrong_digest(self) -> None:
        """Correct snapshot/staging with broken export still binds the wrong apply_digest."""
        def check() -> None:
            tree = BUNDLES / "layered-precedence"
            out = OUTPUT / "partial-staging-export-digest.json"
            proc = apply(tree, SEEDS[0], out)
            assert proc.returncode == 0, proc.stderr
            got = json.loads(out.read_text(encoding="utf-8"))
            expect = reference_apply(tree, SEEDS[0])
            assert got["effective"] == expect["effective"]
            assert got["apply_digest"] != expect["apply_digest"]

        with_partial_patch(
            {
                **INGEST_CORE_GOLDEN,
                "staging.sh": GOLDEN / "golden_staging.sh",
            },
            check,
        )

    def test_apply_chains_staging_validation(self) -> None:
        """Apply must fail when ingest wrote snapshot but staging digest is wrong."""
        tree = BUNDLES / "cascade-retain"
        snap = STATE / "chain-staging-bad.json"
        out = OUTPUT / "chain-staging-bad.json"

        def check() -> None:
            ing = ingest(tree, SEEDS[0], snap)
            assert ing.returncode == 0, ing.stderr
            staging_path = reference_staging_path(snap)
            staging = json.loads(staging_path.read_text(encoding="utf-8"))
            staging["snapshot_digest"] = "0" * 64
            staging_path.write_text(json.dumps(staging, indent=2) + "\n", encoding="utf-8")
            exp = export_snapshot(snap, out)
            assert exp.returncode == 4, exp.stderr + exp.stdout
            assert not out.exists()

        with_partial_patch(
            {
                "merge.sh": GOLDEN / "golden_merge.sh",
                "export.sh": GOLDEN / "golden_export.sh",
                "guard.sh": GOLDEN / "golden_guard.sh",
                "staging.sh": GOLDEN / "golden_staging.sh",
                "replay.sh": GOLDEN / "golden_replay.sh",
            },
            check,
        )

    def test_apply_digest_matches_reference(self) -> None:
        """apply_digest must match independent reference binding."""
        tree = BUNDLES / "override-stack"
        out = OUTPUT / "apply-digest.json"
        proc = apply(tree, SEEDS[0], out)
        assert proc.returncode == 0, proc.stderr
        got = json.loads(out.read_text(encoding="utf-8"))
        expect = reference_apply(tree, SEEDS[0])
        assert got["apply_digest"] == expect["apply_digest"]
        assert got["apply_digest"] == snapshot_digest(
            {
                "processing_order": got["processing_order"],
                "effective": got["effective"],
                "sources": got["sources"],
            }
        )

    def test_replay_ledger_written_on_ingest(self) -> None:
        """Successful ingest must append a replay ledger record bound to the snapshot."""
        tree = BUNDLES / "cascade-retain"
        snap = STATE / "replay-ingest.json"

        def check() -> None:
            proc = ingest(tree, SEEDS[0], snap)
            assert proc.returncode == 0, proc.stderr + proc.stdout
            assert REPLAY_LEDGER.is_file()
            meta = json.loads(snap.read_text(encoding="utf-8"))
            lines = [ln for ln in REPLAY_LEDGER.read_text(encoding="utf-8").splitlines() if ln.strip()]
            assert lines
            record = json.loads(lines[-1])
            assert record["tree"] == meta["tree"]
            assert record["seed"] == meta["seed"]
            assert record["snapshot_digest"] == snapshot_digest(meta)
            assert record["files_processed"] == meta["stats"]["files_processed"]
            staging_path = reference_staging_path(snap)
            staging = json.loads(staging_path.read_text(encoding="utf-8"))
            layer_digest = hashlib.sha256(
                json.dumps(staging["layer_keys"], sort_keys=True, separators=(",", ":")).encode(
                    "utf-8"
                )
            ).hexdigest()
            assert record["layer_keys_digest"] == layer_digest

        with_partial_patch(
            {
                "merge.sh": GOLDEN / "golden_merge.sh",
                "digest.sh": GOLDEN / "golden_digest.sh",
                "staging.sh": GOLDEN / "golden_staging.sh",
                "replay.sh": GOLDEN / "golden_replay.sh",
            },
            check,
        )

    def test_export_fails_without_replay_ledger(self) -> None:
        """Export must exit 5 when replay ledger is missing."""
        tree = BUNDLES / "layered-precedence"
        snap = STATE / "no-replay-ledger.json"
        out = OUTPUT / "missing-replay.json"

        def check() -> None:
            ing = ingest(tree, SEEDS[0], snap)
            assert ing.returncode == 0, ing.stderr
            if REPLAY_LEDGER.exists():
                REPLAY_LEDGER.unlink()
            exp = export_snapshot(snap, out)
            assert exp.returncode == 5, exp.stderr + exp.stdout
            assert not out.exists()

        with_partial_patch(
            {
                "merge.sh": GOLDEN / "golden_merge.sh",
                "staging.sh": GOLDEN / "golden_staging.sh",
                "export.sh": GOLDEN / "golden_export.sh",
                "guard.sh": GOLDEN / "golden_guard.sh",
                "replay.sh": GOLDEN / "golden_replay.sh",
            },
            check,
        )

    def test_export_fails_replay_digest_mismatch(self) -> None:
        """Export must exit 5 when ledger snapshot_digest does not match snapshot."""
        tree = BUNDLES / "sparse-main"
        snap = STATE / "bad-replay-digest.json"
        out = OUTPUT / "bad-replay-export.json"

        def check() -> None:
            ing = ingest(tree, SEEDS[0], snap)
            assert ing.returncode == 0, ing.stderr
            lines = REPLAY_LEDGER.read_text(encoding="utf-8").splitlines()
            record = json.loads(lines[-1])
            record["snapshot_digest"] = "0" * 64
            lines[-1] = json.dumps(record, sort_keys=True, separators=(",", ":"))
            REPLAY_LEDGER.write_text("\n".join(lines) + "\n", encoding="utf-8")
            exp = export_snapshot(snap, out)
            assert exp.returncode == 5, exp.stderr + exp.stdout
            assert not out.exists()

        with_partial_patch(
            {
                "merge.sh": GOLDEN / "golden_merge.sh",
                "staging.sh": GOLDEN / "golden_staging.sh",
                "export.sh": GOLDEN / "golden_export.sh",
                "guard.sh": GOLDEN / "golden_guard.sh",
                "replay.sh": GOLDEN / "golden_replay.sh",
            },
            check,
        )

    def test_export_fails_replay_layer_keys_digest_mismatch(self) -> None:
        """Export must exit 5 when ledger layer_keys_digest does not match staging."""
        tree = BUNDLES / "quoted-values"
        snap = STATE / "bad-layer-digest.json"
        out = OUTPUT / "bad-layer-export.json"

        def check() -> None:
            ing = ingest(tree, SEEDS[0], snap)
            assert ing.returncode == 0, ing.stderr
            lines = REPLAY_LEDGER.read_text(encoding="utf-8").splitlines()
            record = json.loads(lines[-1])
            record["layer_keys_digest"] = "0" * 64
            lines[-1] = json.dumps(record, sort_keys=True, separators=(",", ":"))
            REPLAY_LEDGER.write_text("\n".join(lines) + "\n", encoding="utf-8")
            exp = export_snapshot(snap, out)
            assert exp.returncode == 5, exp.stderr + exp.stdout
            assert not out.exists()

        with_partial_patch(
            {
                "parse.sh": GOLDEN / "golden_parse.sh",
                "normalize.sh": GOLDEN / "golden_normalize.sh",
                "tree.sh": GOLDEN / "golden_tree.sh",
                "merge.sh": GOLDEN / "golden_merge.sh",
                "staging.sh": GOLDEN / "golden_staging.sh",
                "export.sh": GOLDEN / "golden_export.sh",
                "guard.sh": GOLDEN / "golden_guard.sh",
                "replay.sh": GOLDEN / "golden_replay.sh",
            },
            check,
        )

    def test_verify_aligned_after_ingest(self) -> None:
        """verify must report aligned staging/replay after ingest."""
        tree = BUNDLES / "layered-precedence"
        snap = STATE / "verify-aligned.json"

        def check() -> None:
            assert ingest(tree, SEEDS[0], snap).returncode == 0
            code, body = verify_snapshot(snap)
            assert code == 0
            assert body.get("aligned") is True

        with_partial_patch(
            {
                "parse.sh": GOLDEN / "golden_parse.sh",
                "normalize.sh": GOLDEN / "golden_normalize.sh",
                "tree.sh": GOLDEN / "golden_tree.sh",
                "order.sh": GOLDEN / "golden_order.sh",
                "layers.sh": GOLDEN / "golden_layers.sh",
                "merge.sh": GOLDEN / "golden_merge.sh",
                **EXPORT_GATE_GOLDEN,
            },
            check,
        )

    def test_verify_misaligned_after_tampered_replay_ledger(self) -> None:
        """verify must report misalignment when replay ledger was tampered."""
        tree = BUNDLES / "override-stack"
        snap = STATE / "verify-tamper.json"

        def check() -> None:
            assert ingest(tree, SEEDS[0], snap).returncode == 0
            lines = REPLAY_LEDGER.read_text(encoding="utf-8").splitlines()
            record = json.loads(lines[-1])
            record["snapshot_digest"] = "0" * 64
            lines[-1] = json.dumps(record, sort_keys=True, separators=(",", ":"))
            REPLAY_LEDGER.write_text("\n".join(lines) + "\n", encoding="utf-8")
            code, body = verify_snapshot(snap)
            assert code == 1
            assert body.get("aligned") is False

        with_partial_patch(
            {
                "parse.sh": GOLDEN / "golden_parse.sh",
                "normalize.sh": GOLDEN / "golden_normalize.sh",
                "tree.sh": GOLDEN / "golden_tree.sh",
                "order.sh": GOLDEN / "golden_order.sh",
                "layers.sh": GOLDEN / "golden_layers.sh",
                "merge.sh": GOLDEN / "golden_merge.sh",
                **EXPORT_GATE_GOLDEN,
            },
            check,
        )

    def test_partial_golden_without_guard_allows_tampered_replay_export(self) -> None:
        """Golden modules except guard must export after replay ledger tampering."""
        tree = BUNDLES / "cascade-retain"
        snap = STATE / "partial-guard-tamper.json"
        out = OUTPUT / "partial-guard-export.json"

        def check() -> None:
            assert ingest(tree, SEEDS[0], snap).returncode == 0
            lines = REPLAY_LEDGER.read_text(encoding="utf-8").splitlines()
            record = json.loads(lines[-1])
            record["snapshot_digest"] = "0" * 64
            lines[-1] = json.dumps(record, sort_keys=True, separators=(",", ":"))
            REPLAY_LEDGER.write_text("\n".join(lines) + "\n", encoding="utf-8")
            exp = export_snapshot(snap, out)
            assert exp.returncode == 0, exp.stderr + exp.stdout

        with_partial_patch(
            {
                "parse.sh": GOLDEN / "golden_parse.sh",
                "normalize.sh": GOLDEN / "golden_normalize.sh",
                "tree.sh": GOLDEN / "golden_tree.sh",
                "order.sh": GOLDEN / "golden_order.sh",
                "layers.sh": GOLDEN / "golden_layers.sh",
                "merge.sh": GOLDEN / "golden_merge.sh",
                "staging.sh": GOLDEN / "golden_staging.sh",
                "replay.sh": GOLDEN / "golden_replay.sh",
                "export.sh": GOLDEN / "golden_export.sh",
            },
            check,
        )

    def test_quoted_values_normalization_matches_reference(self) -> None:
        """Quoted sysctl values must be normalized in effective map."""
        tree = BUNDLES / "quoted-values"
        out = OUTPUT / "quoted-values-spot.json"
        proc = apply(tree, SEEDS[0], out)
        assert proc.returncode == 0, proc.stderr
        got = json.loads(out.read_text(encoding="utf-8"))
        expect = reference_apply(tree, SEEDS[0])
        assert got == expect
        assert got["effective"]["vm.overcommit_memory"] == "1"
        assert got["effective"]["net.ipv4.tcp_mem"] == "1024 2048 4096"

    def test_partial_golden_normalize_only_still_wrong_quoted_values(self) -> None:
        """Golden parse/tree/merge with broken normalize keeps quoted literals in effective."""
        def check() -> None:
            tree = BUNDLES / "quoted-values"
            out = OUTPUT / "partial-normalize.json"
            proc = apply(tree, SEEDS[0], out)
            assert proc.returncode == 0, proc.stderr
            got = json.loads(out.read_text(encoding="utf-8"))
            expect = reference_apply(tree, SEEDS[0])
            assert got["effective"] != expect["effective"]
            assert got["effective"]["net.ipv4.tcp_mem"] == '"1024 2048 4096"'

        with_partial_patch(
            {
                "parse.sh": GOLDEN / "golden_parse.sh",
                "tree.sh": GOLDEN / "golden_tree.sh",
                "merge.sh": GOLDEN / "golden_merge.sh",
                "layers.sh": GOLDEN / "golden_layers.sh",
                "order.sh": GOLDEN / "golden_order.sh",
                "staging.sh": GOLDEN / "golden_staging.sh",
                "replay.sh": GOLDEN / "golden_replay.sh",
                "export.sh": GOLDEN / "golden_export.sh",
                "guard.sh": GOLDEN / "golden_guard.sh",
            },
            check,
        )

    def test_hidden_escaped_quotes_matches_reference(self) -> None:
        """Hidden bundle with escaped interior quotes must normalize correctly."""

        def check() -> None:
            with hidden_bundle("hidden-escaped-quotes") as tree:
                out = OUTPUT / "hidden-escaped.json"
                proc = apply(tree, SEEDS[0], out)
                assert proc.returncode == 0, proc.stderr
                got = json.loads(out.read_text(encoding="utf-8"))
                expect = reference_apply(tree, SEEDS[0])
                assert got == expect
                assert got["effective"]["custom.test.quoted"] == '"inner"'

        check()

    def test_hidden_cascade_trap_matches_reference(self) -> None:
        """Hidden sparse drop-ins must retain unrelated main keys across the cascade."""

        def check() -> None:
            with hidden_bundle("hidden-cascade-trap") as tree:
                out = OUTPUT / "hidden-cascade-trap.json"
                proc = apply(tree, SEEDS[0], out)
                assert proc.returncode == 0, proc.stderr
                got = json.loads(out.read_text(encoding="utf-8"))
                expect = reference_apply(tree, SEEDS[0])
                assert got == expect
                assert got["effective"]["trap.keep.gamma"] == "main-gamma"
                assert got["effective"]["trap.winner.key"] == "drop-final"

        check()

    def test_partial_golden_all_but_merge_still_wrong_hidden_cascade_trap(self) -> None:
        """Golden parse/tree/export with replace-merge still drops unrelated hidden keys."""

        def check() -> None:
            with hidden_bundle("hidden-cascade-trap") as tree:
                out = OUTPUT / "partial-hidden-cascade.json"
                proc = apply(tree, SEEDS[0], out)
                assert proc.returncode == 0, proc.stderr
                got = json.loads(out.read_text(encoding="utf-8"))
                expect = reference_apply(tree, SEEDS[0])
                assert got != expect
                assert "trap.keep.gamma" not in got["effective"]

        with_partial_patch(
            {
                "parse.sh": GOLDEN / "golden_parse.sh",
                "normalize.sh": GOLDEN / "golden_normalize.sh",
                "tree.sh": GOLDEN / "golden_tree.sh",
                "order.sh": GOLDEN / "golden_order.sh",
                "staging.sh": GOLDEN / "golden_staging.sh",
                "replay.sh": GOLDEN / "golden_replay.sh",
                "export.sh": GOLDEN / "golden_export.sh",
                "guard.sh": GOLDEN / "golden_guard.sh",
            },
            check,
        )

    def test_layer_keys_per_fragment_matches_reference(self) -> None:
        """Merge-staging layer_keys must list per-file keys in parse order."""
        tree = BUNDLES / "intra-duplicate"
        snap = STATE / "layer-keys.json"

        def check() -> None:
            proc = ingest(tree, SEEDS[0], snap)
            assert proc.returncode == 0, proc.stderr
            meta = json.loads(snap.read_text(encoding="utf-8"))
            staging_path = reference_staging_path(snap)
            got = json.loads(staging_path.read_text(encoding="utf-8"))
            expect = reference_staging(tree, meta)
            assert got["layer_keys"] == expect["layer_keys"]

        with_partial_patch(
            {
                "merge.sh": GOLDEN / "golden_merge.sh",
                "staging.sh": GOLDEN / "golden_staging.sh",
                "replay.sh": GOLDEN / "golden_replay.sh",
            },
            check,
        )

    def test_partial_golden_replay_only_still_fails_apply(self) -> None:
        """Golden replay alone must not satisfy apply when merge and export remain broken."""
        tree = BUNDLES / "whitespace-sep"
        out = OUTPUT / "partial-replay-only.json"
        expect = reference_apply(tree, SEEDS[0])

        def check() -> None:
            proc = apply(tree, SEEDS[0], out)
            if proc.returncode != 0 or not out.is_file():
                return
            got = json.loads(out.read_text(encoding="utf-8"))
            if got != expect:
                return
            raise AssertionError("partial replay-only patch produced full reference output")

        with_partial_patch({"replay.sh": GOLDEN / "golden_replay.sh"}, check)

    def test_split_stage_export_replay_matches_apply(self) -> None:
        """Split ingest/export with replay validation must match apply."""
        tree = BUNDLES / "key-collision"
        snap = STATE / "split-replay.json"
        chained = OUTPUT / "split-replay-export.json"
        direct = OUTPUT / "split-replay-apply.json"

        def check() -> None:
            assert ingest(tree, SEEDS[2], snap).returncode == 0
            assert export_snapshot(snap, chained).returncode == 0
            proc = apply(tree, SEEDS[2], direct)
            assert proc.returncode == 0, proc.stderr
            assert json.loads(chained.read_text(encoding="utf-8")) == json.loads(
                direct.read_text(encoding="utf-8")
            )

        with_partial_patch(
            {
                "parse.sh": GOLDEN / "golden_parse.sh",
                "tree.sh": GOLDEN / "golden_tree.sh",
                "merge.sh": GOLDEN / "golden_merge.sh",
                "layers.sh": GOLDEN / "golden_layers.sh",
                "order.sh": GOLDEN / "golden_order.sh",
                "staging.sh": GOLDEN / "golden_staging.sh",
                "export.sh": GOLDEN / "golden_export.sh",
                "guard.sh": GOLDEN / "golden_guard.sh",
                "replay.sh": GOLDEN / "golden_replay.sh",
            },
            check,
        )

    def test_hidden_tab_sep_matches_reference(self) -> None:
        """Hidden bundle with tab-separated assignments must parse and merge correctly."""

        def check() -> None:
            with hidden_bundle("hidden-tab-sep") as tree:
                out = OUTPUT / "hidden-tab-sep.json"
                proc = apply(tree, SEEDS[0], out)
                assert proc.returncode == 0, proc.stderr
                got = json.loads(out.read_text(encoding="utf-8"))
                expect = reference_apply(tree, SEEDS[0])
                assert got == expect
                assert got["effective"]["tab.drop.key"] == "from-drop"

        check()

    def test_hidden_interior_hash_matches_reference(self) -> None:
        """Hidden bundle must retain interior # characters when not preceded by whitespace."""

        def check() -> None:
            with hidden_bundle("hidden-interior-hash") as tree:
                out = OUTPUT / "hidden-interior-hash.json"
                proc = apply(tree, SEEDS[0], out)
                assert proc.returncode == 0, proc.stderr
                got = json.loads(out.read_text(encoding="utf-8"))
                expect = reference_apply(tree, SEEDS[0])
                assert got == expect
                assert got["effective"]["custom.interior.hash"] == "foo#bar"
                assert got["effective"]["other.keep.key"] == "drop-value"

        check()

    def test_partial_golden_all_but_digest_still_wrong_apply_digest(self) -> None:
        """Golden ingest/export stack with broken digest.sh still binds wrong digests."""
        def check() -> None:
            tree = BUNDLES / "override-stack"
            out = OUTPUT / "partial-no-digest.json"
            proc = apply(tree, SEEDS[0], out)
            assert proc.returncode == 0, proc.stderr
            got = json.loads(out.read_text(encoding="utf-8"))
            expect = reference_apply(tree, SEEDS[0])
            assert got["effective"] == expect["effective"]
            assert got["apply_digest"] != expect["apply_digest"]

        with_partial_patch(
            {
                **INGEST_CORE_GOLDEN,
                "normalize.sh": GOLDEN / "golden_normalize.sh",
                **EXPORT_GATE_GOLDEN,
            },
            check,
        )

    def test_partial_golden_parse_only_still_wrong_hidden_interior_hash(self) -> None:
        """Fixing parse.sh alone still mishandles interior # on hidden fixtures."""

        def check() -> None:
            with hidden_bundle("hidden-interior-hash") as tree:
                out = OUTPUT / "partial-hidden-interior.json"
                proc = apply(tree, SEEDS[0], out)
                assert proc.returncode == 0, proc.stderr
                got = json.loads(out.read_text(encoding="utf-8"))
                expect = reference_apply(tree, SEEDS[0])
                assert got != expect
                assert got["effective"].get("custom.interior.hash") != "foo#bar"

        with_partial_patch({"parse.sh": GOLDEN / "golden_parse.sh"}, check)

    def test_partial_golden_ingest_without_digest_still_wrong_replay(self) -> None:
        """Golden ingest/export without digest.sh still writes wrong replay snapshot_digest."""
        tree = BUNDLES / "sparse-main"
        snap = STATE / "partial-no-digest-replay.json"

        def check() -> None:
            proc = ingest(tree, SEEDS[0], snap)
            assert proc.returncode == 0, proc.stderr + proc.stdout
            meta = json.loads(snap.read_text(encoding="utf-8"))
            lines = [ln for ln in REPLAY_LEDGER.read_text(encoding="utf-8").splitlines() if ln.strip()]
            record = json.loads(lines[-1])
            assert record["snapshot_digest"] != snapshot_digest(meta)

        with_partial_patch(
            {
                **INGEST_CORE_GOLDEN,
                "normalize.sh": GOLDEN / "golden_normalize.sh",
                "staging.sh": GOLDEN / "golden_staging.sh",
                "replay.sh": GOLDEN / "golden_replay.sh",
            },
            check,
        )

    def test_partial_golden_bind_only_still_wrong_apply_digest(self) -> None:
        """Fixing legacy bind.sh without digest.sh still binds wrong apply_digest on export."""
        def check() -> None:
            tree = BUNDLES / "override-stack"
            out = OUTPUT / "partial-bind-only.json"
            proc = apply(tree, SEEDS[0], out)
            assert proc.returncode == 0, proc.stderr
            got = json.loads(out.read_text(encoding="utf-8"))
            expect = reference_apply(tree, SEEDS[0])
            assert got["effective"] == expect["effective"]
            assert got["apply_digest"] != expect["apply_digest"]

        with_partial_patch(
            {
                **INGEST_CORE_GOLDEN,
                "normalize.sh": GOLDEN / "golden_normalize.sh",
                "bind.sh": GOLDEN / "golden_bind.sh",
                **EXPORT_GATE_GOLDEN,
            },
            check,
        )

    def test_partial_golden_digest_only_still_wrong_staging_digest(self) -> None:
        """Correct digest.sh with staging still on legacy bind must write wrong staging digest."""
        tree = BUNDLES / "cascade-retain"
        snap = STATE / "partial-digest-only-staging.json"

        def check() -> None:
            proc = ingest(tree, SEEDS[0], snap)
            assert proc.returncode == 0, proc.stderr + proc.stdout
            meta = json.loads(snap.read_text(encoding="utf-8"))
            staging_path = reference_staging_path(snap)
            got = json.loads(staging_path.read_text(encoding="utf-8"))
            expect = reference_staging(tree, meta)
            assert got["snapshot_digest"] != expect["snapshot_digest"]
            assert got["snapshot_digest"] != snapshot_digest(meta)

        with_partial_patch(
            {
                **INGEST_CORE_GOLDEN,
                "normalize.sh": GOLDEN / "golden_normalize.sh",
                "digest.sh": GOLDEN / "golden_digest.sh",
                "replay.sh": GOLDEN / "golden_replay.sh",
            },
            check,
        )

    def test_partial_golden_bind_digest_still_wrong_staging_layer_keys(self) -> None:
        """Golden bind/digest without staging rewrite still writes wrong per-file layer_keys."""
        tree = BUNDLES / "override-stack"
        snap = STATE / "partial-bind-digest-staging-keys.json"

        def check() -> None:
            proc = ingest(tree, SEEDS[0], snap)
            assert proc.returncode == 0, proc.stderr + proc.stdout
            meta = json.loads(snap.read_text(encoding="utf-8"))
            staging_path = reference_staging_path(snap)
            got = json.loads(staging_path.read_text(encoding="utf-8"))
            expect = reference_staging(tree, meta)
            assert got["snapshot_digest"] == expect["snapshot_digest"]
            assert got["layer_keys"] != expect["layer_keys"]

        with_partial_patch(
            {
                **INGEST_CORE_GOLDEN,
                "normalize.sh": GOLDEN / "golden_normalize.sh",
                "digest.sh": GOLDEN / "golden_digest.sh",
                "bind.sh": GOLDEN / "golden_bind.sh",
            },
            check,
        )
