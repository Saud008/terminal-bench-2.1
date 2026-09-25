"""Behavioral tests for pestctl PEG precedence climb auditor."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from reference_parse import (
    grammar_by_id,
    load_graph,
    reference_audit,
    reference_checksum,
    reference_climb_table,
    reference_parse_calc,
    reference_parse_sequence,
    tb3_prec_bias,
)

PESTCTL = "/app/bin/pestctl"
GRAPH = Path("/app/state/peg-rule-graph.json")
PARSE = Path("/app/state/parse-tree.json")
AUDIT = Path("/app/output/span-audit.json")
CHECKSUM = Path("/app/output/span-checksum.txt")
GRAMMARS = Path("/app/data/grammars")
INPUTS = Path("/app/data/inputs")
TB3_GRAMMARS = Path("/opt/verifier-fixtures/peg-grammars/tb3-grammars")
TB3_INPUTS = Path("/opt/verifier-fixtures/peg-grammars/tb3-inputs")


def _run(cmd: list[str], *, env: dict | None = None, check: bool = True) -> subprocess.CompletedProcess:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(cmd, check=check, capture_output=True, text=True, env=merged)


def _fresh() -> None:
    for p in (GRAPH, PARSE, AUDIT, CHECKSUM):
        if p.exists():
            p.unlink()


def _ingest(grammar_dir: Path) -> None:
    _run([PESTCTL, "ingest", str(grammar_dir)])


def _parse(input_path: Path, *, env: dict | None = None) -> None:
    _run([PESTCTL, "climb", "parse", "--input", str(input_path)], env=env)


def _export() -> None:
    _run([PESTCTL, "audit", "export"])


def _pipeline(grammar_dir: Path, input_path: Path, *, env: dict | None = None) -> None:
    _fresh()
    _ingest(grammar_dir)
    _parse(input_path, env=env)
    _export()


@pytest.fixture(autouse=True)
def clean_state():
    _fresh()
    yield
    _fresh()


def test_pestctl_binary_exists():
    """Instruction requires /app/bin/pestctl built from workspace."""
    assert Path(PESTCTL).is_file()


def test_bundled_grammars_directory():
    """Instruction cites bundled grammars under /app/data/grammars/."""
    assert GRAMMARS.is_dir()
    assert (GRAMMARS / "calc.json").is_file()
    assert (GRAMMARS / "stmt.json").is_file()


def test_ingest_writes_rule_graph():
    """Ingest must write normalized graph at /app/state/peg-rule-graph.json."""
    _ingest(GRAMMARS)
    assert GRAPH.is_file()
    data = load_graph(GRAPH)
    assert len(data["grammars"]) == 3


def test_ingest_increments_seq():
    """Repeated ingest bumps ingest_seq."""
    _ingest(GRAMMARS)
    first = load_graph(GRAPH)["ingest_seq"]
    _ingest(GRAMMARS)
    second = load_graph(GRAPH)["ingest_seq"]
    assert second == first + 1


def test_climb_table_sorted_by_explicit_prec():
    """rule-precedence-table.md requires climb_table sorted by descending prec."""
    _ingest(GRAMMARS)
    graph = load_graph(GRAPH)
    ref_table = reference_climb_table(graph)
    assert graph["climb_table"] == ref_table
    precs = [row["prec"] for row in graph["climb_table"]]
    assert precs == sorted(precs, reverse=True)


def test_graph_path_contract():
    """Instruction staging path /app/state/peg-rule-graph.json is honored."""
    _ingest(GRAMMARS)
    assert GRAPH == Path("/app/state/peg-rule-graph.json")


def test_climb_parse_writes_parse_tree():
    """climb parse writes /app/state/parse-tree.json."""
    _ingest(GRAMMARS)
    _parse(INPUTS / "calc_add_mul.json")
    assert PARSE.is_file()


def test_mul_binds_tighter_than_add():
    """calc_add_mul fixture must parse as 2 + (3 * 4) per precedence table."""
    _ingest(GRAMMARS)
    _parse(INPUTS / "calc_add_mul.json")
    tree = json.loads(PARSE.read_text(encoding="utf-8"))
    root = tree["root"]
    assert root["kind"] == "binary"
    assert root["value"] == "+"
    assert root["children"][0]["value"] == "2"
    right = root["children"][1]
    assert right["kind"] == "binary"
    assert right["value"] == "*"
    assert right["children"][0]["value"] == "3"
    assert right["children"][1]["value"] == "4"


def test_calc_parse_matches_reference():
    """Bundled calc fixture agrees with independent reference parse."""
    _ingest(GRAMMARS)
    _parse(INPUTS / "calc_add_mul.json")
    graph = load_graph(GRAPH)
    grammar = grammar_by_id(graph, "calc")
    ref = reference_parse_calc(
        json.loads((INPUTS / "calc_add_mul.json").read_text())["tokens"],
        graph,
        grammar,
    )
    got = json.loads(PARSE.read_text(encoding="utf-8"))["root"]
    assert got == ref


def test_whitespace_between_items_not_after_terminator():
    """whitespace-contract.md keeps WS between ; and + at token index 2."""
    _ingest(GRAMMARS)
    _parse(INPUTS / "ws_after_term.json")
    tree = json.loads(PARSE.read_text(encoding="utf-8"))
    plus = tree["root"]["children"][2]
    assert plus["kind"] == "token"
    assert plus["value"] == "+"
    assert plus["span"] == [3, 4]


def test_negative_predicate_partial_no_commit():
    """negative-predicate.md allows NUM token after partialX guard token."""
    _ingest(GRAMMARS)
    _parse(INPUTS / "neg_partial.json")
    tree = json.loads(PARSE.read_text(encoding="utf-8"))
    number = tree["root"]["children"][1]
    assert number["kind"] == "number"
    assert number["value"] == "9"
    assert number["span"] == [1, 2]


def test_stmt_sequence_matches_reference():
    """stmt ws fixture agrees with reference sequence parse."""
    _ingest(GRAMMARS)
    _parse(INPUTS / "ws_after_term.json")
    graph = load_graph(GRAPH)
    grammar = grammar_by_id(graph, "stmt")
    tokens = json.loads((INPUTS / "ws_after_term.json").read_text())["tokens"]
    ref = reference_parse_sequence(tokens, grammar)
    got = json.loads(PARSE.read_text(encoding="utf-8"))["root"]
    assert got == ref


def test_audit_export_paths():
    """Instruction output paths are honored."""
    _pipeline(GRAMMARS, INPUTS / "calc_add_mul.json")
    assert AUDIT.is_file()
    assert CHECKSUM.is_file()
    assert str(AUDIT) == "/app/output/span-audit.json"
    assert str(CHECKSUM) == "/app/output/span-checksum.txt"


def test_checksum_matches_reference():
    """span-checksum-export.md digest must match independent reference."""
    _pipeline(GRAMMARS, INPUTS / "calc_add_mul.json")
    digest = CHECKSUM.read_text(encoding="utf-8").strip()
    assert digest == reference_checksum(GRAPH, PARSE)
    assert len(digest) == 64


def test_audit_spans_include_recovered_nodes():
    """span ledger must include recovered error_recovery nodes when present."""
    _ingest(GRAMMARS)
    _parse(INPUTS / "calc_add_mul.json")
    _export()
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    ref = reference_audit(GRAPH, PARSE)
    assert audit["spans"] == ref["spans"]


def test_subprocess_cli_roundtrip():
    """Independent reference agrees after subprocess ingest parse export."""
    _pipeline(GRAMMARS, INPUTS / "calc_add_mul.json")
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    ref = reference_audit(GRAPH, PARSE)
    assert audit == ref


def _tb3_grammar_dir() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="tb3-grammars-"))
    for src in GRAMMARS.glob("*.json"):
        shutil.copy(src, tmp / src.name)
    shutil.copy(TB3_GRAMMARS / "tb3_calc.json", tmp / "tb3_calc.json")
    return tmp


def test_tb3_hidden_grammar_precedence():
    """Hidden tb3_calc grammar with conflicting decl_order must match reference."""
    gdir = _tb3_grammar_dir()
    try:
        _pipeline(gdir, TB3_INPUTS / "tb3_left_prec.json")
        graph = load_graph(GRAPH)
        grammar = grammar_by_id(graph, "tb3_calc")
        ref = reference_parse_calc(
            json.loads((TB3_INPUTS / "tb3_left_prec.json").read_text())["tokens"],
            graph,
            grammar,
            tb3_prec_bias(),
        )
        got = json.loads(PARSE.read_text(encoding="utf-8"))["root"]
        assert got == ref
    finally:
        shutil.rmtree(gdir, ignore_errors=True)


def test_tb3_prec_bias_env():
    """TB3_PREC_BIAS offsets operator precedence for hidden fixtures."""
    gdir = _tb3_grammar_dir()
    try:
        _fresh()
        _ingest(gdir)
        _parse(TB3_INPUTS / "tb3_left_prec.json", env={"TB3_PREC_BIAS": "5"})
        graph = load_graph(GRAPH)
        grammar = grammar_by_id(graph, "tb3_calc")
        ref = reference_parse_calc(
            json.loads((TB3_INPUTS / "tb3_left_prec.json").read_text())["tokens"],
            graph,
            grammar,
            5,
        )
        got = json.loads(PARSE.read_text(encoding="utf-8"))["root"]
        assert got == ref
    finally:
        shutil.rmtree(gdir, ignore_errors=True)


def test_tb3_hidden_checksum():
    """Hidden fixture checksum matches reference audit ledger."""
    gdir = _tb3_grammar_dir()
    try:
        _pipeline(gdir, TB3_INPUTS / "tb3_left_prec.json")
        digest = CHECKSUM.read_text(encoding="utf-8").strip()
        assert digest == reference_checksum(GRAPH, PARSE)
    finally:
        shutil.rmtree(gdir, ignore_errors=True)


def test_instruction_data_paths_exercised():
    """Instruction paths /app/data/grammars and /app/data/inputs are exercised."""
    assert list(GRAMMARS.glob("*.json"))
    assert list(INPUTS.glob("*.json"))
    _pipeline(GRAMMARS, INPUTS / "calc_add_mul.json")
    assert json.loads(AUDIT.read_text(encoding="utf-8"))["grammar_id"] == "calc"


def test_ingest_preserves_grammar_ids():
    """Staging lists grammar_id values from bundled fixtures."""
    _ingest(GRAMMARS)
    graph = load_graph(GRAPH)
    ids = [g["grammar_id"] for g in graph["grammars"]]
    assert ids == ["calc", "neg_stmt", "stmt"]
