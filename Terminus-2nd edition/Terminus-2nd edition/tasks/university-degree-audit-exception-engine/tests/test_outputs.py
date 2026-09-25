"""Parametrized registrar degree audit matrix verifier tests."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from deg_workspace import (
    CLI_BIN,
    EVAL_PASS,
    FIXTURE_ROOT,
    LOAD_MANIFEST,
    REPORT_JSON,
    REQ_EVAL,
    SCENARIO_CLEAN,
    SCENARIO_STABLE,
    STAGING_JSON,
    WORKSPACE_DB,
    execute_degree_audit_workflow,
    load_json,
)
from registrar_graph_sim import reference_report, reference_material

PATH_EVALUATION_PASS = "/app/state/evaluation-pass.json"
PATH_LOAD_MANIFEST = "/app/state/load-manifest.json"
PATH_TRANSCRIPT_STAGING = "/app/state/transcript-material.json"
PATH_REGISTRAR_WORKSPACE = "/app/state/registrar-workspace.db"
PATH_REQUIREMENT_EVAL = "/app/work/requirement-eval.json"
PATH_DEGREE_AUDIT_REPORT = "/app/output/degree-audit-report.json"


@pytest.mark.parametrize(
    "scenario",
    ["clean-audit", "stable-report"],
)
def test_registrar_matrix_matches_graph_sim(scenario: str):
    """End-to-end workflow output must match independent requirement graph simulator."""
    execute_degree_audit_workflow(scenario)
    report = load_json(REPORT_JSON)
    ref = reference_report(FIXTURE_ROOT, scenario)
    assert report["run_stamp"] == ref["run_stamp"]
    assert report["students"] == ref["students"]


def test_registrar_cli_binary_present():
    """Compiled degaudit binary must exist at /app/bin/degaudit."""
    assert Path(CLI_BIN).is_file()


def test_registrar_cli_rejects_missing_subcommand():
    """Bare degaudit invocation must exit non-zero."""
    proc = subprocess.run([CLI_BIN], capture_output=True, text=True, check=False)
    assert proc.returncode != 0


@pytest.mark.parametrize(
    "path,label",
    [
        (WORKSPACE_DB, "registrar-workspace.db"),
        (LOAD_MANIFEST, "load-manifest.json"),
        (STAGING_JSON, "transcript-material.json"),
        (REQ_EVAL, "requirement-eval.json"),
        (EVAL_PASS, "evaluation-pass.json"),
        (REPORT_JSON, "degree-audit-report.json"),
    ],
)
def test_registrar_artifact_paths_materialized(path: Path, label: str):
    """Each instruction-cited artifact path must exist after the full workflow."""
    execute_degree_audit_workflow(SCENARIO_CLEAN)
    assert path.is_file(), f"missing {label}"


def test_registrar_staging_fingerprint_anti_cheat():
    """Transcript materialization digest must match registrar_graph_sim independent math."""
    execute_degree_audit_workflow(SCENARIO_CLEAN)
    body = load_json(STAGING_JSON)
    ref = reference_material(FIXTURE_ROOT, SCENARIO_CLEAN)
    assert body["material_fingerprint"] == ref["material_fingerprint"]
    assert body["course_count"] == ref["course_count"]


def test_registrar_publish_gate_without_audit_pass():
    """publish-report must fail when evaluation-pass.json shows zero passes."""
    proc = subprocess.run(
        [CLI_BIN, "publish-report", "--scenario", SCENARIO_CLEAN],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode != 0


def test_registrar_stable_matrix_repeat_run_bytes():
    """stable-report scenario yields identical JSON payload across two cold runs."""
    execute_degree_audit_workflow(SCENARIO_STABLE)
    first = REPORT_JSON.read_text(encoding="utf-8")
    execute_degree_audit_workflow(SCENARIO_STABLE)
    second = REPORT_JSON.read_text(encoding="utf-8")
    assert json.loads(first) == json.loads(second)


def test_registrar_audit_pass_monotonic():
    """Repeated workflows must increment audit_pass in evaluation-pass.json."""
    execute_degree_audit_workflow(SCENARIO_CLEAN)
    first = load_json(EVAL_PASS)["audit_pass"]
    execute_degree_audit_workflow(SCENARIO_CLEAN)
    second = load_json(EVAL_PASS)["audit_pass"]
    assert second == first + 1


def test_registrar_requirement_row_ordering():
    """Requirement rows must sort by req_id ascending in the published matrix."""
    execute_degree_audit_workflow(SCENARIO_CLEAN)
    report = load_json(REPORT_JSON)
    req_ids = [row["req_id"] for row in report["students"][0]["requirements"]]
    assert req_ids == sorted(req_ids)


def test_app_state_load_manifest_json_written():
    """load-scenario must create /app/state/load-manifest.json with scenario metadata."""
    execute_degree_audit_workflow(SCENARIO_CLEAN)
    assert Path(PATH_LOAD_MANIFEST).is_file()


def test_app_state_evaluation_pass_json_written():
    """run-audit must create /app/state/evaluation-pass.json with audit_pass counter."""
    execute_degree_audit_workflow(SCENARIO_CLEAN)
    assert Path(PATH_EVALUATION_PASS).is_file()


def test_registrar_ingest_export_stage_split():
    """Ingest load-scenario and export publish-report remain separate CLI stages with staging between."""
    execute_degree_audit_workflow(SCENARIO_CLEAN)
    assert Path(PATH_LOAD_MANIFEST).is_file()
    assert Path(PATH_TRANSCRIPT_STAGING).is_file()
    assert Path(PATH_DEGREE_AUDIT_REPORT).is_file()


def test_instruction_cited_paths_exist_after_pipeline():
    """Cover every absolute output path named in instruction.md after a full workflow."""
    execute_degree_audit_workflow(SCENARIO_CLEAN)
    cited = (
        PATH_REGISTRAR_WORKSPACE,
        PATH_LOAD_MANIFEST,
        PATH_TRANSCRIPT_STAGING,
        PATH_EVALUATION_PASS,
        PATH_REQUIREMENT_EVAL,
        PATH_DEGREE_AUDIT_REPORT,
    )
    for path_str in cited:
        assert Path(path_str).is_file(), path_str
