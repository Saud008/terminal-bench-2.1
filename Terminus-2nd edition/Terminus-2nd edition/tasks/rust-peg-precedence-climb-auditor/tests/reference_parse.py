"""Independent reference for pestctl climb parse and span audit."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any


def load_graph(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def grammar_by_id(graph: dict[str, Any], grammar_id: str) -> dict[str, Any]:
    for g in graph["grammars"]:
        if g["grammar_id"] == grammar_id:
            return g
    raise KeyError(grammar_id)


def reference_climb_table(graph: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for g in graph["grammars"]:
        for rule in g["rules"]:
            rows.append(
                {
                    "rule": f"{g['grammar_id']}::{rule['name']}",
                    "prec": rule["prec"],
                    "rank": rule["decl_order"],
                    "left_recursive": rule["left_recursive"],
                }
            )
    rows.sort(key=lambda r: (-r["prec"], r["rule"]))
    for idx, row in enumerate(rows):
        row["rank"] = idx
    return rows


def _binary_op(pattern: dict[str, Any]) -> str | None:
    if pattern.get("type") == "choice":
        for alt in pattern.get("alts", []):
            op = _binary_op(alt)
            if op:
                return op
    if pattern.get("type") == "seq":
        items = pattern.get("items", [])
        if len(items) == 3:
            mid = items[1]
            if mid.get("type") == "pattern":
                val = mid.get("value", {})
                if val.get("type") == "token":
                    return val.get("lit")
    return None


def _op_prec(token: str, graph: dict[str, Any], grammar: dict[str, Any], bias: int = 0) -> int | None:
    for rule in grammar["rules"]:
        op = _binary_op(rule["rhs"])
        if op == token:
            key = f"{grammar['grammar_id']}::{rule['name']}"
            for row in graph["climb_table"]:
                if row["rule"] == key:
                    return int(row["prec"]) + bias
            return int(rule["prec"]) + bias
    return None


def _node(kind: str, span: list[int], value: str | None = None, children: list | None = None) -> dict:
    return {
        "kind": kind,
        "value": value,
        "span": span,
        "recovered": False,
        "children": children or [],
    }


def reference_parse_calc(tokens: list[str], graph: dict[str, Any], grammar: dict[str, Any], bias: int = 0) -> dict:
    toks = [t for t in tokens if t != "WS"]

    def parse_primary(pos: int) -> tuple[dict, int]:
        if pos >= len(toks):
            raise ValueError("eof")
        if toks[pos].startswith("NUM:"):
            val = toks[pos].split(":", 1)[1]
            return _node("number", [pos, pos + 1], val), pos + 1
        raise ValueError(f"bad primary {pos}")

    def parse_expr(pos: int, min_prec: int) -> tuple[dict, int]:
        left, pos = parse_primary(pos)
        while pos < len(toks):
            prec = _op_prec(toks[pos], graph, grammar, bias)
            if prec is None or prec < min_prec:
                break
            op = toks[pos]
            pos += 1
            right, pos = parse_expr(pos, prec + 1)
            left = _node("binary", [left["span"][0], right["span"][1]], op, [left, right])
        return left, pos

    root, end = parse_expr(0, 0)
    if end != len(toks):
        raise ValueError("trailing tokens")
    return root


def _skip_ws(tokens: list[str], pos: int) -> int:
    while pos < len(tokens) and tokens[pos] == "WS":
        pos += 1
    return pos


def reference_parse_sequence(tokens: list[str], grammar: dict[str, Any]) -> dict:
    toks = list(tokens)
    start = grammar["rules"][0]
    items = start["rhs"]["items"]
    pos = 0
    children: list[dict] = []
    start_pos = 0
    for item in items:
        pos = _skip_ws(toks, pos)
        if item["type"] == "pattern":
            pat = item["value"]
            if pat["type"] == "token" and pat["lit"] == "NUMBER":
                if pos >= len(toks) or not toks[pos].startswith("NUM:"):
                    raise ValueError("expected number")
                val = toks[pos].split(":", 1)[1]
                children.append(_node("number", [pos, pos + 1], val))
                pos += 1
            elif pat["type"] == "token":
                lit = pat["lit"]
                if pos >= len(toks) or toks[pos] != lit:
                    raise ValueError(f"expected {lit}")
                children.append(_node("token", [pos, pos + 1], lit))
                pos += 1
            elif pat["type"] == "neg_pred":
                inner = pat["inner"]
                lit = inner["lit"]
                if pos < len(toks) and toks[pos] == lit:
                    raise ValueError("neg pred matched")
                children.append(_node("neg_pred", [pos, pos], None))
                if pos < len(toks) and not toks[pos].startswith("NUM:"):
                    pos += 1
            else:
                raise ValueError("unsupported")
        elif item["type"] == "terminator":
            lit = item["lit"]
            if pos >= len(toks) or toks[pos] != lit:
                raise ValueError("terminator")
            children.append(_node("terminator", [pos, pos], None))
            pos += 1
    return _node("sequence", [start_pos, pos], None, children)


def flatten_spans(root: dict, recovered: list[dict] | None = None) -> list[dict]:
    rows: list[dict] = []

    def walk(n: dict) -> None:
        rows.append({"kind": n["kind"], "span": n["span"], "recovered": n.get("recovered", False)})
        for c in n.get("children", []):
            walk(c)

    walk(root)
    for n in recovered or []:
        rows.append({"kind": n["kind"], "span": n["span"], "recovered": n.get("recovered", False)})
    rows.sort(key=lambda r: (r["span"][0], r["kind"]))
    return rows


def reference_audit(graph_path: Path, parse_path: Path) -> dict[str, Any]:
    graph = load_graph(graph_path)
    tree = json.loads(parse_path.read_text(encoding="utf-8"))
    spans = flatten_spans(tree["root"], tree.get("recovered_nodes", []))
    return {
        "grammar_id": tree["grammar_id"],
        "ingest_seq": graph["ingest_seq"],
        "spans": spans,
    }


def reference_checksum(graph_path: Path, parse_path: Path) -> str:
    audit = reference_audit(graph_path, parse_path)
    payload = json.dumps(audit, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def tb3_prec_bias() -> int:
    raw = os.environ.get("TB3_PREC_BIAS", "0")
    try:
        return int(raw)
    except ValueError:
        return 0
