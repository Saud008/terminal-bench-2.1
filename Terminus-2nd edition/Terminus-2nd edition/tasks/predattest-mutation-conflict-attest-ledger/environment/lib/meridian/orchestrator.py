"""Compile orchestrator: walk a mutation wave through the six gates.

Shared plumbing that sequences the gate modules. It must not itself encode
gate policy; every hold/precedence/coalesce/abort decision is delegated to a
module under meridian.gates so the verifier can swap one gate at a time.
"""

from __future__ import annotations

from typing import Any, Dict, List

from meridian.atlas import build_atlas
from meridian.gates import (
    conflict_precedence,
    deny_pin_hold,
    identity_bind,
    list_coalesce,
    preflight_hold,
    schema_bump_abort,
)
from meridian.graphstate import FleetGraph
from meridian.waveload import load_config, load_wave

ROOT_NODE = "0xroot"


def process_record(
    g: FleetGraph,
    cache: List[str],
    cfg: Dict[str, Any],
    rec: Dict[str, Any],
    st: Dict[str, Any],
) -> None:
    graph_snap = g.snapshot()
    schema_snap = list(cache)

    if not preflight_hold.preflight_ok(g, rec):
        st["held_records"] += 1
        st["outcomes"].append(
            {
                "index": rec["commit_index"],
                "node": "",
                "attr": "",
                "reason": "preflight_hold",
                "value": "",
                "edit_rank": 0,
            }
        )
        return

    hold_attrs = cfg.get("hold_attrs") or []
    slots: List[Dict[str, Any]] = []
    pending: List[Dict[str, Any]] = []

    for i, edit in enumerate(rec.get("edits") or []):
        uid = identity_bind.resolve_bind(g, edit)
        rank = edit.get("edit_rank") or (i + 1)
        if deny_pin_hold.attr_is_held(edit["attr"], hold_attrs):
            st["held_attrs"].add(edit["attr"])
            slots.append(
                {
                    "held": True,
                    "dec": {
                        "index": rec["commit_index"],
                        "node": uid,
                        "attr": edit["attr"],
                        "reason": "policy_hold",
                        "value": edit.get("value", ""),
                        "edit_rank": rank,
                    },
                }
            )
            continue
        pending.append(
            {
                "index": rec["commit_index"],
                "edit_rank": rank,
                "uid": uid,
                "attr": edit["attr"],
                "value": edit.get("value", ""),
                "lang": edit.get("lang", ""),
                "multi": bool(edit.get("multi")),
                "facets": edit.get("facets") or [],
            }
        )
        slots.append({"held": False, "pidx": len(pending) - 1})

    resolved = conflict_precedence.resolve_precedence(pending)

    for s in slots:
        if s["held"]:
            st["outcomes"].append(s["dec"])
            continue
        r = resolved[s["pidx"]]
        w = r["edit"]
        st["outcomes"].append(
            {
                "index": rec["commit_index"],
                "node": w["uid"],
                "attr": w["attr"],
                "reason": r["reason"],
                "value": w["value"],
                "edit_rank": w["edit_rank"],
            }
        )

    applied = 0
    for r in resolved:
        if not r["winner"]:
            continue
        w = r["edit"]
        if w["multi"]:
            cur = g.get_list(w["uid"], w["attr"])
            merged, did = list_coalesce.coalesce_entry(cur, {"value": w["value"], "lang": w["lang"]})
            if did:
                applied += 1
            g.set_list(w["uid"], w["attr"], merged)
            continue
        g.set_scalar(w["uid"], w["attr"], w["value"])
        if w["facets"]:
            g.set_facets(w["uid"], w["attr"], w["facets"])
        applied += 1

    for n in rec.get("schema_marks") or []:
        if n and n not in cache:
            cache.append(n)

    if not schema_bump_abort.keep_commit(rec):
        g.rollback_to(graph_snap)
        cache[:] = schema_snap
        return

    st["applied_edits"] += applied


def compile_atlas(config_path: str, wave_path: str) -> Dict[str, Any]:
    cfg = load_config(config_path)
    records = load_wave(wave_path)

    g = FleetGraph()
    g.resolve_node(ROOT_NODE)
    g.set_scalar(ROOT_NODE, "state", cfg.get("root_state") or "active")

    cache: List[str] = []
    st: Dict[str, Any] = {
        "outcomes": [],
        "applied_edits": 0,
        "held_records": 0,
        "held_attrs": set(),
    }

    for rec in records:
        process_record(g, cache, cfg, rec, st)

    return build_atlas(
        schema_marks=sorted(cache),
        applied_edits=st["applied_edits"],
        held_records=st["held_records"],
        held_attrs=sorted(st["held_attrs"]),
        last_commit_index=records[-1]["commit_index"] if records else 0,
        outcomes=st["outcomes"],
        nodes=g.seal(),
    )
