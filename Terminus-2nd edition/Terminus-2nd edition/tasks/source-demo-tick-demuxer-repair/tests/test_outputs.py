"""
Verifier for source-demo tick demuxer repair.

Compares demo-index CLI output against an independent byte-level reference parser.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from reference_parser import BUILD_FILES, PROBE_TRUNC, reference_build

APP = Path("/app")
CLI = APP / "bin/demo-index"
DEMOS = APP / "fixtures/demos"
SEEDS = APP / "fixtures/seeds.json"
OUT = APP / "output/tick-index.json"
RESET = APP / "scripts/reset-state.sh"
HIDDEN_FIXTURE_ROOT = Path("/opt/verifier-fixtures/demos")

SEED_PRIMARY = "primary01"
ALT_SEEDS = ("alt_gamma", "alt_delta")

# Verifier-side baseline digests (shipping environment tree). Not computed at import time.
PROTECTED_SHA256: dict[str, str] = {
    "fixtures/demos/alpha/late.dem": "1215dad327d602dc2a1678e15644eae18539594baba3b8bdf23a2c18a112e29c",
    "fixtures/demos/beta/early.dem": "bf8ab8db72dc8fbe0e118dd4f896eb9d4954478a30afa1749ed6135a65067c26",
    "fixtures/demos/loop/session.dem": "6f82f34c10d5bff2dee60687a9afb212734fd476c8061735080fc642ba13aa8e",
    "fixtures/demos/signon/reset.dem": "8fec86ad1cbc962e67ea315065862a374b403921abb81faf704efed88bbb621e",
    "fixtures/demos/strings/highidx.dem": "b3c0a131ab6a897407b55538c62fa5ee4dc6f976a81852bf89817827e67244b5",
    "fixtures/demos/broken/trunc.dem": "ba6d279ff478349c2e21a240ac6858ffaf35abb7aa16befe0d43f2053a6edf2d",
    "fixtures/seeds.json": "71e40013b00d158f801f15e88bdf9b3317c03694df528653c341e4dd7c2ef2d8",
    "docs/index-schema.md": "7b6baa5b332f4d2856b693282dd436bc7523af86ee2d2289b50e318faa4738f1",
    "docs/fixture-catalog.md": "bd7ca92a0e6de9ac45b6e0e4ef7733741842a21e2d41e7af3c7155831cbe9179",
    "docs/exit-codes.md": "1c9a0bda13e29cda27ce1430000b228df2645276c40d9d4c1eee957c4cd01dd6",
    "docs/demo-format.md": "e9539eff3c442d87aeb305cdf5444ef100914ac1e6451a6b6119ab2c2d986fdb",
    "tools/gendemo.py": "cf21b8ba51844de375e7dfcd04f4566cd6f63d6b67a4ee88061522a98afade2b",
    "src/demux.c": "0ab6f666b00aab8f11f5a4ae5117ad1bdb6f61a160d08b530791fb113aad1840",
}


def sha256_file(rel: str) -> str:
    return hashlib.sha256((APP / rel).read_bytes()).hexdigest()


def reset() -> None:
    subprocess.run(["bash", str(RESET)], check=True)


def run_build(seed: str, out: Path | None = None, *, root: Path | None = None) -> subprocess.CompletedProcess[str]:
    out = out or OUT
    root = root or DEMOS
    out.parent.mkdir(parents=True, exist_ok=True)
    return subprocess.run(
        [str(CLI), "build", "--root", str(root), "--seed", seed, "--out", str(out)],
        capture_output=True,
        text=True,
        timeout=180,
    )


def run_probe(demo: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(CLI), "probe", "--demo", str(demo)],
        capture_output=True,
        text=True,
        timeout=60,
    )


def load_export(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class TestDemoIndexRepair:
    """Behavioral checks for demo-index build and probe."""

    def test_protected_paths_unchanged(self) -> None:
        """Protected docs, fixtures, gendemo.py, and demux.c must not be edited by agents."""
        for rel, expected in PROTECTED_SHA256.items():
            path = APP / rel
            assert path.is_file(), f"missing protected path {rel}"
            assert sha256_file(rel) == expected, f"protected path mutated: {rel}"

    def test_build_primary_matches_reference(self) -> None:
        """Full-tree build for primary seed matches independent parser."""
        reset()
        proc = run_build(SEED_PRIMARY)
        assert proc.returncode == 0, proc.stderr
        got = load_export(OUT)
        want = reference_build(DEMOS, SEED_PRIMARY)
        assert got == want

    def test_merge_order_uses_full_relative_paths(self) -> None:
        """alpha/late.dem must precede beta/early.dem (not basename sort)."""
        reset()
        proc = run_build(SEED_PRIMARY)
        assert proc.returncode == 0, proc.stderr
        files = load_export(OUT)["files"]
        assert files.index("alpha/late.dem") < files.index("beta/early.dem")

    def test_signon_reset_tick_base(self) -> None:
        """SIGNON_RESET shifts later global ticks in signon/reset.dem."""
        reset()
        run_build(SEED_PRIMARY)
        ticks = load_export(OUT)["ticks"]
        post = [t for t in ticks if t["source"] == "signon/reset.dem" and t["global_tick"] >= 1000]
        assert any(t["global_tick"] == 1001 for t in post)
        assert any(t["global_tick"] == 1003 for t in post)
        assert load_export(OUT)["stats"]["signon_resets"] == 1

    def test_unsigned_string_index_highidx(self) -> None:
        """String index 129 resolves to str_129, not a negative index."""
        reset()
        run_build(SEED_PRIMARY)
        rows = [t for t in load_export(OUT)["ticks"] if t["source"] == "strings/highidx.dem"]
        assert len(rows) == 1
        cmd = rows[0]["usercmds"][0]
        assert cmd["str_idx"] == 129
        assert cmd["string"] == "str_129"

    def test_loop_replay_dedupes_usercmds(self) -> None:
        """loops_packet_stream must not duplicate usercmds on second pass."""
        reset()
        run_build(SEED_PRIMARY)
        loop_rows = [t for t in load_export(OUT)["ticks"] if t["source"] == "loop/session.dem"]
        usercmd_total = sum(len(t["usercmds"]) for t in loop_rows)
        assert usercmd_total == 2

    def test_probe_truncated_demo_exits_two(self) -> None:
        """Partial packet at EOF returns exit code 2 per exit-codes.md."""
        reset()
        proc = run_probe(DEMOS / PROBE_TRUNC)
        assert proc.returncode == 2, proc.stderr

    def test_probe_valid_demo_exits_zero(self) -> None:
        """Non-truncated demo probe succeeds."""
        reset()
        proc = run_probe(DEMOS / "alpha/late.dem")
        assert proc.returncode == 0, proc.stderr

    def test_alternate_seed_mutates_args(self) -> None:
        """Alternate seed export matches reference and differs from primary on salted args."""
        reset()
        run_build(SEED_PRIMARY, APP / "output/primary.json")
        proc = run_build(ALT_SEEDS[0], APP / "output/alt.json")
        assert proc.returncode == 0, proc.stderr
        p = load_export(APP / "output/primary.json")
        a = load_export(APP / "output/alt.json")
        assert a == reference_build(DEMOS, ALT_SEEDS[0])
        prow = next(
            t["usercmds"][0]["arg"]
            for t in p["ticks"]
            if t["source"] == "alpha/late.dem" and t["global_tick"] == 100
        )
        arow = next(
            t["usercmds"][0]["arg"]
            for t in a["ticks"]
            if t["source"] == "alpha/late.dem" and t["global_tick"] == 100
        )
        assert prow != arow

    def test_nested_tree_includes_all_catalog_demos(self) -> None:
        """Build covers every catalog demo except broken/trunc.dem."""
        reset()
        run_build(SEED_PRIMARY)
        files = load_export(OUT)["files"]
        assert set(files) == set(BUILD_FILES)

    def test_stats_usercmd_count_matches_ticks(self) -> None:
        """stats.usercmd_count equals flattened usercmd rows."""
        reset()
        run_build(SEED_PRIMARY)
        doc = load_export(OUT)
        flat = sum(len(t["usercmds"]) for t in doc["ticks"])
        assert doc["stats"]["usercmd_count"] == flat

    def test_second_alt_seed_differs_from_primary(self) -> None:
        """Second alternate seed matches reference and differs from primary on salted args."""
        reset()
        run_build(SEED_PRIMARY, APP / "output/s0.json")
        proc = run_build(ALT_SEEDS[1], APP / "output/s1.json")
        assert proc.returncode == 0, proc.stderr
        d0 = load_export(APP / "output/s0.json")
        d1 = load_export(APP / "output/s1.json")
        assert d1 == reference_build(DEMOS, ALT_SEEDS[1])
        args0 = [c["arg"] for t in d0["ticks"] for c in t["usercmds"]]
        args1 = [c["arg"] for t in d1["ticks"] for c in t["usercmds"]]
        assert args0 != args1

    def test_staging_build_snapshot_primary_ingest_export(self) -> None:
        """Ingest fixtures then export staging snapshot JSON for primary seed."""
        reset()
        proc = run_build(SEED_PRIMARY, APP / "output/staging-primary.json")
        assert proc.returncode == 0, proc.stderr
        doc = load_export(APP / "output/staging-primary.json")
        assert doc["seed"] == SEED_PRIMARY
        assert doc["index_version"] == 1
        assert doc == reference_build(DEMOS, SEED_PRIMARY)

    def test_export_json_lists_seed_and_files(self) -> None:
        """Export JSON records seed and merged file list."""
        reset()
        run_build(SEED_PRIMARY)
        doc = load_export(OUT)
        assert doc["seed"] == SEED_PRIMARY
        assert len(doc["files"]) == len(BUILD_FILES)

    def test_build_stats_tick_count_positive(self) -> None:
        """stats.tick_count is positive after full ingest export build."""
        reset()
        run_build(SEED_PRIMARY)
        stats = load_export(OUT)["stats"]
        assert stats["tick_count"] > 0
        assert stats["file_count"] == len(BUILD_FILES)

    def test_probe_strings_highidx_exits_zero(self) -> None:
        """Probe on strings/highidx.dem succeeds."""
        reset()
        proc = run_probe(DEMOS / "strings/highidx.dem")
        assert proc.returncode == 0, proc.stderr

    def test_hidden_verifier_fixture_twist_demo(self) -> None:
        """Hidden demo under /opt/verifier-fixtures/demos probes successfully."""
        assert HIDDEN_FIXTURE_ROOT.is_dir(), "missing /opt/verifier-fixtures/demos"
        hidden = HIDDEN_FIXTURE_ROOT / "hidden-twist.dem"
        assert hidden.is_file()
        reset()
        proc = run_probe(hidden)
        assert proc.returncode == 0, proc.stderr

    def test_hidden_verifier_fixture_merge_order(self) -> None:
        """Hidden /opt/verifier-fixtures tree build sorts flat demo paths."""
        assert HIDDEN_FIXTURE_ROOT.is_dir(), "missing /opt/verifier-fixtures/demos"
        reset()
        proc = run_build(SEED_PRIMARY, APP / "output/hidden-tree.json", root=HIDDEN_FIXTURE_ROOT)
        assert proc.returncode == 0, proc.stderr
        files = load_export(APP / "output/hidden-tree.json")["files"]
        assert files == ["hidden-merge.dem", "hidden-twist.dem"]
