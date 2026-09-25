"""Independent reference for bratctl consensus export.

Derives expected consensus solely from annotation-stage.json (plus optional
generation counter from consensus-generation.json). Never trusts implementation
span/relation rows from the consensus witness.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def shift_for(project: dict, doc_id: str, revision: int) -> int:
    entry = project.get("revision_map", {}).get(doc_id, {})
    return int(entry.get("shifts", {}).get(str(revision), 0))


def normalize_span(project: dict, span: dict) -> dict:
    entry = project.get("revision_map", {}).get(span["doc_id"], {})
    shift = shift_for(project, span["doc_id"], span["revision"])
    return {
        **span,
        "revision": entry.get("current_revision", span["revision"]),
        "start": span["start"] + shift,
        "end": span["end"] + shift,
    }


def overlaps(a: dict, b: dict) -> bool:
    return (
        a["doc_id"] == b["doc_id"]
        and a["label"] == b["label"]
        and a["start"] < b["end"]
        and b["start"] < a["end"]
    )


def resolve_overlaps(spans: list[dict]) -> list[dict]:
    if not spans:
        return []
    sorted_spans = sorted(spans, key=lambda s: (s["doc_id"], s["label"], s["start"]))
    groups: list[list[dict]] = []
    for s in sorted_spans:
        placed = False
        for g in groups:
            if any(overlaps(x, s) for x in g):
                g.append(s)
                placed = True
                break
        if not placed:
            groups.append([s])
    winners: list[dict] = []
    for g in groups:
        winner = g[0]
        for c in g[1:]:
            if c["weight"] > winner["weight"]:
                winner = c
            elif c["weight"] == winner["weight"]:
                clen = c["end"] - c["start"]
                wlen = winner["end"] - winner["start"]
                if clen > wlen or (clen == wlen and c["source_id"] < winner["source_id"]):
                    winner = c
        winners.append(winner)
    return sorted(winners, key=lambda s: (s["doc_id"], s["start"], s["end"]))


def prefer_locks(spans: list[dict]) -> list[dict]:
    locked = [s for s in spans if s.get("locked")]
    unlocked = [s for s in spans if not s.get("locked")]
    kept = [u for u in unlocked if not any(overlaps(u, l) for l in locked)]
    return locked + resolve_overlaps(kept)


def build_consensus(stage: dict) -> dict[str, Any]:
    project = stage["project"]
    normalized = []
    for s in stage.get("spans") or []:
        row = {
            "source_id": s["source_id"],
            "annotator": s["annotator"],
            "doc_id": s["doc_id"],
            "revision": s["revision"],
            "start": s["start"],
            "end": s["end"],
            "label": s["label"],
            "weight": s["weight"],
            "locked": s.get("locked", False),
        }
        # Staging should already be revision-normalized; normalize_span is idempotent
        # when revision equals current_revision (shift 0).
        normalized.append(normalize_span(project, row))
    resolved = prefer_locks(normalized)

    consensus_spans = []
    span_map: dict[str, str] = {}
    for i, winner in enumerate(resolved, start=1):
        cid = f"c-s{i}"
        group = [x for x in normalized if overlaps(x, winner)]
        score = sum(x["weight"] for x in group)
        if winner.get("locked"):
            score = 1000.0
        consensus_spans.append(
            {
                "id": cid,
                "doc_id": winner["doc_id"],
                "start": winner["start"],
                "end": winner["end"],
                "label": winner["label"],
                "score": score,
                "locked": winner.get("locked", False),
            }
        )
        for orig in normalized:
            if overlaps(orig, winner):
                span_map[f"{orig['annotator']}:{orig['source_id']}"] = cid

    mapped_rels = []
    for r in stage.get("relations") or []:
        key_from = f"{r['annotator']}:{r['from']}"
        key_to = f"{r['annotator']}:{r['to']}"
        arg1 = span_map.get(key_from, r["from"])
        arg2 = span_map.get(key_to, r["to"])
        mapped_rels.append({**r, "from": arg1, "to": arg2})

    rel_groups: dict[str, list[dict]] = {}
    for r in mapped_rels:
        key = f"{r['doc_id']}|{r['from']}|{r['to']}|{r['type']}"
        rel_groups.setdefault(key, []).append(r)

    consensus_rels = []
    for i, key in enumerate(sorted(rel_groups), start=1):
        group = rel_groups[key]
        winner = max(group, key=lambda x: x["weight"])
        score = sum(x["weight"] for x in group)
        consensus_rels.append(
            {
                "id": f"c-r{i}",
                "doc_id": winner["doc_id"],
                "arg1_span": winner["from"],
                "arg2_span": winner["to"],
                "type": winner["type"],
                "score": score,
                "locked": winner.get("locked", False),
            }
        )

    consensus_spans.sort(key=lambda s: (s["doc_id"], s["start"], s["end"]))
    return {
        "staging_generation": stage["staging_generation"],
        "project_digest": stage["project_digest"],
        "spans": consensus_spans,
        "relations": consensus_rels,
        "generation": 1,
    }


def span_key(s: dict) -> str:
    return f"{s['doc_id']}:{s['label']}:{s['start']}-{s['end']}"


def rel_key(r: dict) -> str:
    return f"{r['doc_id']}:{r['arg1_span']}->{r['arg2_span']}:{r['type']}"


def consensus_digest(project_id: str, spans: list[dict], rels: list[dict]) -> str:
    payload = {
        "project_id": project_id,
        "spans": sorted(span_key(s) for s in spans),
        "relations": sorted(rel_key(r) for r in rels),
    }
    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(body).hexdigest()


def reference_export(stage_path: Path, gen_path: Path | None = None) -> dict[str, Any]:
    stage = json.loads(stage_path.read_text(encoding="utf-8"))
    gen = build_consensus(stage)
    if gen_path and gen_path.is_file():
        # Only borrow the monotonic generation counter; span/relation truth is independent.
        witness = json.loads(gen_path.read_text(encoding="utf-8"))
        gen["generation"] = witness.get("generation", gen["generation"])
    spans = sorted(gen["spans"], key=lambda s: (s["doc_id"], s["start"], s["end"]))
    rels = sorted(gen["relations"], key=lambda r: (r["doc_id"], r["arg1_span"], r["arg2_span"]))
    return {
        "project_id": stage["project_id"],
        "staging_generation": stage["staging_generation"],
        "consensus_generation": gen.get("generation", 1),
        "spans": spans,
        "relations": rels,
        "consensus_digest": consensus_digest(stage["project_id"], spans, rels),
    }
