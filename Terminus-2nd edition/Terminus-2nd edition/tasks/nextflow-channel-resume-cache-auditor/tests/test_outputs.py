"""Behavioral verifier for Nextflow resume-cache auditor."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest
from reference_audit import (
    expansion_hash,
    lineage_digest,
    norm_digest,
    reference_report,
    stage_tasks,
)

APP = Path("/app")
CLI = "/app/bin/nfresume-audit"
RESET = APP / "scripts" / "reset-state.sh"
STAGE = APP / "state/resume-stage.json"
GENERATION = APP / "state/audit-generation.json"
FINDINGS = APP / "work/audit-findings.json"
FIXTURES = APP / "fixtures"
HIDDEN = Path("/opt/verifier-fixtures/nfresume")
STAGE_PATH = "/app/state/resume-stage.json"
GENERATION_PATH = "/app/state/audit-generation.json"
FINDINGS_PATH = "/app/work/audit-findings.json"
SEEDS = json.loads((FIXTURES / "seeds.json").read_text(encoding="utf-8"))["seeds"]

SCENARIOS = [
    "clean-pipeline",
    "digest-drift",
    "glob-mismatch",
    "retry-stale",
    "provenance-crossrun",
    "lineage-break",
]


def run(cmd: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False, env=merged)


def reset() -> None:
    proc = run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def pipeline(seed: str, scenario: str, fixture_dir: Path | None = None, out_name: str | None = None) -> Path:
    root = fixture_dir or FIXTURES
    env = {}
    if fixture_dir is not None:
        env["TB3_FIXTURE_DIR"] = str(fixture_dir)
    for step in (
        [CLI, "ingest", "--seed", seed, "--scenario", scenario, "--fixture-dir", str(root)],
        [CLI, "audit", "--scenario", scenario],
    ):
        proc = run(step, env=env)
        assert proc.returncode == 0, proc.stderr + proc.stdout
    out = APP / "output" / (out_name or f"{seed}-{scenario}-report.json")
    proc = run([CLI, "export", "--scenario", scenario, "--output", str(out)], env=env)
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return out


class TestOutputPaths:
    def test_ingest_writes_resume_stage_json(self) -> None:
        """Instruction requires ingest to write /app/state/resume-stage.json."""
        reset()
        assert str(STAGE) == STAGE_PATH
        proc = run([CLI, "ingest", "--seed", SEEDS[0], "--scenario", "clean-pipeline", "--fixture-dir", str(FIXTURES)])
        assert proc.returncode == 0
        assert Path(STAGE_PATH).is_file()

    def test_audit_writes_audit_generation_json(self) -> None:
        """Audit must bump /app/state/audit-generation.json after findings persist."""
        reset()
        assert str(GENERATION) == GENERATION_PATH
        run([CLI, "ingest", "--seed", SEEDS[0], "--scenario", "clean-pipeline", "--fixture-dir", str(FIXTURES)])
        proc = run([CLI, "audit", "--scenario", "clean-pipeline"])
        assert proc.returncode == 0
        assert Path(GENERATION_PATH).is_file()
        assert json.loads(Path(GENERATION_PATH).read_text(encoding="utf-8"))["audit_generation"] >= 1

    def test_audit_writes_findings_json(self) -> None:
        """Audit must persist findings to /app/work/audit-findings.json."""
        reset()
        pipeline(SEEDS[0], "digest-drift")
        assert Path(FINDINGS_PATH).is_file()


class TestIngestStaging:
    def test_staging_container_digest_normalized(self) -> None:
        """Container digests must be normalized without sha256 prefix."""
        reset()
        run([CLI, "ingest", "--seed", SEEDS[1], "--scenario", "glob-mismatch", "--fixture-dir", str(FIXTURES)])
        snap = json.loads(STAGE.read_text(encoding="utf-8"))
        digest_val = snap["tasks"][0]["container_digest"]
        assert digest_val == norm_digest("SHA256:" + ("0" * 64).upper())
        assert not digest_val.startswith("sha256:")

    def test_staging_glob_expansion_sorted(self) -> None:
        """Computed expansion hash must use lexicographically sorted paths."""
        reset()
        run([CLI, "ingest", "--seed", SEEDS[0], "--scenario", "clean-pipeline", "--fixture-dir", str(FIXTURES)])
        snap = json.loads(STAGE.read_text(encoding="utf-8"))
        run_dir = FIXTURES / "runs" / "clean-pipeline"
        fetch = next(t for t in snap["tasks"] if t["task_id"] == "fetch:raw")
        expected = expansion_hash(run_dir, ["inputs/samples/*.fastq"])
        assert fetch["computed_expansion_hash"] == expected

    def test_staging_lineage_hash_root_first(self) -> None:
        """Lineage digest must chain parent_hashes root-first then task hash."""
        reset()
        run([CLI, "ingest", "--seed", SEEDS[0], "--scenario", "clean-pipeline", "--fixture-dir", str(FIXTURES)])
        snap = json.loads(STAGE.read_text(encoding="utf-8"))
        align = next(t for t in snap["tasks"] if t["task_id"] == "align:sample")
        expected = lineage_digest(["aa11"], "bb22")
        assert align["lineage_digest"] == expected

    def test_staging_task_count_matches_trace(self) -> None:
        """Staging task_count must equal trace file count."""
        reset()
        run([CLI, "ingest", "--seed", SEEDS[2], "--scenario", "clean-pipeline", "--fixture-dir", str(FIXTURES)])
        snap = json.loads(STAGE.read_text(encoding="utf-8"))
        assert snap["task_count"] == len(snap["tasks"])
        assert snap["task_count"] == 2


class TestAuditRules:
    def test_digest_drift_flagged(self) -> None:
        """Cached task with changed container digest must emit digest_drift."""
        reset()
        pipeline(SEEDS[0], "digest-drift")
        body = json.loads(FINDINGS.read_text(encoding="utf-8"))
        rules = {f["rule"] for f in body["findings"]}
        assert "digest_drift" in rules

    def test_glob_mismatch_flagged(self) -> None:
        """Wrong expansion_hash must emit glob_expansion_mismatch."""
        reset()
        pipeline(SEEDS[1], "glob-mismatch")
        body = json.loads(FINDINGS.read_text(encoding="utf-8"))
        rules = {f["rule"] for f in body["findings"]}
        assert "glob_expansion_mismatch" in rules

    def test_lineage_break_flagged(self) -> None:
        """Poisoned recorded lineage_digest must emit lineage_break."""
        reset()
        pipeline(SEEDS[0], "lineage-break")
        body = json.loads(FINDINGS.read_text(encoding="utf-8"))
        rules = {f["rule"] for f in body["findings"]}
        assert "lineage_break" in rules
        finding = next(f for f in body["findings"] if f["rule"] == "lineage_break")
        expected = lineage_digest(["aa11"], "ii99")
        assert finding["detail"] == f"staged {'0' * 64} expected {expected}"

    def test_retry_stale_cache_flagged(self) -> None:
        """Cached retry after failed prior attempt must emit retry_stale_cache."""
        reset()
        pipeline(SEEDS[2], "retry-stale")
        body = json.loads(FINDINGS.read_text(encoding="utf-8"))
        rules = {f["rule"] for f in body["findings"]}
        assert "retry_stale_cache" in rules

    def test_provenance_crossrun_flagged(self) -> None:
        """Resumed run with foreign cache session must emit provenance_crossrun."""
        reset()
        pipeline(SEEDS[3], "provenance-crossrun")
        body = json.loads(FINDINGS.read_text(encoding="utf-8"))
        rules = {f["rule"] for f in body["findings"]}
        assert "provenance_crossrun" in rules


class TestExportReference:
    @pytest.mark.parametrize("scenario", SCENARIOS)
    def test_export_matches_reference(self, scenario: str) -> None:
        """Export unsafe-cache report must match independent reference audit."""
        reset()
        seed = SEEDS[0]
        out = pipeline(seed, scenario)
        body = json.loads(out.read_text(encoding="utf-8"))
        ref = reference_report(FIXTURES, scenario)
        assert body["unsafe_count"] == ref["unsafe_count"]
        assert body["findings"] == ref["findings"]
        assert body["audit_digest"] == ref["audit_digest"]
        assert body["safe_for_resume"] == ref["safe_for_resume"]

    def test_clean_pipeline_safe_for_resume(self) -> None:
        """Clean pipeline must report safe_for_resume true."""
        reset()
        out = pipeline(SEEDS[0], "clean-pipeline")
        body = json.loads(out.read_text(encoding="utf-8"))
        assert body["safe_for_resume"] is True
        assert body["unsafe_count"] == 0

    def test_export_refuses_before_audit(self) -> None:
        """Export must fail when audit_generation gate is unset."""
        reset()
        run([CLI, "ingest", "--seed", SEEDS[0], "--scenario", "clean-pipeline", "--fixture-dir", str(FIXTURES)])
        out = APP / "output" / "early.json"
        proc = run([CLI, "export", "--scenario", "clean-pipeline", "--output", str(out)])
        assert proc.returncode != 0


class TestHiddenTraps:
    def test_tb3_glob_poison_hidden_trap(self) -> None:
        """Hidden glob poison fixture must flag glob_expansion_mismatch via reference."""
        reset()
        hidden_root = "/opt/verifier-fixtures/nfresume"
        env = {"TB3_FIXTURE_DIR": hidden_root}
        proc = run(
            [CLI, "ingest", "--seed", SEEDS[3], "--scenario", "glob-poison-trap", "--fixture-dir", hidden_root],
            env=env,
        )
        assert proc.returncode == 0
        proc = run([CLI, "audit", "--scenario", "glob-poison-trap"], env=env)
        assert proc.returncode == 0
        out = APP / "output" / "tb3-glob.json"
        proc = run([CLI, "export", "--scenario", "glob-poison-trap", "--output", str(out)], env=env)
        assert proc.returncode == 0
        body = json.loads(out.read_text(encoding="utf-8"))
        ref = reference_report(HIDDEN, "glob-poison-trap")
        assert body["findings"] == ref["findings"]

    def test_tb3_digest_drift_hidden_trap(self) -> None:
        """Hidden digest drift trap must match reference unsafe findings."""
        reset()
        hidden_root = "/opt/verifier-fixtures/nfresume"
        env = {"TB3_FIXTURE_DIR": hidden_root}
        proc = run(
            [CLI, "ingest", "--seed", SEEDS[2], "--scenario", "digest-drift-trap", "--fixture-dir", hidden_root],
            env=env,
        )
        assert proc.returncode == 0
        proc = run([CLI, "audit", "--scenario", "digest-drift-trap"], env=env)
        assert proc.returncode == 0
        out = APP / "output" / "tb3-digest.json"
        proc = run([CLI, "export", "--scenario", "digest-drift-trap", "--output", str(out)], env=env)
        assert proc.returncode == 0
        body = json.loads(out.read_text(encoding="utf-8"))
        ref = reference_report(HIDDEN, "digest-drift-trap")
        assert body["unsafe_count"] == ref["unsafe_count"]
        assert "digest_drift" in {f["rule"] for f in body["findings"]}


class TestPersistence:
    def test_second_audit_increments_generation(self) -> None:
        """Second audit command must increment persisted audit_generation counter."""
        reset()
        pipeline(SEEDS[0], "clean-pipeline")
        gen1 = json.loads(GENERATION.read_text(encoding="utf-8"))["audit_generation"]
        proc = run([CLI, "audit", "--scenario", "clean-pipeline"])
        assert proc.returncode == 0
        gen2 = json.loads(GENERATION.read_text(encoding="utf-8"))["audit_generation"]
        assert gen2 == gen1 + 1

    def test_stale_generation_blocks_export(self) -> None:
        """Export must fail when staging audit_generation drifts from generation file."""
        reset()
        pipeline(SEEDS[1], "digest-drift")
        gen = json.loads(GENERATION.read_text(encoding="utf-8"))["audit_generation"]
        STAGE.write_text(
            STAGE.read_text(encoding="utf-8").replace(
                f'"audit_generation": {gen}',
                f'"audit_generation": {gen - 1}',
            ),
            encoding="utf-8",
        )
        proc = run([CLI, "export", "--scenario", "digest-drift", "--output", str(APP / "output/stale.json")])
        assert proc.returncode != 0

    def test_reference_staging_independent(self) -> None:
        """Reference staging must differ from bundled when lineage ordering wrong."""
        reset()
        run([CLI, "ingest", "--seed", SEEDS[0], "--scenario", "clean-pipeline", "--fixture-dir", str(FIXTURES)])
        snap = json.loads(STAGE.read_text(encoding="utf-8"))
        ref_staged = stage_tasks(FIXTURES, "clean-pipeline")
        for got, want in zip(snap["tasks"], ref_staged, strict=True):
            assert got["lineage_digest"] == want["lineage_digest"]

    def test_findings_sorted_by_task_and_rule(self) -> None:
        """Audit findings must be sorted by task_id then rule name."""
        reset()
        pipeline(SEEDS[0], "digest-drift")
        findings = json.loads(FINDINGS.read_text(encoding="utf-8"))["findings"]
        keys = [(f["task_id"], f["rule"]) for f in findings]
        assert keys == sorted(keys)
