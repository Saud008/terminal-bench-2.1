#!/usr/bin/env python3
"""Behavioral verifier for borg-prune-retention-policy-simulator."""

from __future__ import annotations

import json
import shutil
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path

from reference_retention import (
    compact_export,
    evaluate_retention,
    load_json,
    make_random_list,
    parse_list_file,
    stage_path_for,
)

BIN = Path("/app/bin/borg-prune-sim")
SEED_LIST = Path("/app/fixtures/seed/repo.list")
POLICY = Path("/app/policy/default.json")
HOLDS_EMPTY = Path("/app/holds/empty.json")
OUTPUT = Path("/app/output")
TB3_SKEW = Path("/opt/verifier-fixtures/borg/hidden-skew")
TB3_HOLDS = Path("/opt/verifier-fixtures/borg/hidden-holds")
REF_NOW = datetime(2024, 7, 1, 0, 0, 0, tzinfo=timezone.utc)


def _run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=check, capture_output=True, text=True)


def _oracle_report(list_file: Path, policy: Path, holds: Path, ref_now: datetime) -> dict:
    archives = parse_list_file(list_file)
    policy_doc = load_json(policy)
    holds_doc = load_json(holds)
    return evaluate_retention(archives, policy_doc, holds_doc, ref_now)


def _pipeline(list_file: Path, policy: Path, holds: Path, ref_now: datetime, out: Path) -> dict:
    ref_s = ref_now.strftime("%Y-%m-%dT%H:%M:%SZ")
    _run([str(BIN), "ingest", "--list", str(list_file), "--repo-id", "main"])
    _run(
        [
            str(BIN),
            "evaluate",
            "--list",
            str(list_file),
            "--policy",
            str(policy),
            "--holds",
            str(holds),
            "--now",
            ref_s,
        ]
    )
    _run([str(BIN), "export", "--list", str(list_file), "--out", str(out)])
    return json.loads(out.read_text(encoding="utf-8"))


def _assert_export_matches(report: dict, expected: dict) -> None:
    assert report["kept_archives"] == expected["kept_archives"]
    assert report["pruned_archives"] == expected["pruned_archives"]
    assert report["legal_hold_count"] == expected["legal_hold_count"]
    assert report["clock_skew_adjustment_count"] == expected["clock_skew_adjustment_count"]
    assert report["compaction_bytes_reclaimable"] == expected["compaction_bytes_reclaimable"]
    assert report["compaction_segments_reclaimable"] == expected["compaction_segments_reclaimable"]


