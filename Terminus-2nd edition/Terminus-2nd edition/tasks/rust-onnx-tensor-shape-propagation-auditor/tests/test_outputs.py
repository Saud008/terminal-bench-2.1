"""Shape constraint verifier suite for tensor graph propagation."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest
from shape_batch_runner import (
    ENV_ROOT,
    LEDGER_PATH,
    REPORT_PATH,
    SHAPEPROP_BIN,
    cli_help_tokens,
    compile_shapeprop,
    read_diagnostic_report,
    read_ledger_rows,
    resolve_graph_batch,
    run_batch_and_emit,
    run_shapeprop_help,
)

ROOT = Path("/app")
HIDDEN_BATCH = Path("/opt/verifier-fixtures/tg_hidden/graphs")


def _sym_table(links: list[list[str]]) -> dict[str, str]:
    parent: dict[str, str] = {}

    def find(x: str) -> str:
        while x in parent and parent[x] != x:
            parent[x] = parent.get(parent[x], parent[x])
            x = parent[x]
        return x

    def unite(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for pair in links:
        if len(pair) == 2:
            unite(pair[0], pair[1])
    return {k: find(k) for k in set(sum(links, [])) if links}


def _sym_resolve(sym: str, table: dict[str, str]) -> str:
    return table.get(sym, sym)


def _materialize_shape(shape: list[Any], table: dict[str, str]) -> list[Any]:
    out = []
    for d in shape:
        if isinstance(d, int):
            out.append(d)
        else:
            out.append(_sym_resolve(str(d), table))
    return out


def _apply_defaults(port: dict) -> list[Any]:
    base = list(port.get("shape", []))
    defaults = port.get("default_shape")
    if not defaults:
        return base
    out = []
    for i, cur in enumerate(base):
        if isinstance(cur, int) and cur == -1:
            out.append(defaults[i] if i < len(defaults) else cur)
        else:
            out.append(cur)
    while len(out) < len(defaults):
        out.append(defaults[len(out)])
    return out


def _broadcast(a: list[Any], b: list[Any], table: dict[str, str]) -> list[Any] | None:
    ma = _materialize_shape(a, table)
    mb = _materialize_shape(b, table)
    rank = max(len(ma), len(mb))
    la = [1] * (rank - len(ma)) + ma
    rb = [1] * (rank - len(mb)) + mb
    out = []
    for x, y in zip(la, rb):
        if x == 1:
            out.append(y)
        elif y == 1:
            out.append(x)
        elif x == y:
            out.append(x)
        else:
            return None
    return out


def _matmul(a: list[Any], b: list[Any], table: dict[str, str]) -> list[Any] | None:
    ma = _materialize_shape(a, table)
    mb = _materialize_shape(b, table)
    if len(ma) < 2 or len(mb) < 2:
        return None
    batch_rank = max(len(ma), len(mb)) - 2
    ba = [1] * (batch_rank - (len(ma) - 2)) + ma[:-2]
    bb = [1] * (batch_rank - (len(mb) - 2)) + mb[:-2]
    batch = _broadcast(ba, bb, table)
    if batch is None:
        return None
    if ma[-1] != mb[-2] and not (isinstance(ma[-1], str) and ma[-1] == mb[-2]):
        if not (isinstance(ma[-1], int) and isinstance(mb[-2], int) and ma[-1] == mb[-2]):
            return None
    return batch + [ma[-2], mb[-1]]


def _reshape(in_shape: list[Any], target: list[int], table: dict[str, str]) -> list[Any] | None:
    ms = _materialize_shape(in_shape, table)
    total = 1
    for d in ms:
        total *= int(d) if isinstance(d, int) else 1
    known = 1
    out: list[Any] = []
    unknown = None
    for i, t in enumerate(target):
        if t == -1:
            unknown = i
            out.append(-1)
        else:
            known *= t
            out.append(t)
    if unknown is not None:
        out[unknown] = total // known
    return out


def _transpose(in_shape: list[Any], perm: list[int], table: dict[str, str]) -> list[Any]:
    ms = _materialize_shape(in_shape, table)
    return [ms[i] for i in perm]


def _concat(shapes: list[list[Any]], axis: int, table: dict[str, str]) -> list[Any] | None:
    if not shapes:
        return None
    base = _materialize_shape(shapes[0], table)
    out = list(base)
    for sh in shapes[1:]:
        cur = _materialize_shape(sh, table)
        if len(cur) != len(out):
            return None
        for i, (a, b) in enumerate(zip(out, cur)):
            if i == axis:
                if isinstance(a, int) and isinstance(b, int):
                    out[i] = a + b
                elif a == b:
                    out[i] = a
                else:
                    return None
            elif a != b:
                return None
    return out


def _infer_node(node: dict, env: dict[str, list[Any]], table: dict[str, str]) -> list[Any] | None:
    op = node["op"]
    if op == "MatMul":
        return _matmul(env[node["inputs"][0]], env[node["inputs"][1]], table)
    if op in ("Add", "Mul"):
        return _broadcast(env[node["inputs"][0]], env[node["inputs"][1]], table)
    if op == "Reshape":
        target = node.get("attrs", {}).get("target", [])
        return _reshape(env[node["inputs"][0]], target, table)
    if op == "Transpose":
        perm = node.get("attrs", {}).get("perm", [])
        return _transpose(env[node["inputs"][0]], perm, table)
    if op == "Concat":
        axis = int(node.get("attrs", {}).get("axis", 0))
        shapes = [env[n] for n in node["inputs"]]
        return _concat(shapes, axis, table)
    return None


def _propagate_doc(doc: dict) -> list[dict]:
    table = _sym_table(doc.get("symbol_links", []))
    env: dict[str, list[Any]] = {}
    rows = []
    ordinal = 0
    for inp in doc.get("inputs", []):
        shape = _apply_defaults(inp)
        env[inp["name"]] = shape
        rows.append(
            {
                "graph_id": doc["graph_id"],
                "tensor": inp["name"],
                "shape": shape,
                "node_id": "input",
                "ordinal": ordinal,
            }
        )
        ordinal += 1
    for init in doc.get("initializers", []):
        shape = list(init.get("shape", []))
        env[init["name"]] = shape
        rows.append(
            {
                "graph_id": doc["graph_id"],
                "tensor": init["name"],
                "shape": shape,
                "node_id": "initializer",
                "ordinal": ordinal,
            }
        )
        ordinal += 1
    for node in doc.get("nodes", []):
        out_shape = _infer_node(node, env, table)
        if out_shape is None:
            continue
        for out_name in node.get("outputs", []):
            env[out_name] = out_shape
            rows.append(
                {
                    "graph_id": doc["graph_id"],
                    "tensor": out_name,
                    "shape": out_shape,
                    "node_id": node["id"],
                    "ordinal": ordinal,
                }
            )
            ordinal += 1
    return rows


def _load_graphs(graph_dir: Path) -> list[dict]:
    docs = []
    for path in sorted(graph_dir.glob("*.json")):
        docs.append(json.loads(path.read_text(encoding="utf-8")))
    return docs


def reference_staging(graph_dir: Path) -> list[dict]:
    rows: list[dict] = []
    for doc in _load_graphs(graph_dir):
        rows.extend(_propagate_doc(doc))
    return rows


def reference_audit_report(graph_dir: Path, staging: list[dict]) -> list[dict]:
    expected: dict[tuple[str, str], list[Any]] = {}
    for doc in _load_graphs(graph_dir):
        for row in _propagate_doc(doc):
            expected[(row["graph_id"], row["tensor"])] = row["shape"]
    by_graph: dict[str, list[dict]] = {}
    for row in staging:
        by_graph.setdefault(row["graph_id"], []).append(row)
    reports = []
    for doc in _load_graphs(graph_dir):
        gid = doc["graph_id"]
        violations = []
        for row in by_graph.get(gid, []):
            key = (gid, row["tensor"])
            exp = expected.get(key)
            if exp is None or exp != row["shape"]:
                op = "Input"
                for node in doc.get("nodes", []):
                    if node["id"] == row["node_id"]:
                        op = node["op"]
                        break
                violations.append(
                    {
                        "node_id": row["node_id"],
                        "op": op,
                        "tensor": row["tensor"],
                        "code": "SHAPE_MISMATCH",
                        "message": "propagated shape differs from contract",
                    }
                )
        violations.sort(key=lambda v: (v["node_id"], v["code"], v["tensor"]))
        rows_g = by_graph.get(gid, [])
        reports.append(
            {
                "graph_id": gid,
                "violations": violations,
                "totals": {
                    "violation_count": len(violations),
                    "tensor_count": len(rows_g),
                },
            }
        )
    return reports


def expected_ledger_rows(graph_dir: Path) -> list[dict]:
    return reference_staging(graph_dir)


def expected_diagnostic_report(graph_dir: Path, ledger: list[dict]) -> list[dict]:
    return reference_audit_report(graph_dir, ledger)


@pytest.fixture(scope="module")
def compiled_once() -> None:
    compile_shapeprop()
    assert SHAPEPROP_BIN.is_file()


@pytest.fixture
def bundled_run(compiled_once: None) -> tuple[list[dict], list[dict]]:
    run_batch_and_emit()
    return read_ledger_rows(), read_diagnostic_report()


class TestCompileGate:
    def test_shapeprop_binary_exists_after_build(self, compiled_once: None) -> None:
        """Release build must install the shapeprop binary under /app/environment/tools."""
        assert SHAPEPROP_BIN.is_file()


class TestLedgerContract:
    def test_ledger_output_path_matches_instruction(self, bundled_run: tuple) -> None:
        """Ledger must materialize at the instruction ledger path under /app/state."""
        assert LEDGER_PATH.is_file()

    def test_report_output_path_matches_instruction(self, bundled_run: tuple) -> None:
        """Diagnostic report must materialize at the instruction report path under /app/output."""
        assert REPORT_PATH.is_file()

    def test_ingest_batch_materializes_ledger_file(self, bundled_run: tuple) -> None:
        """Ingest stage must write the JSONL ledger before export runs."""
        assert LEDGER_PATH.is_file()
        assert LEDGER_PATH.stat().st_size > 0

    def test_export_diagnostic_after_ingest(self, bundled_run: tuple) -> None:
        """Export stage reads staged rows and writes diagnostic JSON."""
        assert REPORT_PATH.is_file()
        _, report = bundled_run
        assert isinstance(report, list)

    def test_ledger_ordinals_monotonic_per_graph(self, bundled_run: tuple) -> None:
        """Ledger ordinals must increase monotonically within each graph_id."""
        ledger, _ = bundled_run
        by_graph: dict[str, list[int]] = {}
        for row in ledger:
            by_graph.setdefault(row["graph_id"], []).append(row["ordinal"])
        for ordinals in by_graph.values():
            assert ordinals == sorted(ordinals)

    @pytest.mark.parametrize(
        "graph_id,tensor,expected_tail",
        [
            ("linear_matmul", "Z", 64),
            ("broadcast_bias", "C", 3),
        ],
    )
    def test_bundled_tensor_shape_facts(
        self, bundled_run: tuple, graph_id: str, tensor: str, expected_tail: int
    ) -> None:
        """Bundled graphs must expose expected tensor tail dimensions in the ledger."""
        ledger, _ = bundled_run
        row = next(r for r in ledger if r["graph_id"] == graph_id and r["tensor"] == tensor)
        if isinstance(expected_tail, int) and expected_tail < 10:
            assert len(row["shape"]) == expected_tail
        else:
            assert row["shape"][-1] == expected_tail

    def test_reshape_chain_flatten_dims(self, bundled_run: tuple) -> None:
        """Reshape chain graph must flatten to the gold reference rank."""
        ledger, _ = bundled_run
        flat = next(r for r in ledger if r["graph_id"] == "reshape_chain" and r["tensor"] == "Flat")
        gold = next(
            r
            for r in expected_ledger_rows(resolve_graph_batch())
            if r["graph_id"] == "reshape_chain" and r["tensor"] == "Flat"
        )
        assert flat["shape"] == gold["shape"]


class TestDiagnosticExport:
    def test_report_is_array_per_graph_file(self, bundled_run: tuple) -> None:
        """Diagnostic export must return one report object per bundled graph."""
        _, report = bundled_run
        assert isinstance(report, list)
        assert len(report) >= 3

    def test_violation_totals_match_array_lengths(self, bundled_run: tuple) -> None:
        """Totals.violation_count must equal the violations array length."""
        _, report = bundled_run
        for block in report:
            assert block["totals"]["violation_count"] == len(block["violations"])

    def test_violation_rows_stable_sort(self, bundled_run: tuple) -> None:
        """Violations must sort stably by node_id, code, then tensor."""
        _, report = bundled_run
        for block in report:
            keys = [(v["node_id"], v["code"], v["tensor"]) for v in block["violations"]]
            assert keys == sorted(keys)

    def test_clean_graphs_emit_zero_violations(self, bundled_run: tuple) -> None:
        """Bundled clean graphs must emit empty violation arrays."""
        _, report = bundled_run
        for block in report:
            assert block["violations"] == []

    def test_tensor_totals_align_with_ledger(self, bundled_run: tuple) -> None:
        """Report tensor_count must match ledger row count per graph_id."""
        ledger, report = bundled_run
        for block in report:
            count = sum(1 for row in ledger if row["graph_id"] == block["graph_id"])
            assert block["totals"]["tensor_count"] == count

    def test_repeat_emit_is_byte_stable(self, compiled_once: None) -> None:
        """Repeated emit-violations runs must produce byte-identical JSON."""
        run_batch_and_emit()
        first = REPORT_PATH.read_text(encoding="utf-8")
        run_batch_and_emit()
        second = REPORT_PATH.read_text(encoding="utf-8")
        assert first == second


class TestReferenceParity:
    def test_ledger_matches_gold_propagation(self, bundled_run: tuple) -> None:
        """Ledger rows must match the independent gold propagation reference."""
        ledger, _ = bundled_run
        gold = expected_ledger_rows(resolve_graph_batch())
        assert len(ledger) == len(gold)
        for got, exp in zip(ledger, gold):
            assert got["graph_id"] == exp["graph_id"]
            assert got["tensor"] == exp["tensor"]
            assert got["shape"] == exp["shape"]
            assert got["ordinal"] == exp["ordinal"]

    def test_report_matches_gold_audit(self, bundled_run: tuple) -> None:
        """Diagnostic report must match the independent gold audit reference."""
        _, report = bundled_run
        batch = resolve_graph_batch()
        gold = expected_diagnostic_report(batch, expected_ledger_rows(batch))
        assert report == gold


class TestHiddenGraphBatch:
    @pytest.mark.skipif(not HIDDEN_BATCH.is_dir(), reason="hidden graph fixtures absent")
    def test_tb3_override_ledger_parity(self, compiled_once: None, monkeypatch: pytest.MonkeyPatch) -> None:
        """TB3 graph dir override must drive hidden-batch ledger parity."""
        monkeypatch.setenv("TB3_GRAPH_DIR", str(HIDDEN_BATCH))
        run_batch_and_emit(HIDDEN_BATCH)
        assert read_ledger_rows() == expected_ledger_rows(HIDDEN_BATCH)

    @pytest.mark.skipif(not HIDDEN_BATCH.is_dir(), reason="hidden graph fixtures absent")
    def test_dynamic_concat_axis_zero(self, compiled_once: None) -> None:
        """Hidden dynamic_concat graph must match gold axis-zero symbol behavior."""
        os.environ["TB3_GRAPH_DIR"] = str(HIDDEN_BATCH)
        run_batch_and_emit(HIDDEN_BATCH)
        merged = next(r for r in read_ledger_rows() if r["graph_id"] == "dynamic_concat" and r["tensor"] == "Merged")
        gold = next(
            r
            for r in expected_ledger_rows(HIDDEN_BATCH)
            if r["graph_id"] == "dynamic_concat" and r["tensor"] == "Merged"
        )
        assert merged["shape"] == gold["shape"]

    @pytest.mark.skipif(not HIDDEN_BATCH.is_dir(), reason="hidden graph fixtures absent")
    def test_init_override_default_before_matmul(self, compiled_once: None) -> None:
        """Initializer override must apply default_shape before MatMul inference."""
        os.environ["TB3_GRAPH_DIR"] = str(HIDDEN_BATCH)
        run_batch_and_emit(HIDDEN_BATCH)
        y_row = next(r for r in read_ledger_rows() if r["graph_id"] == "init_override" and r["tensor"] == "Y")
        assert y_row["shape"] == [4, 32]


class TestSubprocessHarness:
    def test_shapeprop_cli_help_via_subprocess(self, compiled_once: None) -> None:
        """shapeprop --help must list documented CLI subcommands."""
        proc = run_shapeprop_help()
        missing = [tok for tok in cli_help_tokens() if tok not in proc.stdout]
        assert not missing

    def test_build_script_invokes_cargo_release(self, compiled_once: None) -> None:
        """build_all.sh must rebuild and install the release binary."""
        import subprocess

        proc = subprocess.run(
            ["bash", str(ENV_ROOT / "scripts" / "build_all.sh")],
            check=True,
            capture_output=True,
            text=True,
        )
        assert SHAPEPROP_BIN.is_file()
        assert proc.returncode == 0

    def test_entrypoint_subprocess_smoke(self, compiled_once: None) -> None:
        """Ensure the graded binary responds via subprocess from the entry module."""
        proc = run_shapeprop_help()
        assert "batch-propagate" in proc.stdout
        assert "emit-violations" in proc.stdout
