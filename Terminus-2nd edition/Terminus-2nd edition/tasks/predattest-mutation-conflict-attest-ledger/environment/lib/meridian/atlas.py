"""Rollout atlas + hold-witness serialization and the atlas digest.

The atlas digest is a SHA-256 over the deterministically ordered outcomes,
sealed nodes, and schema marks (see /app/docs/rollout-atlas-format.md). Shared
plumbing, not a swappable gate.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List

ATLAS_SCHEMA = "wavehold.rollout.v1"


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compact_json(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def atlas_digest(
    outcomes: List[Dict[str, Any]], nodes: List[Dict[str, Any]], schema_marks: List[str]
) -> str:
    ad = [
        {
            "attr": d["attr"],
            "edit_rank": d["edit_rank"],
            "index": d["index"],
            "node": d["node"],
            "reason": d["reason"],
            "value": d["value"],
        }
        for d in outcomes
    ]
    an = []
    for n in nodes:
        an.append(
            {
                "facets": {
                    k: [{"key": f["key"], "value": f["value"]} for f in v]
                    for k, v in n["facets"].items()
                },
                "lists": {
                    k: [{"lang": e.get("lang", ""), "value": e["value"]} for e in v]
                    for k, v in n["lists"].items()
                },
                "scalars": dict(n["scalars"]),
                "uid": n["uid"],
            }
        )
    payload = {"nodes": an, "outcomes": ad, "schema_marks": schema_marks}
    return sha256_hex(compact_json(payload))


def build_atlas(
    schema_marks: List[str],
    applied_edits: int,
    held_records: int,
    held_attrs: List[str],
    last_commit_index: int,
    outcomes: List[Dict[str, Any]],
    nodes: List[Dict[str, Any]],
) -> Dict[str, Any]:
    return {
        "schema": ATLAS_SCHEMA,
        "schema_marks": schema_marks,
        "applied_edits": applied_edits,
        "held_records": held_records,
        "held_attrs": held_attrs,
        "last_commit_index": last_commit_index,
        "outcomes": outcomes,
        "nodes": nodes,
        "atlas_digest": atlas_digest(outcomes, nodes, schema_marks),
    }


def witness_of(atlas: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "schema_marks": atlas["schema_marks"],
        "applied_edits": atlas["applied_edits"],
        "held_records": atlas["held_records"],
        "held_attrs": atlas["held_attrs"],
        "last_commit_index": atlas["last_commit_index"],
        "atlas_digest": atlas["atlas_digest"],
    }
