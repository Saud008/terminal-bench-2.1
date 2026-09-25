"""Independent behavioral verifier for systemd timer calendar drift planner."""

from __future__ import annotations

import json
import shutil
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path

from drift_plan_math import (
    export_report,
    load_json,
    manifest_path_for,
    merge_timer_bundle,
    plan_timer,
)

BIN = Path("/usr/local/bin/systemd-timer-planner")
SEED_BUNDLE = Path("/app/fixtures/seed/backup.timer.bundle")
CONTEXT = Path("/app/context/default.json")
OUTPUT = Path("/app/output")
REF_NOW = datetime(2024, 7, 1, 12, 0, 0, tzinfo=timezone.utc)
TIMER_NAME = "backup"


def _run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=check, capture_output=True, text=True)


def _oracle_report(bundle: Path, timer_name: str, context: Path, ref_now: datetime) -> dict:
    ctx = load_json(context)
    plan = plan_timer(bundle, timer_name, ctx, ref_now)
    return export_report(plan)


def reference_oracle_report(bundle: Path, timer_name: str, context: Path, ref_now: datetime) -> dict:
    """Public alias for independent reference oracle (probe contract)."""
    return _oracle_report(bundle, timer_name, context, ref_now)


def reference_merge_timer_bundle(bundle: Path, timer_name: str) -> dict[str, str]:
    """Public alias for drop-in merge reference."""
    return merge_timer_bundle(bundle, timer_name)


def _pipeline(bundle: Path, timer_name: str, context: Path, ref_now: datetime, out: Path) -> dict:
    ref_s = ref_now.strftime("%Y-%m-%dT%H:%M:%SZ")
    _run([str(BIN), "load", "--bundle", str(bundle), "--timer-name", timer_name])
    _run([str(BIN), "forecast", "--bundle", str(bundle), "--context", str(context), "--now", ref_s])
    _run([str(BIN), "write-report", "--bundle", str(bundle), "--out", str(out)])
    return json.loads(out.read_text(encoding="utf-8"))


def _assert_report_matches(report: dict, expected: dict) -> None:
    for key in (
        "timer_name",
        "timer_mode",
        "timezone_normalized",
        "next_fire_utc_earliest",
        "next_fire_utc_latest",
        "missed_run_count",
        "missed_run_utc",
        "catchup_run_count",
        "catchup_run_utc",
        "randomized_delay_sec",
        "accuracy_sec",
        "drop_in_overrides_applied",
        "persistent_enabled",
        "plan_digest",
    ):
        assert report[key] == expected[key], f"mismatch on {key}"


