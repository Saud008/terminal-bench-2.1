"""In-memory fleet graph the compile pipeline mutates while previewing a wave.

Nodes carry scalar attributes, multi-valued (list) attributes, and per-attr
facets. Blank nodes (``_:name``) are allocated deterministic ``0x`` uids.
This module is shared plumbing and is not one of the swappable gate modules.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


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
