"""Independent reference for JSON Schema ref coverage mapper."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def schema_id_for(path: Path) -> str:
    data = load_json(path)
    if isinstance(data, dict) and "$id" in data:
        uri = str(data["$id"])
        return uri.rsplit("/", 1)[-1].replace(".json", "")
    return path.stem


def build_anchor_index(doc_id: str, node: Any, pointer: str = "") -> dict[str, str]:
    idx: dict[str, str] = {}
    if isinstance(node, dict):
        anchor = node.get("$anchor")
        if isinstance(anchor, str):
            idx[anchor] = f"{doc_id}{pointer}"
        for k, v in node.items():
            if k.startswith("$"):
                continue
            child = f"{pointer}/{k}" if pointer else f"/{k}"
            idx.update(build_anchor_index(doc_id, v, child))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            child = f"{pointer}/{i}"
            idx.update(build_anchor_index(doc_id, v, child))
    return idx


def resolve_pointer(root: Any, pointer: str) -> Any | None:
    if pointer in ("", "#", "#/"):
        return root
    p = pointer.lstrip("#")
    if not p.startswith("/"):
        return None
    cur = root
    for part in p.strip("/").split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        if isinstance(cur, list) and part.isdigit():
            cur = cur[int(part)]
        elif isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return None
    return cur


def resolve_refs(schema_dir: Path) -> list[dict[str, Any]]:
    paths = sorted(schema_dir.glob("*.json"))
    docs: dict[str, tuple[Path, Any]] = {}
    anchors: dict[str, dict[str, str]] = {}
    for p in paths:
        sid = schema_id_for(p)
        root = load_json(p)
        docs[sid] = (p, root)
        anchors[sid] = build_anchor_index(sid, root)
    edges: list[dict[str, Any]] = []

    def walk(doc_id: str, node: Any, pointer: str, root: Any, stack: set[tuple[str, str]]):
        if isinstance(node, dict) and "$ref" in node:
            raw = node["$ref"]
            ref_pointer = "$ref" if not pointer else f"{pointer}/$ref"
            edge = resolve_one(doc_id, ref_pointer, raw, root, docs, anchors, stack)
            edges.append(edge)
        if isinstance(node, dict):
            for k, v in node.items():
                if k.startswith("$"):
                    continue
                child = f"{pointer}/{k}" if pointer else f"/{k}"
                walk(doc_id, v, child, root, stack)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(doc_id, v, f"{pointer}/{i}", root, stack)

    for doc_id, (_p, root) in docs.items():
        walk(doc_id, root, "", root, set())
    edges.sort(key=lambda e: (e["schema_id"], e["ref_pointer"]))
    return edges


def resolve_one(
    doc_id: str,
    ref_pointer: str,
    raw_ref: str,
    root: Any,
    docs: dict[str, tuple[Path, Any]],
    anchors: dict[str, dict[str, str]],
    stack: set[tuple[str, str]],
) -> dict[str, Any]:
    if raw_ref.startswith("http://") or raw_ref.startswith("https://"):
        return {
            "schema_id": doc_id,
            "ref_pointer": ref_pointer,
            "target_id": raw_ref,
            "status": "unresolved",
            "anchor_name": None,
        }
    if raw_ref.startswith("#"):
        frag = raw_ref.lstrip("#")
        if frag in anchors.get(doc_id, {}):
            return {
                "schema_id": doc_id,
                "ref_pointer": ref_pointer,
                "target_id": anchors[doc_id][frag],
                "status": "resolved",
                "anchor_name": frag,
            }
        key = (doc_id, ref_pointer)
        if key in stack:
            return {
                "schema_id": doc_id,
                "ref_pointer": ref_pointer,
                "target_id": f"{doc_id}{raw_ref}",
                "status": "recursive",
                "anchor_name": None,
            }
        stack.add(key)
        ok = resolve_pointer(root, raw_ref) is not None
        stack.discard(key)
        return {
            "schema_id": doc_id,
            "ref_pointer": ref_pointer,
            "target_id": f"{doc_id}{raw_ref}",
            "status": "resolved" if ok else "unresolved",
            "anchor_name": None,
        }
    file_part, frag = (raw_ref.split("#", 1) + [""])[:2]
    frag = f"#{frag}" if frag else ""
    stem = Path(file_part).stem
    if stem in docs:
        _p, target_root = docs[stem]
        if frag:
            anchor_key = frag.lstrip("#")
            if anchor_key in anchors.get(stem, {}):
                return {
                    "schema_id": doc_id,
                    "ref_pointer": ref_pointer,
                    "target_id": anchors[stem][anchor_key],
                    "status": "resolved",
                    "anchor_name": anchor_key,
                }
            if resolve_pointer(target_root, frag) is not None:
                return {
                    "schema_id": doc_id,
                    "ref_pointer": ref_pointer,
                    "target_id": f"{stem}{frag}",
                    "status": "resolved",
                    "anchor_name": None,
                }
        return {
            "schema_id": doc_id,
            "ref_pointer": ref_pointer,
            "target_id": stem,
            "status": "resolved",
            "anchor_name": None,
        }
    return {
        "schema_id": doc_id,
        "ref_pointer": ref_pointer,
        "target_id": file_part,
        "status": "unresolved",
        "anchor_name": None,
    }


def instance_matches(schema: Any, instance: Any) -> bool:
    if not isinstance(schema, dict):
        return True
    if "const" in schema:
        return schema["const"] == instance
    props = schema.get("properties")
    if isinstance(props, dict) and isinstance(instance, dict):
        for key, subschema in props.items():
            if key not in instance:
                continue
            if isinstance(subschema, dict) and "const" in subschema:
                if instance[key] != subschema["const"]:
                    return False
            elif isinstance(subschema, dict) and not instance_matches(subschema, instance[key]):
                return False
        required = schema.get("required")
        if isinstance(required, list):
            for key in required:
                if key not in instance:
                    return False
    t = schema.get("type")
    if t == "object":
        return isinstance(instance, dict)
    if t == "array":
        return isinstance(instance, list)
    if t == "string":
        return isinstance(instance, str)
    if t == "integer":
        return isinstance(instance, int) and not isinstance(instance, bool)
    if t == "number":
        return isinstance(instance, (int, float)) and not isinstance(instance, bool)
    if t == "boolean":
        return isinstance(instance, bool)
    if t == "null":
        return instance is None
    return True


def combinator_coverage(schema: Any, instance: Any, pointer: str = "") -> tuple[list[str], list[str]]:
    all_of: list[str] = []
    any_of: list[str] = []
    if not isinstance(schema, dict):
        return all_of, any_of
    if "allOf" in schema and isinstance(schema["allOf"], list):
        for i, branch in enumerate(schema["allOf"]):
            bp = f"{pointer}/allOf/{i}" if pointer else f"/allOf/{i}"
            if instance_matches(branch, instance):
                all_of.append(bp)
            a, b = combinator_coverage(branch, instance, bp)
            all_of.extend(a)
            any_of.extend(b)
    if "anyOf" in schema and isinstance(schema["anyOf"], list):
        for i, branch in enumerate(schema["anyOf"]):
            bp = f"{pointer}/anyOf/{i}" if pointer else f"/anyOf/{i}"
            if instance_matches(branch, instance):
                any_of.append(bp)
            a, b = combinator_coverage(branch, instance, bp)
            all_of.extend(a)
            any_of.extend(b)
    if "properties" in schema and isinstance(schema["properties"], dict) and isinstance(instance, dict):
        for k, sub in schema["properties"].items():
            if k in instance:
                cp = f"{pointer}/properties/{k}" if pointer else f"/properties/{k}"
                a, b = combinator_coverage(sub, instance[k], cp)
                all_of.extend(a)
                any_of.extend(b)
    return all_of, any_of


def load_examples(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def reference_staging(schema_dir: Path, examples_path: Path) -> dict[str, Any]:
    edges = resolve_refs(schema_dir)
    examples = load_examples(examples_path)
    schema_roots = {schema_id_for(p): load_json(p) for p in sorted(schema_dir.glob("*.json"))}
    coverage = []
    for idx, ex in enumerate(examples):
        sid = ex["schema_id"]
        if sid not in schema_roots:
            continue
        a, b = combinator_coverage(schema_roots[sid], ex["instance"])
        coverage.append(
            {
                "schema_id": sid,
                "example_id": f"ex-{idx:03}",
                "all_of_branches": sorted(a),
                "any_of_branches": sorted(b),
            }
        )
    coverage.sort(key=lambda r: (r["schema_id"], r["example_id"]))
    return {"ref_edges": edges, "example_coverage": coverage}


def reference_report(staging: dict[str, Any]) -> dict[str, Any]:
    edges = staging["ref_edges"]
    unresolved = [f"{e['schema_id']}:{e['ref_pointer']}" for e in edges if e["status"] == "unresolved"]
    schema_ids = sorted({e["schema_id"] for e in edges})
    return {
        "totals": {
            "schema_count": len(schema_ids),
            "resolved_ref_count": sum(1 for e in edges if e["status"] == "resolved"),
            "unresolved_ref_count": len(unresolved),
            "recursive_ref_count": sum(1 for e in edges if e["status"] == "recursive"),
            "example_count": len(staging["example_coverage"]),
        },
        "unresolved_refs": unresolved,
        "example_coverage": staging["example_coverage"],
    }


def reference_graph(staging: dict[str, Any]) -> dict[str, Any]:
    nodes_set = set()
    edges = []
    for e in staging["ref_edges"]:
        nodes_set.add(e["schema_id"])
        nodes_set.add(e["target_id"])
        edges.append({"from": e["schema_id"], "to": e["target_id"], "ref_kind": e["status"]})
    nodes = [
        {"id": nid, "kind": "definition" if "/" in nid else "schema"}
        for nid in sorted(nodes_set)
    ]
    edges.sort(key=lambda x: (x["from"], x["to"], x["ref_kind"]))
    return {"nodes": nodes, "edges": edges}
