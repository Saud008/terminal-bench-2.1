"""Behavioral verifier for Count-Min Sketch epsilon budget merger."""

from __future__ import annotations

import json
import math
import os
import subprocess
from pathlib import Path

import pytest
from reference_sketch import (
    compose_epsilons,
    load_bundle,
    reference_pipeline,
    seed_offset,
)

APP = Path("/app")
CMSCTL = Path("/app/bin/cmsctl")
RESET = APP / "scripts" / "reset-state.sh"
STAGE = APP / "state" / "cms-merge-stage.json"
GENERATION = APP / "state" / "merge-generation.json"
STAGE_PATH = "/app/state/cms-merge-stage.json"
GENERATION_PATH = "/app/state/merge-generation.json"
FIXTURES = APP / "fixtures"
HIDDEN = Path("/opt/verifier-fixtures/cms-sketch")
SEEDS = json.loads((FIXTURES / "seeds.json").read_text(encoding="utf-8"))["seeds"]

BUNDLES = ["overlap-merge", "triple-weight", "narrow-window"]


def run(cmd: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        cmd,
        cwd=str(APP),
        capture_output=True,
        text=True,
        check=False,
        env=merged,
    )


def reset() -> None:
    proc = run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def pipeline(seed: str, bundle: str, fixture_dir: Path | None = None) -> Path:
    env = {}
    if fixture_dir is not None:
        env["TB3_FIXTURE_DIR"] = str(fixture_dir)
    root = fixture_dir or FIXTURES
    for step in (
        [str(CMSCTL), "ingest", "--seed", seed, "--bundle", bundle, "--fixture-dir", str(root)],
        [str(CMSCTL), "merge", "--seed", seed, "--bundle", bundle, "--fixture-dir", str(root)],
    ):
        proc = run(step, env=env)
        assert proc.returncode == 0, proc.stderr + proc.stdout
    out = APP / "output" / f"{seed}-{bundle}-rollup.json"
    proc = run(
        [
            str(CMSCTL),
            "export",
            "--seed",
            seed,
            "--bundle",
            bundle,
            "--fixture-dir",
            str(root),
            "--output",
            str(out),
        ],
        env=env,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return out


class TestOutputPaths:
    def test_ingest_writes_cms_merge_stage_json(self) -> None:
        """Instruction requires ingest to materialize /app/state/cms-merge-stage.json."""
        reset()
        assert str(STAGE) == STAGE_PATH
        proc = run(
            [
                str(CMSCTL),
                "ingest",
                "--seed",
                SEEDS[0],
                "--bundle",
                "overlap-merge",
                "--fixture-dir",
                str(FIXTURES),
            ]
        )
        assert proc.returncode == 0
        assert Path(STAGE_PATH).is_file()

    def test_merge_writes_merge_generation_json(self) -> None:
        """Instruction requires merge to bump /app/state/merge-generation.json."""
        reset()
        assert str(GENERATION) == GENERATION_PATH
        pipeline(SEEDS[0], "overlap-merge")
        assert Path(GENERATION_PATH).is_file()
        assert json.loads(Path(GENERATION_PATH).read_text(encoding="utf-8"))["merge_generation"] >= 1


class TestIngestStaging:
    def test_ingest_writes_overlap_ms_for_overlap_merge(self) -> None:
        """Verify window overlap weighting contract via overlap_ms in cms-merge-stage.json."""
        reset()
        seed = SEEDS[0]
        proc = run(
            [
                str(CMSCTL),
                "ingest",
                "--seed",
                seed,
                "--bundle",
                "overlap-merge",
                "--fixture-dir",
                str(FIXTURES),
            ]
        )
        assert proc.returncode == 0
        snap = json.loads(STAGE.read_text(encoding="utf-8"))
        ref = reference_pipeline(FIXTURES, seed, "overlap-merge")
        assert snap["overlap_ms"] == ref["overlap_ms"] == 1000

    def test_staging_window_weights_match_reference(self) -> None:
        """Window overlap weights in staging must match independent reference weighting."""
        reset()
        seed = SEEDS[1]
        pipeline(seed, "overlap-merge")
        snap = json.loads(STAGE.read_text(encoding="utf-8"))
        ref = reference_pipeline(FIXTURES, seed, "overlap-merge")
        assert snap["window_weights"] == ref["window_weights"]

    def test_staging_epsilon_lineage_l2_composition(self) -> None:
        """Epsilon lineage in staging must use L2 composition from epsilon-composition.md."""
        reset()
        seed = SEEDS[0]
        run(
            [
                str(CMSCTL),
                "ingest",
                "--seed",
                seed,
                "--bundle",
                "overlap-merge",
                "--fixture-dir",
                str(FIXTURES),
            ]
        )
        snap = json.loads(STAGE.read_text(encoding="utf-8"))
        raw = snap["epsilon_lineage"]["raw_epsilons"]
        assert raw == [0.3, 0.4]
        assert math.isclose(snap["epsilon_lineage"]["composed_epsilon"], 0.5, rel_tol=1e-9)

    def test_ingest_applies_seed_offset_to_hash_seed(self) -> None:
        """Seed fixtures must shift hash_seed per seeds.json offset rules."""
        reset()
        seed = SEEDS[2]
        run(
            [
                str(CMSCTL),
                "ingest",
                "--seed",
                seed,
                "--bundle",
                "narrow-window",
                "--fixture-dir",
                str(FIXTURES),
            ]
        )
        snap = json.loads(STAGE.read_text(encoding="utf-8"))
        assert snap["hash_seed"] == (7777 + seed_offset(seed)) & 0xFFFFFFFFFFFFFFFF

    def test_staging_engine_and_fingerprints(self) -> None:
        """Staging snapshot must record engine id and per-shard fingerprints."""
        reset()
        seed = SEEDS[0]
        run(
            [
                str(CMSCTL),
                "ingest",
                "--seed",
                seed,
                "--bundle",
                "triple-weight",
                "--fixture-dir",
                str(FIXTURES),
            ]
        )
        snap = json.loads(STAGE.read_text(encoding="utf-8"))
        assert snap["engine"] == "cms-hash-v2"
        assert len(snap["shard_fingerprints"]) == 3


class TestCompatibilityGate:
    def test_seed_mismatch_rejects_atomically(self) -> None:
        """Shard compatibility gate must reject mismatched hash seeds without staging."""
        reset()
        assert not STAGE.exists()
        hidden_root = "/opt/verifier-fixtures/cms-sketch"
        proc = run(
            [
                str(CMSCTL),
                "ingest",
                "--seed",
                "alpha",
                "--bundle",
                "seed-mismatch",
                "--fixture-dir",
                hidden_root,
            ]
        )
        assert proc.returncode != 0
        assert not STAGE.exists()

    def test_zero_overlap_rejects_without_staging(self) -> None:
        """Zero overlap windows must fail ingest atomically per window-overlap-weighting.md."""
        reset()
        hidden_root = "/opt/verifier-fixtures/cms-sketch"
        proc = run(
            [
                str(CMSCTL),
                "ingest",
                "--seed",
                "beta",
                "--bundle",
                "zero-overlap",
                "--fixture-dir",
                hidden_root,
            ]
        )
        assert proc.returncode != 0
        assert not STAGE.exists()

    def test_namespace_split_rejects_incompatible_shards(self) -> None:
        """Namespace salt mismatches must fail shard-compatibility-gate.md validation."""
        reset()
        hidden_root = "/opt/verifier-fixtures/cms-sketch"
        proc = run(
            [
                str(CMSCTL),
                "ingest",
                "--seed",
                "gamma",
                "--bundle",
                "namespace-split",
                "--fixture-dir",
                hidden_root,
            ]
        )
        assert proc.returncode != 0


class TestMergeExport:
    @pytest.mark.parametrize("bundle", BUNDLES)
    @pytest.mark.parametrize("seed", SEEDS[:3])
    def test_export_estimates_match_reference(self, seed: str, bundle: str) -> None:
        """Export estimates must match independent Count-Min reference for each bundle."""
        reset()
        out = pipeline(seed, bundle)
        body = json.loads(out.read_text(encoding="utf-8"))
        ref = reference_pipeline(FIXTURES, seed, bundle)
        for key, expected in ref["estimates"].items():
            assert body["estimates"][key] == expected

    def test_merge_bumps_generation_file(self) -> None:
        """Merge must synchronize merge_generation between staging and generation file."""
        reset()
        seed = SEEDS[0]
        pipeline(seed, "overlap-merge")
        gen = json.loads(GENERATION.read_text(encoding="utf-8"))
        snap = json.loads(STAGE.read_text(encoding="utf-8"))
        assert gen["merge_generation"] == snap["merge_generation"] == 1

    def test_export_includes_stage_digest_hex(self) -> None:
        """Export rollup must include lowercase sha256 stage_digest per lineage-export-schema.md."""
        reset()
        seed = SEEDS[1]
        out = pipeline(seed, "narrow-window")
        body = json.loads(out.read_text(encoding="utf-8"))
        assert len(body["stage_digest"]) == 64
        int(body["stage_digest"], 16)

    def test_export_refuses_before_merge(self) -> None:
        """Export must refuse when merge_generation gate has not been satisfied."""
        reset()
        seed = SEEDS[0]
        run(
            [
                str(CMSCTL),
                "ingest",
                "--seed",
                seed,
                "--bundle",
                "overlap-merge",
                "--fixture-dir",
                str(FIXTURES),
            ]
        )
        out = APP / "output" / "premature.json"
        proc = run(
            [
                str(CMSCTL),
                "export",
                "--seed",
                seed,
                "--bundle",
                "overlap-merge",
                "--fixture-dir",
                str(FIXTURES),
                "--output",
                str(out),
            ]
        )
        assert proc.returncode != 0

    def test_triple_weight_overlap_ms(self) -> None:
        """Triple-shard bundle overlap_ms and epsilon lineage must match reference math."""
        reset()
        seed = SEEDS[0]
        out = pipeline(seed, "triple-weight")
        body = json.loads(out.read_text(encoding="utf-8"))
        assert body["overlap_ms"] == 2000
        eps = body["epsilon_lineage"]["composed_epsilon"]
        assert math.isclose(eps, compose_epsilons([0.2, 0.15, 0.25]), rel_tol=1e-9)


class TestHiddenTraps:
    def test_tb3_width_bias_hidden_bundle(self) -> None:
        """TB3_WIDTH_BIAS hidden trap must shift width and preserve reference estimates."""
        reset()
        seed = SEEDS[3]
        hidden_root = "/opt/verifier-fixtures/cms-sketch"
        env = {"TB3_WIDTH_BIAS": "16", "TB3_FIXTURE_DIR": hidden_root}
        proc = run(
            [
                str(CMSCTL),
                "ingest",
                "--seed",
                seed,
                "--bundle",
                "tb3-width-trap",
                "--fixture-dir",
                hidden_root,
            ],
            env=env,
        )
        assert proc.returncode == 0
        snap = json.loads(STAGE.read_text(encoding="utf-8"))
        ref = reference_pipeline(HIDDEN, seed, "tb3-width-trap", width_bias=16)
        assert snap["width"] == ref["width"]
        proc = run(
            [
                str(CMSCTL),
                "merge",
                "--seed",
                seed,
                "--bundle",
                "tb3-width-trap",
                "--fixture-dir",
                hidden_root,
            ],
            env=env,
        )
        assert proc.returncode == 0
        out = APP / "output" / "tb3-trap.json"
        proc = run(
            [
                str(CMSCTL),
                "export",
                "--seed",
                seed,
                "--bundle",
                "tb3-width-trap",
                "--fixture-dir",
                hidden_root,
                "--output",
                str(out),
            ],
            env=env,
        )
        assert proc.returncode == 0
        body = json.loads(out.read_text(encoding="utf-8"))
        assert body["estimates"]["trap:flow"] == ref["estimates"]["trap:flow"]

    def test_namespace_salt_affects_estimates(self) -> None:
        """Salted-key namespace rules must change estimates when namespace salt differs."""
        reset()
        seed = SEEDS[0]
        out = pipeline(seed, "overlap-merge")
        body = json.loads(out.read_text(encoding="utf-8"))
        _, shards = load_bundle(FIXTURES, seed, "overlap-merge")
        wrong = body["estimates"]["event:login"]
        alt_table = __import__("reference_sketch").build_table(
            shards[0]["width"],
            shards[0]["depth"],
            shards[0]["hash_seed"],
            "wrong-salt",
            [("event:login", 9999)],
        )
        assert wrong != __import__("reference_sketch").estimate(
            alt_table, "event:login", shards[0]["hash_seed"], "wrong-salt"
        )

    def test_conservative_max_not_sum_on_overlap_merge(self) -> None:
        """Conservative merge must use cell-wise max rather than summing shard counters."""
        reset()
        seed = SEEDS[2]
        out = pipeline(seed, "overlap-merge")
        body = json.loads(out.read_text(encoding="utf-8"))
        ref = reference_pipeline(FIXTURES, seed, "overlap-merge")
        naive_sum_login = 50 + 80
        assert body["estimates"]["event:login"] <= naive_sum_login
        assert body["estimates"]["event:login"] == ref["estimates"]["event:login"]


class TestPersistenceGeneration:
    def test_merge_generation_persist_gate_blocks_stale_export(self) -> None:
        """Persisted merge_generation must match staging before export is allowed."""
        reset()
        seed = SEEDS[0]
        pipeline(seed, "narrow-window")
        gen_before = json.loads(GENERATION.read_text(encoding="utf-8"))["merge_generation"]
        STAGE.write_text(
            STAGE.read_text(encoding="utf-8").replace(
                f'"merge_generation": {gen_before}',
                f'"merge_generation": {gen_before - 1}',
            ),
            encoding="utf-8",
        )
        out = APP / "output" / "stale.json"
        proc = run(
            [
                str(CMSCTL),
                "export",
                "--seed",
                seed,
                "--bundle",
                "narrow-window",
                "--fixture-dir",
                str(FIXTURES),
                "--output",
                str(out),
            ]
        )
        assert proc.returncode != 0

    def test_second_merge_increments_persisted_generation(self) -> None:
        """Repeated merge commands must increment /app/state/merge-generation.json."""
        reset()
        seed = SEEDS[1]
        pipeline(seed, "triple-weight")
        gen1 = json.loads(GENERATION.read_text(encoding="utf-8"))["merge_generation"]
        proc = run(
            [
                str(CMSCTL),
                "merge",
                "--seed",
                seed,
                "--bundle",
                "triple-weight",
                "--fixture-dir",
                str(FIXTURES),
            ]
        )
        assert proc.returncode == 0
        gen2 = json.loads(GENERATION.read_text(encoding="utf-8"))["merge_generation"]
        assert gen2 == gen1 + 1

    def test_overlap_merge_delta_seed_reference(self) -> None:
        """Delta seed bundle must still match reference estimates after offset."""
        reset()
        seed = SEEDS[3]
        out = pipeline(seed, "overlap-merge")
        body = json.loads(out.read_text(encoding="utf-8"))
        ref = reference_pipeline(FIXTURES, seed, "overlap-merge")
        assert body["estimates"] == ref["estimates"]

    def test_narrow_window_epsilon_lineage_export(self) -> None:
        """Export epsilon_lineage must reflect L2 composition for narrow-window bundle."""
        reset()
        seed = SEEDS[2]
        out = pipeline(seed, "narrow-window")
        body = json.loads(out.read_text(encoding="utf-8"))
        assert math.isclose(body["epsilon_lineage"]["composed_epsilon"], compose_epsilons([0.1, 0.12]), rel_tol=1e-9)
