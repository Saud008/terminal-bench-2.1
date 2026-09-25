"""Harness smoke for gridplan CLI: ingest-stage import-grid and export-stage syndicate-plan."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from bcast_synd_refmath import reference_plan
from bcast_synd_cli import CLI_BIN, FIXTURE_ROOT, PLAN_JSON, SCENARIO_CLEAN, run_pipeline, wipe_state


class TestGridplanHarness:
    def test_binary_present_under_app_bin(self):
        """gridplan binary must be installed at /app/bin/gridplan."""
        assert Path(CLI_BIN).is_file()

    def test_missing_subcommand_exits_nonzero(self):
        """Invoking gridplan without a subcommand must exit non-zero."""
        proc = subprocess.run([CLI_BIN], capture_output=True, text=True, check=False)
        assert proc.returncode != 0

    def test_full_pipeline_exits_zero_on_clean_playout(self):
        """Full import-grid through syndicate-plan pipeline must succeed on clean-playout."""
        wipe_state()
        run_pipeline(SCENARIO_CLEAN)
        plan = json.loads(PLAN_JSON.read_text(encoding="utf-8"))
        assert plan["entries"] == reference_plan(FIXTURE_ROOT, SCENARIO_CLEAN)["entries"]