class TestSystemdTimerDriftPlanner:
    """Timer bundle load / forecast / write-report with independent drift oracle."""

    def test_tad5225_driver_exists(self):
        """systemd-timer-planner driver is on PATH."""
        assert BIN.is_file() or Path("/app/scripts/systemd-timer-planner.sh").is_file()

    def test_tad5225_worked_example_paths(self):
        """Worked example writes stage manifest and /app/output/drift-report.json."""
        bundle = SEED_BUNDLE
        manifest = manifest_path_for(bundle)
        export = Path("/app/output/drift-report.json")
        if manifest.exists():
            manifest.unlink()
        if export.exists():
            export.unlink()
        expected = _oracle_report(bundle, TIMER_NAME, CONTEXT, REF_NOW)
        report = _pipeline(bundle, TIMER_NAME, CONTEXT, REF_NOW, export)
        assert manifest.is_file()
        assert export.is_file()
        _assert_report_matches(report, expected)

    def test_tad5225_manifest_under_stage_not_beside_bundle(self, tmp_path: Path):
        """Manifest path is /app/stage/manifests/BUNDLE_BASENAME.json."""
        suffix = uuid.uuid4().hex[:8]
        work = tmp_path / f"edge_{suffix}.timer.bundle"
        work.mkdir()
        shutil.copytree(SEED_BUNDLE / "backup.timer.d", work / "backup.timer.d")
        shutil.copy2(SEED_BUNDLE / "backup.timer", work / "backup.timer")
        shutil.copy2(SEED_BUNDLE / "activation.json", work / "activation.json")
        manifest = manifest_path_for(work)
        _run([str(BIN), "load", "--bundle", str(work), "--timer-name", "backup"])
        assert manifest.is_file()
        assert manifest.parent == Path("/app/stage/manifests")

    def test_tad5225_seed_bundle_matches_oracle(self):
        """Seed bundle drift report matches independent oracle at reference now."""
        out = OUTPUT / f"seed-{uuid.uuid4().hex[:8]}.json"
        expected = _oracle_report(SEED_BUNDLE, TIMER_NAME, CONTEXT, REF_NOW)
        report = _pipeline(SEED_BUNDLE, TIMER_NAME, CONTEXT, REF_NOW, out)
        _assert_report_matches(report, expected)

    def test_tad5225_dropin_merge_precedence(self):
        """Merged timer in manifest matches reference drop-in precedence merge."""
        expected_merge = merge_timer_bundle(SEED_BUNDLE, TIMER_NAME)
        out = OUTPUT / f"merge-{uuid.uuid4().hex[:8]}.json"
        _pipeline(SEED_BUNDLE, TIMER_NAME, CONTEXT, REF_NOW, out)
        manifest = json.loads(manifest_path_for(SEED_BUNDLE).read_text(encoding="utf-8"))
        assert manifest["merged_timer"] == expected_merge

    def test_tad5225_dropin_list_lex_sorted(self):
        """drop_in_overrides_applied lists fragments sorted by basename."""
        out = OUTPUT / f"drop-{uuid.uuid4().hex[:8]}.json"
        expected = _oracle_report(SEED_BUNDLE, TIMER_NAME, CONTEXT, REF_NOW)
        report = _pipeline(SEED_BUNDLE, TIMER_NAME, CONTEXT, REF_NOW, out)
        assert report["drop_in_overrides_applied"] == expected["drop_in_overrides_applied"]

    def test_tad5225_missed_runs_timezone_calendar(self):
        """Missed weekday calendar slots honor timezone normalization."""
        out = OUTPUT / f"miss-{uuid.uuid4().hex[:8]}.json"
        expected = _oracle_report(SEED_BUNDLE, TIMER_NAME, CONTEXT, REF_NOW)
        report = _pipeline(SEED_BUNDLE, TIMER_NAME, CONTEXT, REF_NOW, out)
        assert report["missed_run_utc"] == expected["missed_run_utc"]

    def test_tad5225_persistent_catchup_queue(self):
        """Persistent timers enqueue missed slots into catchup_run_utc."""
        out = OUTPUT / f"catch-{uuid.uuid4().hex[:8]}.json"
        expected = _oracle_report(SEED_BUNDLE, TIMER_NAME, CONTEXT, REF_NOW)
        report = _pipeline(SEED_BUNDLE, TIMER_NAME, CONTEXT, REF_NOW, out)
        assert report["catchup_run_utc"] == expected["catchup_run_utc"]

    def test_tad5225_randomized_delay_window(self):
        """RandomizedDelaySec sets latest next fire bound above earliest."""
        out = OUTPUT / f"jitter-{uuid.uuid4().hex[:8]}.json"
        expected = _oracle_report(SEED_BUNDLE, TIMER_NAME, CONTEXT, REF_NOW)
        report = _pipeline(SEED_BUNDLE, TIMER_NAME, CONTEXT, REF_NOW, out)
        assert report["next_fire_utc_earliest"] == expected["next_fire_utc_earliest"]
        assert report["next_fire_utc_latest"] == expected["next_fire_utc_latest"]

    def test_tad5225_write_report_requires_forecast(self, tmp_path: Path):
        """write-report fails when forecast block missing from manifest."""
        bundle = tmp_path / f"empty-{uuid.uuid4().hex[:8]}.timer.bundle"
        bundle.mkdir()
        (bundle / "empty.timer").write_text("[Timer]\nOnCalendar=*-*-* 01:00:00\n", encoding="utf-8")
        (bundle / "activation.json").write_text(
            '{"last_trigger_utc":"2024-01-01T00:00:00Z","unit_active_monotonic_usec":0}\n',
            encoding="utf-8",
        )
        _run([str(BIN), "load", "--bundle", str(bundle), "--timer-name", "empty"])
        out = tmp_path / "report.json"
        proc = _run([str(BIN), "write-report", "--bundle", str(bundle), "--out", str(out)], check=False)
        assert proc.returncode != 0

    def test_tad5225_plan_digest_contract(self):
        """plan_digest matches export-format hash contract."""
        out = OUTPUT / f"digest-{uuid.uuid4().hex[:8]}.json"
        expected = _oracle_report(SEED_BUNDLE, TIMER_NAME, CONTEXT, REF_NOW)
        report = _pipeline(SEED_BUNDLE, TIMER_NAME, CONTEXT, REF_NOW, out)
        assert report["plan_digest"] == expected["plan_digest"]

    def test_tad5225_export_json_shape(self):
        """Export JSON is compact, sorted, and ends with newline."""
        out = OUTPUT / f"fmt-{uuid.uuid4().hex[:8]}.json"
        _pipeline(SEED_BUNDLE, TIMER_NAME, CONTEXT, REF_NOW, out)
        raw = out.read_text(encoding="utf-8")
        assert raw.endswith("\n")
        assert ", " not in raw.split("\n")[0]

    def test_tad5225_calendar_mode_classification(self):
        """Seed bundle reports calendar timer_mode."""
        out = OUTPUT / f"mode-{uuid.uuid4().hex[:8]}.json"
        report = _pipeline(SEED_BUNDLE, TIMER_NAME, CONTEXT, REF_NOW, out)
        assert report["timer_mode"] == "calendar"

    def test_tad5225_staging_manifest_snapshot_after_load(self):
        """load ingest stage writes staging manifest snapshot JSON under /app/stage/manifests."""
        manifest = manifest_path_for(SEED_BUNDLE)
        if manifest.exists():
            manifest.unlink()
        _run([str(BIN), "load", "--bundle", str(SEED_BUNDLE), "--timer-name", TIMER_NAME])
        assert manifest.is_file()
        doc = json.loads(manifest.read_text(encoding="utf-8"))
        assert "merged_timer" in doc
        assert "ingest" in doc
        assert doc["ingest"]["timer_name"] == TIMER_NAME

    def test_tad5225_hidden_persistent_bundle(self):
        """Hidden /opt/verifier-fixtures persistent timezone ingest bundle."""
        bundle = Path("/opt/verifier-fixtures/systemd-timer/hidden-persistent.timer.bundle")
        name = "hidden-persistent"
        ctx = OUTPUT / f"ctx-{uuid.uuid4().hex[:8]}.json"
        ctx.write_text(json.dumps({"host_timezone": "UTC", "boot_monotonic_usec": 0}) + "\n", encoding="utf-8")
        ref = datetime(2024, 6, 10, 6, 0, 0, tzinfo=timezone.utc)
        out = OUTPUT / f"hidp-{uuid.uuid4().hex[:8]}.json"
        expected = _oracle_report(bundle, name, ctx, ref)
        report = _pipeline(bundle, name, ctx, ref, out)
        _assert_report_matches(report, expected)

    def test_tad5225_hidden_monotonic_bundle(self):
        """Hidden /opt/verifier-fixtures monotonic OnUnitActiveSec ingest bundle."""
        bundle = Path("/opt/verifier-fixtures/systemd-timer/hidden-monotonic.timer.bundle")
        name = "hidden-monotonic"
        ctx = OUTPUT / f"ctxm-{uuid.uuid4().hex[:8]}.json"
        ctx.write_text(json.dumps({"host_timezone": "UTC", "boot_monotonic_usec": 2000000}) + "\n", encoding="utf-8")
        ref = datetime(2024, 7, 1, 0, 0, 0, tzinfo=timezone.utc)
        out = OUTPUT / f"hidm-{uuid.uuid4().hex[:8]}.json"
        expected = _oracle_report(bundle, name, ctx, ref)
        report = _pipeline(bundle, name, ctx, ref, out)
        _assert_report_matches(report, expected)
        assert report["timer_mode"] == "monotonic"

    def test_tad5225_weekday_range_skips_weekend(self, tmp_path: Path):
        """Mon..Fri calendar excludes weekend missed slots."""
        bundle = tmp_path / "wk.timer.bundle"
        bundle.mkdir()
        (bundle / "wk.timer").write_text("[Timer]\nOnCalendar=Mon..Fri *-*-* 08:00:00\n", encoding="utf-8")
        (bundle / "activation.json").write_text(
            '{"last_trigger_utc":"2024-06-07T08:00:00Z","unit_active_monotonic_usec":0}\n',
            encoding="utf-8",
        )
        ctx = tmp_path / "ctx.json"
        ctx.write_text(json.dumps({"host_timezone": "UTC", "boot_monotonic_usec": 0}) + "\n", encoding="utf-8")
        ref = datetime(2024, 6, 10, 9, 0, 0, tzinfo=timezone.utc)
        out = tmp_path / "report.json"
        expected = _oracle_report(bundle, "wk", ctx, ref)
        report = _pipeline(bundle, "wk", ctx, ref, out)
        assert report["missed_run_utc"] == expected["missed_run_utc"]

    def test_tad5225_load_writes_merged_timer(self):
        """load stores merged_timer in stage manifest."""
        manifest = manifest_path_for(SEED_BUNDLE)
        if manifest.exists():
            manifest.unlink()
        _run([str(BIN), "load", "--bundle", str(SEED_BUNDLE), "--timer-name", TIMER_NAME])
        doc = json.loads(manifest.read_text(encoding="utf-8"))
        assert "merged_timer" in doc

    def test_tad5225_accuracy_sec_exported(self):
        """accuracy_sec from merged timer appears in export."""
        out = OUTPUT / f"acc-{uuid.uuid4().hex[:8]}.json"
        expected = _oracle_report(SEED_BUNDLE, TIMER_NAME, CONTEXT, REF_NOW)
        report = _pipeline(SEED_BUNDLE, TIMER_NAME, CONTEXT, REF_NOW, out)
        assert report["accuracy_sec"] == expected["accuracy_sec"]

    def test_tad5225_reforecast_changes_digest(self):
        """Changing reference now updates plan_digest after replan."""
        out1 = OUTPUT / f"seq1-{uuid.uuid4().hex[:8]}.json"
        out2 = OUTPUT / f"seq2-{uuid.uuid4().hex[:8]}.json"
        ref1 = datetime(2024, 7, 1, 12, 0, 0, tzinfo=timezone.utc)
        ref2 = datetime(2024, 7, 5, 12, 0, 0, tzinfo=timezone.utc)
        r1 = _pipeline(SEED_BUNDLE, TIMER_NAME, CONTEXT, ref1, out1)
        r2 = _pipeline(SEED_BUNDLE, TIMER_NAME, CONTEXT, ref2, out2)
        assert r1["plan_digest"] != r2["plan_digest"]

    def test_tad5225_default_context_path(self):
        """Default context file at /app/context/default.json is accepted."""
        out = OUTPUT / f"ctx-{uuid.uuid4().hex[:8]}.json"
        expected = _oracle_report(SEED_BUNDLE, TIMER_NAME, CONTEXT, REF_NOW)
        report = _pipeline(SEED_BUNDLE, TIMER_NAME, CONTEXT, REF_NOW, out)
        _assert_report_matches(report, expected)
