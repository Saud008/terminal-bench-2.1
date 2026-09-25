"""Independent reference model for the wavehold rollout-preview gate math.

Rebuilt from the operator contracts under /app/docs (deny-pin-hold,
identity-bind-preview, conflict-precedence-hold, list-coalesce-rules,
preflight-hold-rules, schema-bump-abort, hold-witness-format,
rollout-atlas-format) alone. It computes the exact rollout ledger the
`wavehold compile`/`publish` pipeline must reproduce for a mutation wave:
policy holds, blank-node identity binding, conflict precedence, list
coalescing, preflight holds, transactional schema marks, and the atlas
digest.

Standard library only. Lives under /tests for the verifier harness and is
never on the operator build path under /app.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple

ATLAS_SCHEMA = "wavehold.rollout.v1"
ROOT_NODE = "0xroot"


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compact_json(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


# ---------------------------------------------------------------------------
# Wave / config loading
# ---------------------------------------------------------------------------

def load_config(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_wave(path: str) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


# ---------------------------------------------------------------------------
# Fleet graph state
# ---------------------------------------------------------------------------

class FleetGraph:
    def __init__(self) -> None:
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.blank_map: Dict[str, str] = {}
        self.next_uid = 1

    @staticmethod
    def _new_node() -> Dict[str, Any]:
        return {"scalars": {}, "lists": {}, "facets": {}}

    def _copy_node(self, n: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "scalars": dict(n["scalars"]),
            "lists": {k: [dict(e) for e in v] for k, v in n["lists"].items()},
            "facets": {k: [dict(f) for f in v] for k, v in n["facets"].items()},
        }

    def snapshot(self) -> "FleetGraph":
        g = FleetGraph()
        g.next_uid = self.next_uid
        g.blank_map = dict(self.blank_map)
        g.nodes = {uid: self._copy_node(n) for uid, n in self.nodes.items()}
        return g

    def rollback_to(self, src: "FleetGraph") -> None:
        self.next_uid = src.next_uid
        self.blank_map = dict(src.blank_map)
        self.nodes = {uid: self._copy_node(n) for uid, n in src.nodes.items()}

    def resolve_node(self, node: str) -> str:
        if node.startswith("_:"):
            if node in self.blank_map:
                return self.blank_map[node]
            uid = f"0x{self.next_uid:x}"
            self.next_uid += 1
            self.blank_map[node] = uid
            self.nodes[uid] = self._new_node()
            return uid
        if node not in self.nodes:
            self.nodes[node] = self._new_node()
        return node

    def bind_blank(self, node: str, uid: str) -> None:
        self.blank_map[node] = uid

    def uids_sorted(self) -> List[str]:
        return sorted(self.nodes.keys())

    def get_scalar(self, uid: str, attr: str) -> Tuple[Optional[str], bool]:
        n = self.nodes.get(uid)
        if n is None or attr not in n["scalars"]:
            return None, False
        return n["scalars"][attr], True

    def set_scalar(self, uid: str, attr: str, value: str) -> None:
        self.nodes.setdefault(uid, self._new_node())["scalars"][attr] = value

    def get_facets(self, uid: str, attr: str) -> List[Dict[str, str]]:
        n = self.nodes.get(uid)
        if n is None:
            return []
        return list(n["facets"].get(attr, []))

    def set_facets(self, uid: str, attr: str, facets: List[Dict[str, str]]) -> None:
        self.nodes.setdefault(uid, self._new_node())["facets"][attr] = [dict(f) for f in facets]

    def get_list(self, uid: str, attr: str) -> List[Dict[str, str]]:
        n = self.nodes.get(uid)
        if n is None:
            return []
        return list(n["lists"].get(attr, []))

    def set_list(self, uid: str, attr: str, entries: List[Dict[str, str]]) -> None:
        self.nodes.setdefault(uid, self._new_node())["lists"][attr] = [dict(e) for e in entries]

    def seal(self) -> List[Dict[str, Any]]:
        out = []
        for uid in self.uids_sorted():
            n = self.nodes[uid]
            out.append(
                {
                    "uid": uid,
                    "scalars": dict(n["scalars"]),
                    "lists": {
                        k: [{"value": e["value"], "lang": e.get("lang", "")} for e in v]
                        for k, v in n["lists"].items()
                    },
                    "facets": {
                        k: [{"key": f["key"], "value": f["value"]} for f in v]
                        for k, v in n["facets"].items()
                    },
                }
            )
        return out


# ---------------------------------------------------------------------------
# Gate math
# ---------------------------------------------------------------------------

def attr_is_held(attr: str, hold_attrs: List[str]) -> bool:
    """Gate 1 (deny-pin-hold): whole-attr exact match only."""
    return any(attr == p for p in hold_attrs)


def _sort_facets(facets: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return sorted(facets, key=lambda f: (f.get("key", ""), f.get("value", "")))


def _facets_equal(a: List[Dict[str, str]], b: List[Dict[str, str]]) -> bool:
    if len(a) != len(b):
        return False
    for x, y in zip(a, b):
        if x.get("key") != y.get("key") or x.get("value") != y.get("value"):
            return False
    return True


def _node_matches(g: FleetGraph, uid: str, keys: List[Dict[str, Any]]) -> bool:
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


def resolve_bind(g: FleetGraph, edit: Dict[str, Any]) -> str:
    """Gate 2 (identity-bind-preview): a blank upsert binds to an existing
    node only when every bind_on key matches by value and by sorted facet
    keys; otherwise a fresh node is allocated."""
    if not edit.get("bind") or not edit.get("bind_on"):
        return g.resolve_node(edit["node"])
    for uid in g.uids_sorted():
        if _node_matches(g, uid, edit["bind_on"]):
            g.bind_blank(edit["node"], uid)
            return uid
    return g.resolve_node(edit["node"])


def resolve_precedence(pending: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Gate 3 (conflict-precedence-hold): among scalar edits to the same
    (uid, attr), the highest edit_rank wins; ties break toward the later
    record position. wall_time_ms is never consulted."""
    groups: Dict[Tuple[str, str], List[int]] = {}
    for i, w in enumerate(pending):
        if w["multi"]:
            continue
        groups.setdefault((w["uid"], w["attr"]), []).append(i)

    winner: Dict[Tuple[str, str], int] = {}
    for k, idxs in groups.items():
        best = idxs[0]
        for i in idxs[1:]:
            if pending[i]["edit_rank"] >= pending[best]["edit_rank"]:
                best = i
        winner[k] = best

    out: List[Dict[str, Any]] = []
    for i, w in enumerate(pending):
        if w["multi"]:
            out.append({"edit": w, "reason": "list_coalesce", "winner": True})
            continue
        k = (w["uid"], w["attr"])
        if len(groups[k]) == 1:
            out.append({"edit": w, "reason": "commit_admit", "winner": True})
        elif winner[k] == i:
            out.append({"edit": w, "reason": "precedence_winner", "winner": True})
        else:
            out.append({"edit": w, "reason": "precedence_loser", "winner": False})
    return out


