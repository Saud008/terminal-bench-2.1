"""Loki LogQL offline pipeline eval and fingerprint export tests."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from copy import deepcopy
from pathlib import Path
from typing import Any

CLI = "/app/bin/lokictl"
STAGE = Path("/app/state/logql-stage.json")
FPRINT = Path("/app/output/query-fingerprint.json")


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _parse_selector(part: str) -> dict[str, str]:
    part = part.strip().strip("{}")
    sel: dict[str, str] = {}
    if not part.strip():
        return sel
    for kv in part.split(","):
        key, val = kv.split("=", 1)
        sel[key.strip()] = val.strip().strip('"')
    return sel


def _split_stages(raw: str) -> list[str]:
    parts: list[str] = []
    depth = 0
    start = 0
    for i, ch in enumerate(raw):
        if ch == "{":
            depth += 1
        if ch == "}":
            depth -= 1
        if ch == "|" and depth == 0:
            parts.append(raw[start:i])
            start = i + 1
    parts.append(raw[start:])
    return parts


def _canonicalize(stages: list[dict[str, Any]]) -> str:
    chunks: list[str] = []
    for st in stages:
        kind = st["kind"]
        if kind == "matcher":
            keys = sorted(st["selector"].keys())
            inner = ",".join(f'{k}="{st["selector"][k]}"' for k in keys)
            chunks.append("{" + inner + "}")
        elif kind == "json":
            chunks.append("json")
        elif kind == "line_format":
            chunks.append(f'line_format "{st["template"]}"')
        elif kind == "unwrap":
            chunks.append(f"unwrap {st['field']}")
        elif kind == "sum_by":
            chunks.append("sum by (" + ",".join(st["group_by"]) + ")")
    return " | ".join(chunks)


def parse_query(raw: str) -> dict[str, Any]:
    raw = raw.strip()
    stages: list[dict[str, Any]] = []
    for part in _split_stages(raw):
        part = part.strip()
        if part.startswith("{"):
            stages.append({"kind": "matcher", "selector": _parse_selector(part)})
        elif part == "json":
            stages.append({"kind": "json"})
        elif part.startswith("line_format "):
            tpl = part[len("line_format ") :].strip().strip('"')
            stages.append({"kind": "line_format", "template": tpl})
        elif part.startswith("unwrap "):
            stages.append({"kind": "unwrap", "field": part[len("unwrap ") :].strip()})
        elif part.startswith("sum by"):
            inner = part[len("sum by") :].strip().strip("()")
            group = [g.strip() for g in inner.split(",") if g.strip()] if inner else []
            stages.append({"kind": "sum_by", "group_by": group})
    return {"raw": raw, "canonical": _canonicalize(stages), "stages": stages}


def unescape_field(s: str) -> str:
    out: list[str] = []
    i = 0
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s):
            nxt = s[i + 1]
            if nxt == "n":
                out.append("\n")
                i += 2
                continue
            if nxt == "t":
                out.append("\t")
                i += 2
                continue
            if nxt == "r":
                out.append("\r")
                i += 2
                continue
            if nxt == '"':
                out.append('"')
                i += 2
                continue
            if nxt == "\\":
                out.append("\\")
                i += 2
                continue
        out.append(s[i])
        i += 1
    return "".join(out)


def _fnv1a64(parts: list[bytes]) -> int:
    h = 14695981039346656037
    for chunk in parts:
        for b in chunk:
            h ^= b
            h = (h * 1099511628211) & 0xFFFFFFFFFFFFFFFF
    return h


def _label_checksum_insert(labels: dict[str, str], order: list[str]) -> int:
    chunks: list[bytes] = []
    for k in order:
        if k in labels:
            chunks.append(k.encode())
            chunks.append(b"\0")
            chunks.append(labels[k].encode())
            chunks.append(b"\0")
    return _fnv1a64(chunks)


def _label_checksum_sorted(labels: dict[str, str]) -> int:
    keys = sorted(labels.keys())
    chunks: list[bytes] = []
    for k in keys:
        chunks.append(k.encode())
        chunks.append(b"\0")
        chunks.append(labels[k].encode())
        chunks.append(b"\0")
    return _fnv1a64(chunks)


def reference_eval(lines: list[dict[str, Any]], ast: dict[str, Any]) -> dict[str, Any]:
    insert_order: list[str] = []
    seen: set[str] = set()
    rows: list[dict[str, Any]] = []
    for ln in lines:
        labels = dict(ln["labels"])
        for k in labels:
            if k not in seen:
                seen.add(k)
                insert_order.append(k)
        rows.append({"labels": labels, "fields": {}, "value": 1.0, "filtered": False, "line": ln["line"]})

    group_by: list[str] = []
    for st in ast["stages"]:
        kind = st["kind"]
        if kind == "matcher":
            sel = st["selector"]
            for row in rows:
                if row["filtered"]:
                    continue
                if any(row["labels"].get(k) != v for k, v in sel.items()):
                    row["filtered"] = True
        elif kind == "json":
            for row in rows:
                if row["filtered"]:
                    continue
                obj = json.loads(row["line"])
                row["fields"] = {k: str(v) if not isinstance(v, str) else v for k, v in obj.items()}
        elif kind == "line_format":
            tpl = st["template"]
            for row in rows:
                if row["filtered"]:
                    continue
                norm = {k: unescape_field(v) for k, v in row["fields"].items()}
                formatted = tpl
                for k, v in norm.items():
                    formatted = formatted.replace("{{." + k + "}}", v)
                row["fields"]["line"] = formatted
                row["fields"]["width"] = str(len(formatted))
        elif kind == "unwrap":
            field = st["field"]
            for row in rows:
                if row["filtered"]:
                    continue
                raw = row["fields"].get(field, "0")
                try:
                    row["value"] = float(raw)
                except ValueError:
                    row["value"] = 0.0
                labels = row["labels"]
                if "le" in labels:
                    labels.pop("le", None)
                else:
                    labels.pop(field, None)
        elif kind == "sum_by":
            group_by = st["group_by"]

    buckets: dict[str, dict[str, Any]] = {}
    bucket_order: list[str] = []
    for row in rows:
        if row["filtered"]:
            continue
        glabels: dict[str, str] = {}
        parts: list[str] = []
        label_order: list[str] = []
        if not group_by:
            for k in insert_order:
                if k in row["labels"]:
                    glabels[k] = row["labels"][k]
                    parts.append(f"{k}={row['labels'][k]}")
                    label_order.append(k)
        else:
            for g in group_by:
                glabels[g] = row["labels"][g]
                parts.append(f"{g}={row['labels'][g]}")
            label_order = list(group_by)
        parts_sorted = sorted(parts)
        bkey = "|".join(parts_sorted)
        if bkey not in buckets:
            buckets[bkey] = {"labels": glabels, "value": 0.0, "order": label_order}
            bucket_order.append(bkey)
        buckets[bkey]["value"] += row["value"]

    vectors: list[dict[str, Any]] = []
    for bkey in bucket_order:
        b = buckets[bkey]
        if not group_by:
            cs = _label_checksum_insert(b["labels"], b["order"])
        else:
            cs = _label_checksum_insert(b["labels"], group_by)
        vectors.append({"labels": b["labels"], "value": b["value"], "checksum": cs})
    vectors.sort(key=lambda v: v["checksum"])
    return {
        "query": ast,
        "label_insert_order": insert_order,
        "vectors": vectors,
        "selected_group_labels": group_by,
    }


def reference_fingerprint(stage: dict[str, Any], export_pass: int = 1) -> dict[str, Any]:
    payload = stage["query"]["canonical"] + "|" + ",".join(stage["selected_group_labels"])
    fp = hashlib.sha256(payload.encode()).hexdigest()
    vsum = sum(int(v["checksum"]) for v in stage["vectors"])
    return {
        "fingerprint": fp,
        "selected_labels": stage["selected_group_labels"],
        "vector_checksum": vsum,
        "export_pass": export_pass,
    }


def run_eval(query: Path, lines: Path) -> None:
    if STAGE.exists():
        STAGE.unlink()
    if FPRINT.exists():
        FPRINT.unlink()
    proc = subprocess.run(
        [CLI, "eval", "--query", str(query), "--lines", str(lines)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout


def run_export(export_pass: int = 1) -> None:
    proc = subprocess.run(
        [CLI, "export", "--pass", str(export_pass)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout


def load_stage() -> dict[str, Any]:
    return json.loads(STAGE.read_text(encoding="utf-8"))


def load_fingerprint() -> dict[str, Any]:
    return json.loads(FPRINT.read_text(encoding="utf-8"))


def apply_tb3_label_prefix(lines: list[dict[str, Any]], prefix: str) -> list[dict[str, Any]]:
    out = deepcopy(lines)
    for row in out:
        row["labels"] = {f"{prefix}{k}": v for k, v in row["labels"].items()}
    return out


class TestLokiLogqlPipeline:
    """Offline LogQL pipeline eval and export."""

    def test_eval_writes_stage_snapshot(self) -> None:
        """Eval must write /app/state/logql-stage.json."""
        run_eval(Path("/app/data/matcher_gate.query"), Path("/app/data/matcher_gate.jsonl"))
        assert STAGE.is_file()

    def test_staging_ast_canonical_query(self) -> None:
        """Stage query.canonical must match normalized parse form."""
        raw = Path("/app/data/matcher_gate.query").read_text(encoding="utf-8")
        run_eval(Path("/app/data/matcher_gate.query"), Path("/app/data/matcher_gate.jsonl"))
        stage = load_stage()
        ref = parse_query(raw)
        assert stage["query"]["canonical"] == ref["canonical"]

    def test_matcher_filters_stream_labels_not_json(self) -> None:
        """Matcher must run on stream labels before json field promotion."""
        lines = _load_jsonl(Path("/app/data/matcher_gate.jsonl"))
        ast = parse_query(Path("/app/data/matcher_gate.query").read_text(encoding="utf-8"))
        run_eval(Path("/app/data/matcher_gate.query"), Path("/app/data/matcher_gate.jsonl"))
        stage = load_stage()
        ref = reference_eval(lines, ast)
        assert stage["vectors"] == ref["vectors"]

    def test_matcher_sum_excludes_spoofed_json_service(self) -> None:
        """Json service fields must not bypass stream label matcher."""
        lines = _load_jsonl(Path("/app/data/matcher_gate.jsonl"))
        ast = parse_query(Path("/app/data/matcher_gate.query").read_text(encoding="utf-8"))
        ref = reference_eval(lines, ast)
        assert len(ref["vectors"]) == 1
        assert ref["vectors"][0]["value"] == 2.0

    def test_line_format_unescape_width(self) -> None:
        """line_format must expand escape sequences before width unwrap."""
        lines = _load_jsonl(Path("/app/data/escape_format.jsonl"))
        ast = parse_query(Path("/app/data/escape_format.query").read_text(encoding="utf-8"))
        run_eval(Path("/app/data/escape_format.query"), Path("/app/data/escape_format.jsonl"))
        stage = load_stage()
        ref = reference_eval(lines, ast)
        assert stage["vectors"][0]["value"] == ref["vectors"][0]["value"] == 10.0

    def test_histogram_keeps_sum_count_labels(self) -> None:
        """Histogram unwrap must retain _sum and _count sibling labels."""
        lines = _load_jsonl(Path("/app/data/histogram_unwrap.jsonl"))
        ast = parse_query(Path("/app/data/histogram_unwrap.query").read_text(encoding="utf-8"))
        run_eval(Path("/app/data/histogram_unwrap.query"), Path("/app/data/histogram_unwrap.jsonl"))
        stage = load_stage()
        labels = stage["vectors"][0]["labels"]
        assert "_sum" in labels and "_count" in labels
        assert "le" not in labels

    def test_histogram_unwrap_value(self) -> None:
        """Unwrap must move json value into the vector sample."""
        lines = _load_jsonl(Path("/app/data/histogram_unwrap.jsonl"))
        ast = parse_query(Path("/app/data/histogram_unwrap.query").read_text(encoding="utf-8"))
        run_eval(Path("/app/data/histogram_unwrap.query"), Path("/app/data/histogram_unwrap.jsonl"))
        stage = load_stage()
        ref = reference_eval(lines, ast)
        assert stage["vectors"][0]["value"] == ref["vectors"][0]["value"] == 3.0

    def test_checksum_insert_order_not_sorted(self) -> None:
        """sum by () checksum must use label insertion order not sorted keys."""
        lines = _load_jsonl(Path("/app/data/checksum_insert.jsonl"))
        ast = parse_query(Path("/app/data/checksum_insert.query").read_text(encoding="utf-8"))
        run_eval(Path("/app/data/checksum_insert.query"), Path("/app/data/checksum_insert.jsonl"))
        stage = load_stage()
        ref = reference_eval(lines, ast)
        assert stage["vectors"][0]["checksum"] == ref["vectors"][0]["checksum"]
        assert stage["vectors"][0]["checksum"] != _label_checksum_sorted(stage["vectors"][0]["labels"])

    def test_checksum_vector_total(self) -> None:
        """Grouped sum must aggregate unwrap values across lines."""
        lines = _load_jsonl(Path("/app/data/checksum_insert.jsonl"))
        ast = parse_query(Path("/app/data/checksum_insert.query").read_text(encoding="utf-8"))
        run_eval(Path("/app/data/checksum_insert.query"), Path("/app/data/checksum_insert.jsonl"))
        stage = load_stage()
        ref = reference_eval(lines, ast)
        assert stage["vectors"][0]["value"] == ref["vectors"][0]["value"] == 3.0

    def test_bundled_pipeline_vector_value(self) -> None:
        """Multi-stage bundled query must match independent reference vectors."""
        lines = _load_jsonl(Path("/app/data/bundled_pipeline.jsonl"))
        ast = parse_query(Path("/app/data/bundled_pipeline.query").read_text(encoding="utf-8"))
        run_eval(Path("/app/data/bundled_pipeline.query"), Path("/app/data/bundled_pipeline.jsonl"))
        stage = load_stage()
        ref = reference_eval(lines, ast)
        assert stage["vectors"] == ref["vectors"]

    def test_export_writes_fingerprint(self) -> None:
        """Export must write /app/output/query-fingerprint.json."""
        run_eval(Path("/app/data/matcher_gate.query"), Path("/app/data/matcher_gate.jsonl"))
        run_export()
        assert FPRINT.is_file()

    def test_export_canonical_fingerprint(self) -> None:
        """Fingerprint must hash canonical query not raw query text."""
        lines = _load_jsonl(Path("/app/data/matcher_gate.jsonl"))
        ast = parse_query(Path("/app/data/matcher_gate.query").read_text(encoding="utf-8"))
        run_eval(Path("/app/data/matcher_gate.query"), Path("/app/data/matcher_gate.jsonl"))
        run_export()
        stage = load_stage()
        ref_stage = reference_eval(lines, ast)
        ref_fp = reference_fingerprint(ref_stage)
        fp = load_fingerprint()
        assert fp["fingerprint"] == ref_fp["fingerprint"]

    def test_export_vector_checksum_sum(self) -> None:
        """Export vector_checksum must equal sum of stage vector checksums."""
        run_eval(Path("/app/data/checksum_insert.query"), Path("/app/data/checksum_insert.jsonl"))
        run_export()
        stage = load_stage()
        fp = load_fingerprint()
        assert fp["vector_checksum"] == sum(v["checksum"] for v in stage["vectors"])

    def test_subprocess_cli_rebuild_path(self) -> None:
        """CLI must reject missing eval flags after rebuild."""
        proc = subprocess.run([CLI, "eval"], capture_output=True, text=True, check=False)
        assert proc.returncode != 0

    def test_stage_label_insert_order(self) -> None:
        """Stage must record first-seen label key insertion order."""
        run_eval(Path("/app/data/checksum_insert.query"), Path("/app/data/checksum_insert.jsonl"))
        stage = load_stage()
        assert stage["label_insert_order"][0] == "z"

    def test_eval_idempotent_stage(self) -> None:
        """Repeated eval on same inputs must produce identical stage bytes."""
        q = Path("/app/data/matcher_gate.query")
        l = Path("/app/data/matcher_gate.jsonl")
        run_eval(q, l)
        first = load_stage()
        run_eval(q, l)
        second = load_stage()
        assert first == second

    def test_export_pass_persistence(self) -> None:
        """Export pass flag must persist in fingerprint output."""
        run_eval(Path("/app/data/matcher_gate.query"), Path("/app/data/matcher_gate.jsonl"))
        run_export(2)
        fp = load_fingerprint()
        assert fp["export_pass"] == 2

    def test_tb3_hidden_matcher_prefix(self) -> None:
        """TB3 label prefix hidden trap must match reference vectors."""
        prefix = os.environ.get("TB3_LABEL_PREFIX", "tb3_")
        lines = _load_jsonl(Path("/app/data/matcher_gate.jsonl"))
        mutated = apply_tb3_label_prefix(lines, prefix)
        q = Path("/app/data/matcher_gate.query")
        query_text = q.read_text(encoding="utf-8").replace(
            'service="billing"', f'{prefix}service="billing"'
        )
        tmp_q = Path("/tmp/tb3_matcher.query")
        tmp_l = Path("/tmp/tb3_matcher.jsonl")
        tmp_q.write_text(query_text, encoding="utf-8")
        tmp_l.write_text("\n".join(json.dumps(r) for r in mutated) + "\n", encoding="utf-8")
        ast = parse_query(query_text)
        run_eval(tmp_q, tmp_l)
        stage = load_stage()
        ref = reference_eval(mutated, ast)
        assert stage["vectors"] == ref["vectors"]

    def test_tb3_hidden_multi_stage_chain(self) -> None:
        """TB3 multi-stage hidden query must pass export fingerprint check."""
        prefix = os.environ.get("TB3_LABEL_PREFIX", "tb3_")
        lines = _load_jsonl(Path("/app/data/bundled_pipeline.jsonl"))
        mutated = apply_tb3_label_prefix(lines, prefix)
        query_text = (
            Path("/app/data/bundled_pipeline.query")
            .read_text(encoding="utf-8")
            .replace('service="billing"', f'{prefix}service="billing"')
            .replace("sum by (level)", f"sum by ({prefix}level)")
        )
        tmp_q = Path("/tmp/tb3_bundle.query")
        tmp_l = Path("/tmp/tb3_bundle.jsonl")
        tmp_q.write_text(query_text, encoding="utf-8")
        tmp_l.write_text("\n".join(json.dumps(r) for r in mutated) + "\n", encoding="utf-8")
        ast = parse_query(query_text)
        run_eval(tmp_q, tmp_l)
        run_export()
        stage = load_stage()
        ref = reference_eval(mutated, ast)
        assert stage["vectors"] == ref["vectors"]
        fp = load_fingerprint()
        ref_fp = reference_fingerprint(ref)
        assert fp["fingerprint"] == ref_fp["fingerprint"]

    def test_vector_count_after_sum(self) -> None:
        """sum by (level) must collapse to one vector row for matcher gate."""
        run_eval(Path("/app/data/matcher_gate.query"), Path("/app/data/matcher_gate.jsonl"))
        stage = load_stage()
        assert len(stage["vectors"]) == 1

    def test_selected_group_labels_export(self) -> None:
        """Export selected_labels must mirror stage selected_group_labels."""
        run_eval(Path("/app/data/matcher_gate.query"), Path("/app/data/matcher_gate.jsonl"))
        run_export()
        stage = load_stage()
        fp = load_fingerprint()
        assert fp["selected_labels"] == stage["selected_group_labels"]
