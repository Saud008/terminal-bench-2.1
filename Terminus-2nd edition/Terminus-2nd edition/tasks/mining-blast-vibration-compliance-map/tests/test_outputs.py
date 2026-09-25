"""Smoke tests for seismocomply CLI surface."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from seismocomply_cli_support import APP_ROOT, BUFFER_PATH, CATALOG, CLI_BIN, SEED_POOL, SURVEY_DIR, invoke, run_pipeline, wipe
from seismocomply_contract_math import load_survey, reference_atlas

STATE_BUFFER_PATH = "/app/state/peak-correlation-buffer.json"
OUTPUT_ROOT = "/app/output/"


def test_t66a427_seismocomply_binary_exists():
    """Verify seismocomply is installed at /app/bin/seismocomply after rebuild."""
    assert CLI_BIN.is_file()
    proc = subprocess.run([str(CLI_BIN)], cwd=str(APP_ROOT), capture_output=True, text=True, check=False)
    assert proc.returncode != 0


def test_t66a427_load_survey_writes_peak_correlation_buffer_staging_snapshot():
    """Ingest stage load-survey writes staging snapshot at /app/state/peak-correlation-buffer.json (see peak-correlation-buffer-schema)."""
    wipe()
    survey = CATALOG["surveys"][0]
    seed = SEED_POOL[0]
    proc = invoke([str(CLI_BIN), "load-survey", "--seed", seed, "--survey", survey])
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert BUFFER_PATH == APP_ROOT / "state" / "peak-correlation-buffer.json"
    assert BUFFER_PATH.is_file()
    buf = json.loads(BUFFER_PATH.read_text(encoding="utf-8"))
    assert buf["seed"] == seed
    assert buf["survey"] == survey


def test_t66a427_correlate_writes_audit_passport():
    """correlate must persist active audit passport row under /app/work/audit-passport.json."""
    wipe()
    survey = CATALOG["surveys"][1]
    seed = SEED_POOL[1]
    out = run_pipeline(seed, survey)
    passport = json.loads((APP_ROOT / "work" / "audit-passport.json").read_text(encoding="utf-8"))
    assert passport["active"]["seed"] == seed
    record = load_survey(SURVEY_DIR / f"{survey}.json")
    buf = json.loads(BUFFER_PATH.read_text(encoding="utf-8"))
    exp = reference_atlas(seed, survey, record, buf["correlate_seq"])
    got = json.loads(out.read_text(encoding="utf-8"))
    assert got["exceedance_rows"] == exp["exceedance_rows"]


def test_t66a427_publish_atlas_export_stage_output_suffix():
    """Export stage publish-atlas writes exceedance atlas under /app/output/."""
    wipe()
    survey = CATALOG["surveys"][0]
    seed = SEED_POOL[2]
    out = run_pipeline(seed, survey)
    assert str(out).startswith("/app/output/")
    assert out.parent == APP_ROOT / "output"
    assert out.is_file()
    assert out.name.endswith("-atlas.json")


def test_t66a427_instruction_cited_state_and_output_paths():
    """Instruction cites /app/state/peak-correlation-buffer.json and /app/output/ publish targets."""
    wipe()
    survey = CATALOG["surveys"][0]
    seed = SEED_POOL[0]
    run_pipeline(seed, survey)
    assert Path(STATE_BUFFER_PATH).is_file()
    assert Path(OUTPUT_ROOT).is_dir()
    assert any(Path(OUTPUT_ROOT).glob("*-atlas.json"))


def test_t66a427_waveform_decoy_not_in_help():
    """waveform_decoy module must not appear on the seismocomply CLI help surface."""
    proc = invoke([str(CLI_BIN)])
    assert proc.returncode != 0
    assert "waveform" not in (proc.stderr + proc.stdout).lower()