def coalesce_entry(
    existing: List[Dict[str, str]], add: Dict[str, str]
) -> Tuple[List[Dict[str, str]], bool]:
    """Gate 4 (list-coalesce-rules): list entries are distinct on the pair
    (value, lang)."""
    for e in existing:
        if e["value"] == add["value"] and e.get("lang", "") == add.get("lang", ""):
            return existing, False
    return existing + [add], True


def preflight_ok(g: FleetGraph, rec: Dict[str, Any]) -> bool:
    """Gate 5 (preflight-hold-rules): every @if precondition is checked
    against the LIVE root-node state before any edit of the record is bound
    or applied. A missing scalar or non-eq op fails the whole record."""
    for c in rec.get("preconds") or []:
        val, ok = g.get_scalar(ROOT_NODE, c["attr"])
        if not ok:
            return False
        if c.get("op") == "eq":
            if val != c["value"]:
                return False
        else:
            return False
    return True


def apply_schema_marks(cache: List[str], names: List[str]) -> None:
    for n in names:
        if n and n not in cache:
            cache.append(n)


# ---------------------------------------------------------------------------
# Record processing
# ---------------------------------------------------------------------------

def process_record(
    g: FleetGraph,
    cache: List[str],
    cfg: Dict[str, Any],
    rec: Dict[str, Any],
    st: Dict[str, Any],
) -> None:
    graph_snap = g.snapshot()
    schema_snap = list(cache)

    if not preflight_ok(g, rec):
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
        uid = resolve_bind(g, edit)
        rank = edit.get("edit_rank") or (i + 1)
        if attr_is_held(edit["attr"], hold_attrs):
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

    resolved = resolve_precedence(pending)

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
            merged, did = coalesce_entry(cur, {"value": w["value"], "lang": w["lang"]})
            if did:
                applied += 1
            g.set_list(w["uid"], w["attr"], merged)
            continue
        g.set_scalar(w["uid"], w["attr"], w["value"])
        if w["facets"]:
            g.set_facets(w["uid"], w["attr"], w["facets"])
        applied += 1

    apply_schema_marks(cache, rec.get("schema_marks") or [])

    if not rec.get("commit", False):
        # Gate 6 (schema-bump-abort): a non-committing record restores the
        # graph and schema-mark snapshot taken before the record ran.
        g.rollback_to(graph_snap)
        cache[:] = schema_snap
        return

    st["applied_edits"] += applied


# ---------------------------------------------------------------------------
# Atlas digest and public API
# ---------------------------------------------------------------------------

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


def compile_atlas(config_path: str, wave_path: str) -> Dict[str, Any]:
    """Return the full rollout atlas dict (matching `wavehold publish`
    output), computed independently from the operator contracts."""
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

    schema_marks = sorted(cache)
    nodes = g.seal()
    held_attrs = sorted(st["held_attrs"])
    last_index = records[-1]["commit_index"] if records else 0
    digest = atlas_digest(st["outcomes"], nodes, schema_marks)

    return {
        "schema": ATLAS_SCHEMA,
        "schema_marks": schema_marks,
        "applied_edits": st["applied_edits"],
        "held_records": st["held_records"],
        "held_attrs": held_attrs,
        "last_commit_index": last_index,
        "outcomes": st["outcomes"],
        "nodes": nodes,
        "atlas_digest": digest,
    }


def witness_of(atlas: Dict[str, Any]) -> Dict[str, Any]:
    """Derive the expected hold-witness fields from a compiled atlas."""
    return {
        "schema_marks": atlas["schema_marks"],
        "applied_edits": atlas["applied_edits"],
        "held_records": atlas["held_records"],
        "held_attrs": atlas["held_attrs"],
        "last_commit_index": atlas["last_commit_index"],
        "atlas_digest": atlas["atlas_digest"],
    }


if __name__ == "__main__":
    import sys

    cfg_path = sys.argv[1] if len(sys.argv) > 1 else "/app/config/wavehold.json"
    wave_p = sys.argv[2] if len(sys.argv) > 2 else "/app/fixtures/waves/wave-alpha.jsonl"
    print(json.dumps(compile_atlas(cfg_path, wave_p), indent=2, sort_keys=True))
