"""Behavioral tests for celctl policy trace evaluator."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest

from reference_cel import reference_eval

STAGING_PATH = "/app/state/cel-staging.json"
TRACE_PATH = "/app/output/trace.json"
APP = Path("/app")
STAGING = Path(STAGING_PATH)
TRACE_OUT = Path(TRACE_PATH)
RESULT_OUT = APP / "output" / "result.json"
TB3_ROOT = Path("/opt/verifier-fixtures")


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=True, capture_output=True, text=True)


def _ingest(expr_path: Path, staging: Path = STAGING) -> None:
    staging.parent.mkdir(parents=True, exist_ok=True)
    _run(
        [
            "celctl",
            "ingest",
            "--input",
            str(expr_path),
            "--staging",
            str(staging),
        ]
    )


def _eval_trace(
    staging: Path,
    env_path: Path,
    trace_out: Path = TRACE_OUT,
    result_out: Path = RESULT_OUT,
) -> dict:
    trace_out.parent.mkdir(parents=True, exist_ok=True)
    result_out.parent.mkdir(parents=True, exist_ok=True)
    _run(
        [
            "celctl",
            "eval",
            "--staging",
            str(staging),
            "--env",
            str(env_path),
            "--trace",
            "--trace-out",
            str(trace_out),
            "--result-out",
            str(result_out),
        ]
    )
    return json.loads(trace_out.read_text(encoding="utf-8"))


def _load_root(expr_path: Path) -> dict:
    return json.loads(expr_path.read_text(encoding="utf-8"))["root"]


@pytest.fixture(autouse=True)
def _clean_outputs(tmp_path_factory: pytest.TempPathFactory) -> None:
    for p in (STAGING, TRACE_OUT, RESULT_OUT):
        if p.exists():
            p.unlink()
    yield


def test_staging_output_path_contract() -> None:
    """Instruction staging path /app/state/cel-staging.json is written by ingest."""
    expr = APP / "fixtures" / "literal_true.json"
    _ingest(expr)
    assert str(STAGING) == STAGING_PATH
    assert STAGING.is_file()


def test_trace_output_path_contract() -> None:
    """Instruction trace path /app/output/trace.json is written in trace mode."""
    expr = APP / "fixtures" / "literal_true.json"
    _ingest(expr)
    _eval_trace(STAGING, APP / "fixtures" / "env_empty.json")
    assert str(TRACE_OUT) == TRACE_PATH
    assert TRACE_OUT.is_file()


def test_ingest_writes_staging_snapshot() -> None:
    """Ingest must materialize staging JSON on disk."""
    expr = APP / "fixtures" / "literal_true.json"
    _ingest(expr)
    assert STAGING.is_file()
    data = json.loads(STAGING.read_text(encoding="utf-8"))
    assert data["version"] == 1
    assert data["source"] == str(expr)
    assert "ast_hash" in data
    assert data["normalized"]["type"] == "literal"


def test_staging_schema_hash_stable() -> None:
    """Re-ingest of the same AST yields identical ast_hash."""
    expr = APP / "fixtures" / "literal_true.json"
    _ingest(expr)
    first = json.loads(STAGING.read_text(encoding="utf-8"))["ast_hash"]
    _ingest(expr)
    second = json.loads(STAGING.read_text(encoding="utf-8"))["ast_hash"]
    assert first == second
    canon = json.dumps(
        json.loads(expr.read_text(encoding="utf-8"))["root"],
        separators=(",", ":"),
    ).encode()
    assert first == hashlib.sha256(canon).hexdigest()


def test_eval_literal_subprocess() -> None:
    """Simple literal evaluates to true via subprocess CLI."""
    expr = APP / "fixtures" / "literal_true.json"
    env = APP / "fixtures" / "env_empty.json"
    _ingest(expr)
    trace = _eval_trace(STAGING, env)
    assert trace["result"] is True


def test_reference_matches_literal() -> None:
    """Reference interpreter agrees on literal fixture."""
    expr = APP / "fixtures" / "literal_true.json"
    root = _load_root(expr)
    env = json.loads((APP / "fixtures" / "env_empty.json").read_text(encoding="utf-8"))
    result, _, _ = reference_eval(root, env)
    _ingest(expr)
    trace = _eval_trace(STAGING, APP / "fixtures" / "env_empty.json")
    assert trace["result"] == result


def test_short_circuit_and_skips_has_side_effect() -> None:
    """False LHS must prevent has() side effects on RHS."""
    expr = APP / "fixtures" / "short_circuit_and.json"
    env = APP / "fixtures" / "env_short.json"
    _ingest(expr)
    trace = _eval_trace(STAGING, env)
    assert trace["result"] is False
    assert trace["has_call_count"] == 0


def test_short_circuit_reference_agrees() -> None:
    """Reference confirms zero has() calls when AND short-circuits."""
    expr = APP / "fixtures" / "short_circuit_and.json"
    root = _load_root(expr)
    env = json.loads((APP / "fixtures" / "env_short.json").read_text(encoding="utf-8"))
    result, branches, has_count = reference_eval(root, env)
    assert result is False
    assert has_count == 0
    _ingest(expr)
    trace = _eval_trace(STAGING, APP / "fixtures" / "env_short.json")
    assert trace["has_call_count"] == has_count
    assert trace["result"] == result


def test_trace_omits_pruned_and_right_branch() -> None:
    """Trace must not list RHS paths when AND short-circuits."""
    expr = APP / "fixtures" / "short_circuit_and.json"
    _ingest(expr)
    trace = _eval_trace(STAGING, APP / "fixtures" / "env_short.json")
    paths = [b.get("path", "") for b in trace["branches"]]
    assert not any("right" in p for p in paths)


def test_duration_compare_canonical_nanoseconds() -> None:
    """500ms must be less than 600000000 ns after canonicalization."""
    expr = APP / "fixtures" / "duration_compare.json"
    _ingest(expr)
    trace = _eval_trace(STAGING, APP / "fixtures" / "env_empty.json")
    assert trace["result"] is True


def test_duration_reference_agrees() -> None:
    """Reference duration ordering matches celctl."""
    expr = APP / "fixtures" / "duration_compare.json"
    root = _load_root(expr)
    env: dict = {}
    expected, _, _ = reference_eval(root, env)
    _ingest(expr)
    trace = _eval_trace(STAGING, APP / "fixtures" / "env_empty.json")
    assert trace["result"] == expected


def test_map_comprehension_last_key_wins() -> None:
    """Duplicate keys keep the last generated value."""
    expr = APP / "fixtures" / "map_collision.json"
    _ingest(expr)
    trace = _eval_trace(STAGING, APP / "fixtures" / "env_map.json")
    assert trace["result"] == {"k": 3}


def test_map_reference_agrees() -> None:
    """Reference map comprehension merge matches celctl."""
    expr = APP / "fixtures" / "map_collision.json"
    root = _load_root(expr)
    env = json.loads((APP / "fixtures" / "env_map.json").read_text(encoding="utf-8"))
    expected, _, _ = reference_eval(root, env)
    _ingest(expr)
    trace = _eval_trace(STAGING, APP / "fixtures" / "env_map.json")
    assert trace["result"] == expected


def test_nested_bind_outer_visible_after_inner() -> None:
    """Inner bind must not pop outer frame early; outer x stays 1."""
    expr = APP / "fixtures" / "nested_bind.json"
    _ingest(expr)
    trace = _eval_trace(STAGING, APP / "fixtures" / "env_empty.json")
    assert trace["result"] == 1


def test_nested_bind_reference_agrees() -> None:
    """Reference bind scoping matches nested fixture."""
    expr = APP / "fixtures" / "nested_bind.json"
    root = _load_root(expr)
    env: dict = {}
    expected, _, _ = reference_eval(root, env)
    _ingest(expr)
    trace = _eval_trace(STAGING, APP / "fixtures" / "env_empty.json")
    assert trace["result"] == expected


def test_eval_requires_staging_file() -> None:
    """Eval must read staging snapshot rather than raw input."""
    missing = APP / "state" / "missing-staging.json"
    if missing.exists():
        missing.unlink()
    with pytest.raises(subprocess.CalledProcessError):
        _run(
            [
                "celctl",
                "eval",
                "--staging",
                str(missing),
                "--env",
                str(APP / "fixtures" / "env_empty.json"),
                "--trace",
            ]
        )


def test_cross_run_staging_idempotent_reingest() -> None:
    """Second ingest leaves normalized AST identical (persistence contract)."""
    expr = APP / "fixtures" / "map_collision.json"
    _ingest(expr)
    first = json.loads(STAGING.read_text(encoding="utf-8"))["normalized"]
    _ingest(expr)
    second = json.loads(STAGING.read_text(encoding="utf-8"))["normalized"]
    assert first == second


def test_trace_branch_count_matches_reference() -> None:
    """Evaluated branch records align with reference walk."""
    expr = APP / "fixtures" / "duration_compare.json"
    root = _load_root(expr)
    _, ref_branches, _ = reference_eval(root, {})
    _ingest(expr)
    trace = _eval_trace(STAGING, APP / "fixtures" / "env_empty.json")
    assert len(trace["branches"]) == len(ref_branches)


def test_tb3_hidden_nested_bind_short_circuit() -> None:
    """Hidden fixture: nested bind plus AND short-circuit must skip has()."""
    expr = TB3_ROOT / "tb3_nested_bind.json"
    env = TB3_ROOT / "tb3_env.json"
    _ingest(expr)
    trace = _eval_trace(STAGING, env)
    root = _load_root(expr)
    ref_env = json.loads(env.read_text(encoding="utf-8"))
    expected, _, has_count = reference_eval(root, ref_env)
    assert trace["result"] == expected
    assert trace["has_call_count"] == has_count == 0


def test_tb3_hidden_trace_no_pruned_paths() -> None:
    """Hidden fixture trace must omit pruned RHS under nested bind."""
    expr = TB3_ROOT / "tb3_nested_bind.json"
    env = TB3_ROOT / "tb3_env.json"
    _ingest(expr)
    trace = _eval_trace(STAGING, env)
    paths = [b.get("path", "") for b in trace["branches"]]
    assert not any("right" in p for p in paths)


def test_export_trace_subprocess_writes_output() -> None:
    """Trace mode writes /app/output/trace.json with required fields."""
    expr = APP / "fixtures" / "literal_true.json"
    _ingest(expr)
    _eval_trace(STAGING, APP / "fixtures" / "env_empty.json")
    data = json.loads(TRACE_OUT.read_text(encoding="utf-8"))
    assert "result" in data
    assert "branches" in data
    assert "has_call_count" in data


def test_decoy_module_not_used_in_export() -> None:
    """Export path must not invoke decoy WrapTrace (smoke: eval still succeeds)."""
    expr = APP / "fixtures" / "literal_true.json"
    _ingest(expr)
    trace = _eval_trace(STAGING, APP / "fixtures" / "env_empty.json")
    branches = trace.get("branches") or []
    assert all(b.get("op") != "decoy" for b in branches)


def test_or_short_circuit_skips_rhs() -> None:
    """True LHS on OR must skip RHS has() side effect."""
    or_expr = {
        "root": {
            "type": "binary",
            "op": "or",
            "left": {"type": "literal", "kind": "bool", "value": True},
            "right": {
                "type": "call",
                "fn": "has",
                "args": [{"type": "ident", "name": "probe_slot"}],
            },
        }
    }
    path = APP / "output" / "or_short.json"
    path.write_text(json.dumps(or_expr), encoding="utf-8")
    _ingest(path)
    trace = _eval_trace(STAGING, APP / "fixtures" / "env_short.json")
    assert trace["result"] is True
    assert trace["has_call_count"] == 0
