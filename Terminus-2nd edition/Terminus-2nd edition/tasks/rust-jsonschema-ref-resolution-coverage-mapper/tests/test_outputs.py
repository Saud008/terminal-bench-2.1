"""Verifier contract tests for rust-jsonschema-ref-resolution-coverage-mapper."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from jscov_contract_math import reference_graph, reference_report, reference_staging

APP = Path("/app")
ENV = APP / "environment"
BIN = ENV / "tools" / "jscovmap" / "jscovmap"
BUILD = ENV / "scripts" / "build_all.sh"
REF_EDGES = APP / "state" / "ref_edges.jsonl"
COVERAGE = APP / "state" / "example_coverage.jsonl"
REPORT = APP / "output" / "schema_coverage_report.json"
GRAPH = APP / "output" / "ref_graph.json"
DEFAULT_SCHEMA = ENV / "fixtures" / "schemas"
DEFAULT_EXAMPLES = ENV / "fixtures" / "validation_examples.jsonl"
HIDDEN_ROOT = Path("/opt/verifier-fixtures/jscov_hidden")


def schema_dir() -> Path:
    tb3 = os.environ.get("TB3_SCHEMA_DIR")
    return Path(tb3) if tb3 else DEFAULT_SCHEMA


def examples_file() -> Path:
    tb3 = os.environ.get("TB3_EXAMPLES_FILE")
    return Path(tb3) if tb3 else DEFAULT_EXAMPLES


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)


def rebuild() -> None:
    run(["bash", str(BUILD)])


def run_trace_publish(schema: Path | None = None, examples: Path | None = None) -> None:
    schema = schema or schema_dir()
    examples = examples or examples_file()
    REF_EDGES.parent.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    for p in (REF_EDGES, COVERAGE, REPORT, GRAPH):
        if p.exists():
            p.unlink()
    run(
        [
            str(BIN),
            "trace",
            "--schema-dir",
            str(schema),
            "--examples",
            str(examples),
            "--ref-edges",
            str(REF_EDGES),
            "--coverage",
            str(COVERAGE),
        ]
    )
    run(
        [
            str(BIN),
            "publish",
            "--ref-edges",
            str(REF_EDGES),
            "--coverage",
            str(COVERAGE),
            "--report",
            str(REPORT),
            "--graph",
            str(GRAPH),
        ]
    )


def load_ref_edges() -> list[dict]:
    return [json.loads(ln) for ln in REF_EDGES.read_text(encoding="utf-8").splitlines() if ln.strip()]


def load_coverage_rows() -> list[dict]:
    return [json.loads(ln) for ln in COVERAGE.read_text(encoding="utf-8").splitlines() if ln.strip()]


def load_report() -> dict:
    return json.loads(REPORT.read_text(encoding="utf-8"))


def load_graph() -> dict:
    return json.loads(GRAPH.read_text(encoding="utf-8"))


def test_jscovm_z01():
    """Release rebuild must produce the jscovmap binary under tools/jscovmap."""
    rebuild()
    assert BIN.is_file()


def test_jscovm_z02():
    """Trace and publish must write ref_edges, coverage, report, and ref_graph artifacts."""
    rebuild()
    run_trace_publish()
    assert REF_EDGES.is_file()
    assert COVERAGE.is_file()
    assert REPORT.is_file()
    assert GRAPH.is_file()


def test_jscovm_z03():
    """Coverage report must expose totals and unresolved_refs per export contract."""
    rebuild()
    run_trace_publish()
    data = load_report()
    assert "totals" in data and "unresolved_refs" in data


def test_jscovm_z04():
    """totals.resolved_ref_count must count only resolved ref edges."""
    rebuild()
    run_trace_publish()
    got = load_report()["totals"]
    ref = reference_report(reference_staging(schema_dir(), examples_file()))["totals"]
    assert got["resolved_ref_count"] == ref["resolved_ref_count"]


def test_jscovm_z05():
    """ref_edges.jsonl rows must match independent reference resolution."""
    rebuild()
    run_trace_publish()
    got = load_ref_edges()
    ref = reference_staging(schema_dir(), examples_file())["ref_edges"]
    assert got == ref


def test_jscovm_z06():
    """External http refs must appear as unresolved in ref_edges.jsonl."""
    rebuild()
    run_trace_publish()
    edges = load_ref_edges()
    assert any(e["status"] == "unresolved" and e["target_id"].startswith("https://") for e in edges)


def test_jscovm_z07():
    """tree schema recursive refs must not all be marked unresolved."""
    rebuild()
    run_trace_publish()
    edges = [e for e in load_ref_edges() if e["schema_id"] == "tree"]
    assert any(e["status"] in {"resolved", "recursive"} for e in edges)


def test_jscovm_z08():
    """First combo example anyOf coverage must match reference combinator rules."""
    rebuild()
    run_trace_publish()
    cov = load_coverage_rows()
    alpha = next(c for c in cov if c["example_id"] == "ex-000")
    ref = next(
        c
        for c in reference_staging(schema_dir(), examples_file())["example_coverage"]
        if c["example_id"] == "ex-000"
    )
    assert alpha["any_of_branches"] == ref["any_of_branches"]


def test_jscovm_z09():
    """Second combo example anyOf coverage must match reference combinator rules."""
    rebuild()
    run_trace_publish()
    cov = load_coverage_rows()
    beta = next(c for c in cov if c["example_id"] == "ex-001")
    ref = next(
        c
        for c in reference_staging(schema_dir(), examples_file())["example_coverage"]
        if c["example_id"] == "ex-001"
    )
    assert beta["any_of_branches"] == ref["any_of_branches"]


def test_jscovm_z10():
    """allOf branch coverage must be recorded for satisfied branches."""
    rebuild()
    run_trace_publish()
    cov = load_coverage_rows()
    row = next(c for c in cov if c["example_id"] == "ex-000")
    assert "/allOf/0" in row["all_of_branches"]


def test_jscovm_z11():
    """ref_graph.json nodes must be sorted by id ascending."""
    rebuild()
    run_trace_publish()
    nodes = load_graph()["nodes"]
    ids = [n["id"] for n in nodes]
    assert ids == sorted(ids)


def test_jscovm_z12():
    """ref_graph.json edges must sort by from, to, ref_kind."""
    rebuild()
    run_trace_publish()
    edges = load_graph()["edges"]
    ref = reference_graph(reference_staging(schema_dir(), examples_file()))["edges"]
    assert edges == ref


def test_jscovm_z13():
    """Report example_coverage must match reference staging coverage rows."""
    rebuild()
    run_trace_publish()
    got = load_report()["example_coverage"]
    ref = reference_staging(schema_dir(), examples_file())["example_coverage"]
    assert got == ref


def test_jscovm_z14():
    """Repeated publish with unchanged jsonl staging must produce identical report bytes."""
    rebuild()
    run_trace_publish()
    first = REPORT.read_bytes()
    run(
        [
            str(BIN),
            "publish",
            "--ref-edges",
            str(REF_EDGES),
            "--coverage",
            str(COVERAGE),
            "--report",
            str(REPORT),
            "--graph",
            str(GRAPH),
        ]
    )
    second = REPORT.read_bytes()
    assert first == second


def test_jscovm_z15():
    """Publish-only stage must consume existing jsonl staging without re-tracing."""
    rebuild()
    schema = schema_dir()
    examples = examples_file()
    alt_edges = APP / "state" / "alt_ref_edges.jsonl"
    alt_cov = APP / "state" / "alt_example_coverage.jsonl"
    alt_report = APP / "output" / "alt_report.json"
    alt_graph = APP / "output" / "alt_graph.json"
    run(
        [
            str(BIN),
            "trace",
            "--schema-dir",
            str(schema),
            "--examples",
            str(examples),
            "--ref-edges",
            str(alt_edges),
            "--coverage",
            str(alt_cov),
        ]
    )
    run(
        [
            str(BIN),
            "publish",
            "--ref-edges",
            str(alt_edges),
            "--coverage",
            str(alt_cov),
            "--report",
            str(alt_report),
            "--graph",
            str(alt_graph),
        ]
    )
    data = json.loads(alt_report.read_text(encoding="utf-8"))
    assert data["totals"]["example_count"] >= 3


def test_jscovm_z16():
    """decoy_validate scaffolding must not appear in coverage export output."""
    rebuild()
    run_trace_publish()
    raw = REPORT.read_text(encoding="utf-8")
    assert "wrap_schema_bytes" not in raw


def test_jscovm_z17():
    """TB3 hidden ledger schema anchor refs must match reference resolution."""
    if not HIDDEN_ROOT.is_dir():
        return
    hidden_schema = HIDDEN_ROOT / "schemas"
    hidden_examples = HIDDEN_ROOT / "examples.jsonl"
    if not hidden_schema.is_dir() or not hidden_examples.is_file():
        return
    rebuild()
    os.environ["TB3_SCHEMA_DIR"] = str(hidden_schema)
    os.environ["TB3_EXAMPLES_FILE"] = str(hidden_examples)
    try:
        run_trace_publish(hidden_schema, hidden_examples)
        got = load_ref_edges()
        ref = reference_staging(hidden_schema, hidden_examples)["ref_edges"]
        assert got == ref
    finally:
        os.environ.pop("TB3_SCHEMA_DIR", None)
        os.environ.pop("TB3_EXAMPLES_FILE", None)


def test_jscovm_z18():
    """TB3 schema directory override must drive trace and publish totals."""
    if not HIDDEN_ROOT.is_dir():
        return
    hidden_schema = HIDDEN_ROOT / "schemas"
    hidden_examples = HIDDEN_ROOT / "examples.jsonl"
    if not hidden_schema.is_dir() or not hidden_examples.is_file():
        return
    rebuild()
    os.environ["TB3_SCHEMA_DIR"] = str(hidden_schema)
    os.environ["TB3_EXAMPLES_FILE"] = str(hidden_examples)
    try:
        run_trace_publish(hidden_schema, hidden_examples)
        got = load_report()["totals"]
        ref = reference_report(reference_staging(hidden_schema, hidden_examples))["totals"]
        assert got["resolved_ref_count"] == ref["resolved_ref_count"]
    finally:
        os.environ.pop("TB3_SCHEMA_DIR", None)
        os.environ.pop("TB3_EXAMPLES_FILE", None)


def test_jscovm_z19():
    """Grading must invoke jscovmap via subprocess after rebuild."""
    rebuild()
    schema = schema_dir()
    examples = examples_file()
    probe_edges = APP / "state" / "probe_ref_edges.jsonl"
    probe_cov = APP / "state" / "probe_example_coverage.jsonl"
    probe_report = APP / "output" / "probe_report.json"
    probe_graph = APP / "output" / "probe_graph.json"
    run(
        [
            str(BIN),
            "trace",
            "--schema-dir",
            str(schema),
            "--examples",
            str(examples),
            "--ref-edges",
            str(probe_edges),
            "--coverage",
            str(probe_cov),
        ]
    )
    run(
        [
            str(BIN),
            "publish",
            "--ref-edges",
            str(probe_edges),
            "--coverage",
            str(probe_cov),
            "--report",
            str(probe_report),
            "--graph",
            str(probe_graph),
        ]
    )
    data = json.loads(probe_report.read_text(encoding="utf-8"))
    assert data["totals"]["example_count"] >= 3


def test_jscovm_z20():
    """Instruction artifact paths ref_edges, coverage, report, and ref_graph must exist after pipeline."""
    rebuild()
    run_trace_publish()
    for path in (
        "/app/state/ref_edges.jsonl",
        "/app/state/example_coverage.jsonl",
        "/app/output/schema_coverage_report.json",
        "/app/output/ref_graph.json",
    ):
        assert Path(path).is_file(), path


def test_jscovm_z21():
    """Publish export must read jsonl staging; corrupting ingest-side examples must not alter export output."""
    rebuild()
    run_trace_publish()
    expected_totals = load_report()["totals"]
    expected_graph = load_graph()
    examples = examples_file()
    backup = examples.read_text(encoding="utf-8")
    try:
        examples.write_text("{}\n", encoding="utf-8")
        run(
            [
                str(BIN),
                "publish",
                "--ref-edges",
                str(REF_EDGES),
                "--coverage",
                str(COVERAGE),
                "--report",
                str(REPORT),
                "--graph",
                str(GRAPH),
            ]
        )
        assert load_report()["totals"] == expected_totals
        assert load_graph() == expected_graph
    finally:
        examples.write_text(backup, encoding="utf-8")


def test_jscovm_z22():
    """Trace ingest must write ref_edges jsonl staging snapshot consumed by publish export."""
    rebuild()
    run_trace_publish()
    edges = REF_EDGES.read_text(encoding="utf-8").strip().splitlines()
    assert len(edges) >= 3
    first = json.loads(edges[0])
    assert "schema_id" in first and "ref_pointer" in first


def test_jscovm_z23():
    """Bundled person schema cross-file refs into common must resolve."""
    rebuild()
    run_trace_publish()
    edges = [e for e in load_ref_edges() if e["schema_id"] == "person"]
    assert any(e["status"] == "resolved" and "common" in e["target_id"] for e in edges)


def test_jscovm_z24():
    """Schema ids in ref_edges must use $id basename per ref_resolution_overview.md."""
    rebuild()
    run_trace_publish()
    schema_ids = {e["schema_id"] for e in load_ref_edges()}
    assert "person" in schema_ids
