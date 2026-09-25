"""Gate: identity-bind preview — blank-node upsert binding. See /app/docs/identity-bind-preview.md."""

from __future__ import annotations

from typing import Any, Dict, List


def _sort_facets(facets: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return sorted(facets, key=lambda f: (f.get("key", ""), f.get("value", "")))


def _facets_equal(a: List[Dict[str, str]], b: List[Dict[str, str]]) -> bool:
    if len(a) != len(b):
        return False
    for x, y in zip(a, b):
        if x.get("key") != y.get("key") or x.get("value") != y.get("value"):
            return False
    return True


def _node_matches(g: Any, uid: str, keys: List[Dict[str, Any]]) -> bool:
    for key in keys:
        val, ok = g.get_scalar(uid, key["attr"])
        if not ok or val != key["value"]:
            return False
        kf = key.get("facets") or []
        if kf:
            stored = _sort_facets(g.get_facets(uid, key["attr"]))
            want = _sort_facets(kf)
            if not _facets_equal(stored, want):
                return False
    return True


def resolve_bind(g: Any, edit: Dict[str, Any]) -> str:
    if not edit.get("bind") or not edit.get("bind_on"):
        return g.resolve_node(edit["node"])
    for uid in g.uids_sorted():
        if _node_matches(g, uid, edit["bind_on"]):
            g.bind_blank(edit["node"], uid)
            return uid
    return g.resolve_node(edit["node"])