class TestBorgPruneRetentionSimulator:
    """Borg list ingest / evaluate / export with independent retention oracle."""

    def test_binary_exists(self):
        """borg-prune-sim CLI is installed at /app/bin/borg-prune-sim."""
        assert BIN.is_file(), "missing /app/bin/borg-prune-sim"

    def test_example_workflow_paths(self):
        """Instruction example writes borg.stage.json beside list and /app/output/prune-report.json."""
        list_file = SEED_LIST
        stage = Path("/app/fixtures/seed/borg.stage.json")
        export = Path("/app/output/prune-report.json")
        if stage.exists():
            stage.unlink()
        if export.exists():
            export.unlink()
        ref_s = REF_NOW.strftime("%Y-%m-%dT%H:%M:%SZ")
        _run([str(BIN), "ingest", "--list", str(list_file), "--repo-id", "main"])
        _run(
            [
                str(BIN),
                "evaluate",
                "--list",
                str(list_file),
                "--policy",
                str(POLICY),
                "--holds",
                str(HOLDS_EMPTY),
                "--now",
                ref_s,
            ]
        )
        _run([str(BIN), "export", "--list", str(list_file), "--out", str(export)])
        expected = _oracle_report(list_file, POLICY, HOLDS_EMPTY, REF_NOW)
        report = json.loads(export.read_text(encoding="utf-8"))
        assert stage.is_file(), "stage must be /app/fixtures/seed/borg.stage.json"
        assert export.is_file(), "export must be /app/output/prune-report.json"
        _assert_export_matches(report, expected)

    def test_staging_beside_list_not_global_state(self, tmp_path: Path):
        """Staging snapshot path is dirname(list)/borg.stage.json beside the list file."""
        suffix = uuid.uuid4().hex[:8]
        work = tmp_path / f"custom_{suffix}"
        work.mkdir()
        list_file = work / "repo.list"
        shutil.copy2(SEED_LIST, list_file)
        stage = stage_path_for(list_file)
        _run([str(BIN), "ingest", "--list", str(list_file), "--repo-id", "tb"])
        assert stage.is_file()
        assert stage.parent == list_file.parent

    def test_bundled_seed_retention_decisions(self):
        """Bundled seed fixture matches independent retention oracle at 2024-07-01."""
        out = OUTPUT / f"seed-{uuid.uuid4().hex[:8]}.json"
        expected = _oracle_report(SEED_LIST, POLICY, HOLDS_EMPTY, REF_NOW)
        report = _pipeline(SEED_LIST, POLICY, HOLDS_EMPTY, REF_NOW, out)
        _assert_export_matches(report, expected)

    def test_duplicate_name_last_line_wins(self, tmp_path: Path):
        """Duplicate archive_name lines keep the last occurrence in file order."""
        suffix = uuid.uuid4().hex[:10]
        list_file = tmp_path / f"dup_{suffix}.list"
        list_file.write_text(
            f"dup-{suffix}\t2024-01-01T00:00:00Z\t1000\t1\n"
            f"dup-{suffix}\t2024-06-15T12:00:00Z\t9000\t9\n",
            encoding="utf-8",
        )
        out = tmp_path / "report.json"
        expected = _oracle_report(list_file, POLICY, HOLDS_EMPTY, REF_NOW)
        report = _pipeline(list_file, POLICY, HOLDS_EMPTY, REF_NOW, out)
        _assert_export_matches(report, expected)
        assert f"dup-{suffix}" in report["kept_archives"] or f"dup-{suffix}" in report["pruned_archives"]

    def test_legal_hold_exact_name(self, tmp_path: Path):
        """Exact legal hold names are never pruned."""
        suffix = uuid.uuid4().hex[:8]
        list_file = tmp_path / f"hold_{suffix}.list"
        list_file.write_text(
            f"hold-{suffix}\t2020-01-01T00:00:00Z\t500000\t2\n"
            f"other-{suffix}\t2024-06-01T00:00:00Z\t1000000\t3\n",
            encoding="utf-8",
        )
        holds = tmp_path / "holds.json"
        holds.write_text(json.dumps({"exact": [f"hold-{suffix}"], "prefix": []}) + "\n", encoding="utf-8")
        out = tmp_path / "report.json"
        expected = _oracle_report(list_file, POLICY, holds, REF_NOW)
        report = _pipeline(list_file, POLICY, holds, REF_NOW, out)
        _assert_export_matches(report, expected)
        assert f"hold-{suffix}" in report["kept_archives"]

    def test_legal_hold_prefix_start_only(self, tmp_path: Path):
        """Prefix holds match only when archive name starts with prefix."""
        suffix = uuid.uuid4().hex[:8]
        list_file = tmp_path / f"prefix_{suffix}.list"
        list_file.write_text(
            f"legal-{suffix}\t2024-06-01T00:00:00Z\t1000\t1\n"
            f"xlegal-{suffix}\t2024-06-02T00:00:00Z\t2000\t2\n",
            encoding="utf-8",
        )
        holds = tmp_path / "holds.json"
        holds.write_text(json.dumps({"exact": [], "prefix": ["legal-"]}) + "\n", encoding="utf-8")
        out = tmp_path / "report.json"
        expected = _oracle_report(list_file, POLICY, holds, REF_NOW)
        report = _pipeline(list_file, POLICY, holds, REF_NOW, out)
        _assert_export_matches(report, expected)

    def test_clock_skew_future_clamp(self, tmp_path: Path):
        """Archives beyond reference_now plus skew clamp to reference_now for buckets."""
        suffix = uuid.uuid4().hex[:8]
        list_file = tmp_path / f"skew_{suffix}.list"
        list_file.write_text(
            f"future-{suffix}\t2024-07-01T12:00:00Z\t3000000\t4\n"
            f"normal-{suffix}\t2024-06-30T00:00:00Z\t1000000\t1\n",
            encoding="utf-8",
        )
        policy = tmp_path / "policy.json"
        policy.write_text(
            json.dumps(
                {
                    "clock_skew_sec": 300,
                    "keep_daily": 2,
                    "keep_monthly": 1,
                    "keep_weekly": 1,
                    "keep_yearly": 1,
                    "week_start": "monday",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        out = tmp_path / "report.json"
        expected = _oracle_report(list_file, policy, HOLDS_EMPTY, REF_NOW)
        report = _pipeline(list_file, policy, HOLDS_EMPTY, REF_NOW, out)
        _assert_export_matches(report, expected)
        assert expected["clock_skew_adjustment_count"] >= 1

    def test_weekly_bucket_monday_start(self, tmp_path: Path):
        """Weekly retention respects week_start monday in policy."""
        suffix = uuid.uuid4().hex[:8]
        list_file = tmp_path / f"week_{suffix}.list"
        # 2024-06-03 is Monday; 2024-06-09 is Sunday same ISO week when Monday-start
        list_file.write_text(
            f"mon-{suffix}\t2024-06-03T10:00:00Z\t1000\t1\n"
            f"sun-{suffix}\t2024-06-09T10:00:00Z\t2000\t2\n"
            f"old-{suffix}\t2024-05-01T00:00:00Z\t500\t1\n",
            encoding="utf-8",
        )
        policy = tmp_path / "policy.json"
        policy.write_text(
            json.dumps(
                {
                    "clock_skew_sec": 0,
                    "keep_daily": 1,
                    "keep_monthly": 1,
                    "keep_weekly": 2,
                    "keep_yearly": 1,
                    "week_start": "monday",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        out = tmp_path / "report.json"
        expected = _oracle_report(list_file, policy, HOLDS_EMPTY, REF_NOW)
        report = _pipeline(list_file, policy, HOLDS_EMPTY, REF_NOW, out)
        _assert_export_matches(report, expected)

    def test_compaction_sums_pruned_only(self, tmp_path: Path):
        """compaction_bytes_reclaimable sums pruned archive bytes only."""
        suffix = uuid.uuid4().hex[:8]
        list_file = tmp_path / f"compact_{suffix}.list"
        list_file.write_text(
            f"keep-{suffix}\t2024-06-28T00:00:00Z\t100\t1\n"
            f"prune-{suffix}\t2020-01-01T00:00:00Z\t5000\t7\n",
            encoding="utf-8",
        )
        out = tmp_path / "report.json"
        expected = _oracle_report(list_file, POLICY, HOLDS_EMPTY, REF_NOW)
        report = _pipeline(list_file, POLICY, HOLDS_EMPTY, REF_NOW, out)
        _assert_export_matches(report, expected)

    def test_export_requires_evaluation_block(self, tmp_path: Path):
        """Export fails when evaluate has not populated staging evaluation."""
        suffix = uuid.uuid4().hex[:8]
        list_file = tmp_path / f"noeval_{suffix}.list"
        shutil.copy2(SEED_LIST, list_file)
        _run([str(BIN), "ingest", "--list", str(list_file), "--repo-id", "x"])
        stage = stage_path_for(list_file)
        data = json.loads(stage.read_text(encoding="utf-8"))
        data.pop("evaluation", None)
        stage.write_text(json.dumps(data, sort_keys=True) + "\n", encoding="utf-8")
        out = tmp_path / "report.json"
        proc = _run([str(BIN), "export", "--list", str(list_file), "--out", str(out)], check=False)
        assert proc.returncode != 0

    def test_randomized_list_anti_hardcode(self, tmp_path: Path):
        """Randomized archive timestamps produce oracle-checked decisions."""
        suffix = uuid.uuid4().hex[:12]
        list_file = make_random_list(tmp_path, suffix=suffix, reference_now=REF_NOW, count=14)
        out = tmp_path / "report.json"
        expected = _oracle_report(list_file, POLICY, HOLDS_EMPTY, REF_NOW)
        report = _pipeline(list_file, POLICY, HOLDS_EMPTY, REF_NOW, out)
        _assert_export_matches(report, expected)

    def test_second_evaluate_idempotent(self, tmp_path: Path):
        """Second evaluate with same inputs yields identical export."""
        suffix = uuid.uuid4().hex[:8]
        list_file = make_random_list(tmp_path, suffix=suffix, reference_now=REF_NOW, count=8)
        ref_s = REF_NOW.strftime("%Y-%m-%dT%H:%M:%SZ")
        _run([str(BIN), "ingest", "--list", str(list_file), "--repo-id", "main"])
        _run(
            [
                str(BIN),
                "evaluate",
                "--list",
                str(list_file),
                "--policy",
                str(POLICY),
                "--holds",
                str(HOLDS_EMPTY),
                "--now",
                ref_s,
            ]
        )
        out1 = tmp_path / "r1.json"
        _run([str(BIN), "export", "--list", str(list_file), "--out", str(out1)])
        _run(
            [
                str(BIN),
                "evaluate",
                "--list",
                str(list_file),
                "--policy",
                str(POLICY),
                "--holds",
                str(HOLDS_EMPTY),
                "--now",
                ref_s,
            ]
        )
        out2 = tmp_path / "r2.json"
        _run([str(BIN), "export", "--list", str(list_file), "--out", str(out2)])
        assert out1.read_text(encoding="utf-8") == out2.read_text(encoding="utf-8")

    def test_export_json_compact_sorted(self, tmp_path: Path):
        """Export uses sorted keys, compact separators, trailing newline."""
        suffix = uuid.uuid4().hex[:8]
        list_file = make_random_list(tmp_path, suffix=suffix, reference_now=REF_NOW, count=5)
        out = tmp_path / "report.json"
        expected = _oracle_report(list_file, POLICY, HOLDS_EMPTY, REF_NOW)
        report = _pipeline(list_file, POLICY, HOLDS_EMPTY, REF_NOW, out)
        raw = out.read_text(encoding="utf-8")
        assert raw.endswith("\n")
        assert raw == compact_export(report)
        _assert_export_matches(report, expected)

    def test_staging_contains_repo_id_after_ingest(self, tmp_path: Path):
        """Ingest writes repo_id into staging snapshot."""
        suffix = uuid.uuid4().hex[:8]
        list_file = tmp_path / f"repo_{suffix}.list"
        shutil.copy2(SEED_LIST, list_file)
        _run([str(BIN), "ingest", "--list", str(list_file), "--repo-id", f"repo-{suffix}"])
        stage = json.loads(stage_path_for(list_file).read_text(encoding="utf-8"))
        assert stage["repo_id"] == f"repo-{suffix}"
        assert isinstance(stage["archives"], list)

    def test_pruned_and_kept_sorted_lexicographically(self, tmp_path: Path):
        """kept_archives and pruned_archives are sorted lexicographically."""
        suffix = uuid.uuid4().hex[:6]
        list_file = make_random_list(tmp_path, suffix=suffix, reference_now=REF_NOW, count=10)
        out = tmp_path / "report.json"
        report = _pipeline(list_file, POLICY, HOLDS_EMPTY, REF_NOW, out)
        assert report["kept_archives"] == sorted(report["kept_archives"])
        assert report["pruned_archives"] == sorted(report["pruned_archives"])

    def test_tb3_hidden_skew_fixture(self, tmp_path: Path):
        """TB3 hidden skew fixture reconciles with independent oracle."""
        assert TB3_SKEW.is_dir(), "missing /opt/verifier-fixtures/borg/hidden-skew"
        work = tmp_path / f"tb3_skew_{uuid.uuid4().hex[:8]}"
        work.mkdir()
        list_file = work / "repo.list"
        shutil.copy2(TB3_SKEW / "repo.list", list_file)
        ref_now = datetime(2024, 7, 1, 0, 0, 0, tzinfo=timezone.utc)
        out = work / "report.json"
        expected = _oracle_report(list_file, TB3_SKEW / "policy.json", TB3_SKEW / "holds.json", ref_now)
        report = _pipeline(list_file, TB3_SKEW / "policy.json", TB3_SKEW / "holds.json", ref_now, out)
        _assert_export_matches(report, expected)

    def test_tb3_hidden_holds_prefix_fixture(self, tmp_path: Path):
        """TB3 hidden holds fixture requires prefix-start matching and bucket union."""
        assert TB3_HOLDS.is_dir(), "missing /opt/verifier-fixtures/borg/hidden-holds"
        work = tmp_path / f"tb3_holds_{uuid.uuid4().hex[:8]}"
        work.mkdir()
        list_file = work / "repo.list"
        shutil.copy2(TB3_HOLDS / "repo.list", list_file)
        ref_now = datetime(2024, 7, 1, 0, 0, 0, tzinfo=timezone.utc)
        out = work / "report.json"
        expected = _oracle_report(list_file, TB3_HOLDS / "policy.json", TB3_HOLDS / "holds.json", ref_now)
        report = _pipeline(list_file, TB3_HOLDS / "policy.json", TB3_HOLDS / "holds.json", ref_now, out)
        _assert_export_matches(report, expected)
        assert expected["legal_hold_count"] >= 2

    def test_monthly_yearly_buckets_randomized(self, tmp_path: Path):
        """Monthly and yearly bucket survivors match oracle on randomized fixture."""
        suffix = uuid.uuid4().hex[:10]
        list_file = tmp_path / f"my_{suffix}.list"
        lines = []
        for year in (2022, 2023, 2024):
            for month in (1, 6, 12):
                lines.append(f"arc-{year}-{month}-{suffix}\t{year}-{month:02d}-15T00:00:00Z\t{year*1000}\t{month}")
        list_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        out = tmp_path / "report.json"
        expected = _oracle_report(list_file, POLICY, HOLDS_EMPTY, REF_NOW)
        report = _pipeline(list_file, POLICY, HOLDS_EMPTY, REF_NOW, out)
        _assert_export_matches(report, expected)

    def test_daily_bucket_keeps_newest_per_day(self, tmp_path: Path):
        """Within a calendar day the newest normalized timestamp is kept."""
        suffix = uuid.uuid4().hex[:8]
        list_file = tmp_path / f"daily_{suffix}.list"
        list_file.write_text(
            f"a-{suffix}\t2024-06-30T08:00:00Z\t1000\t1\n"
            f"b-{suffix}\t2024-06-30T20:00:00Z\t2000\t2\n",
            encoding="utf-8",
        )
        policy = tmp_path / "policy.json"
        policy.write_text(
            json.dumps(
                {
                    "clock_skew_sec": 0,
                    "keep_daily": 3,
                    "keep_monthly": 0,
                    "keep_weekly": 0,
                    "keep_yearly": 0,
                    "week_start": "monday",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        out = tmp_path / "report.json"
        expected = _oracle_report(list_file, policy, HOLDS_EMPTY, REF_NOW)
        report = _pipeline(list_file, policy, HOLDS_EMPTY, REF_NOW, out)
        _assert_export_matches(report, expected)
        assert f"b-{suffix}" in report["kept_archives"]
