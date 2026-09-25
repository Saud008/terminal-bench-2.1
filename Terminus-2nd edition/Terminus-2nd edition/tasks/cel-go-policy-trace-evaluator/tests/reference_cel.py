"""Reference CEL subset interpreter for independent verification."""

from __future__ import annotations

import json
from typing import Any


def parse_duration(s: str) -> int:
    s = s.strip()
    if s.endswith("ms"):
        return int(float(s[:-2]) * 1_000_000)
    if s.endswith("s"):
        return int(float(s[:-1]) * 1_000_000_000)
    if s.endswith("m"):
        return int(float(s[:-1]) * 60 * 1_000_000_000)
    raise ValueError(f"bad duration {s}")


def to_nanos(v: Any) -> int:
    if isinstance(v, str):
        return parse_duration(v)
    if isinstance(v, bool):
        raise TypeError("bool is not duration")
    return int(v)


class RefRuntime:
    def __init__(self, env: dict[str, Any]) -> None:
        self.env = dict(env)
        self.frames: list[dict[str, Any]] = [{}]
        self.has_call_count = 0
        self.branches: list[dict[str, Any]] = []

    def lookup(self, name: str) -> Any:
        for frame in reversed(self.frames):
            if name in frame:
                return frame[name]
        return self.env.get(name)

    def eval_node(self, node: dict[str, Any], path: str = "root") -> Any:
        typ = node["type"]
        if typ == "literal":
            val = node["value"]
            if node["kind"] == "bool":
                return bool(val)
            if node["kind"] == "int":
                return int(val)
            return str(val)
        if typ == "ident":
            v = self.lookup(node["name"])
            return False if v is None else v
        if typ == "binary":
            return self._eval_binary(node, path)
        if typ == "call":
            return self._eval_call(node, path)
        if typ == "map_comp":
            return self._eval_map(node, path)
        raise ValueError(f"unknown type {typ}")

    def _eval_binary(self, node: dict[str, Any], path: str) -> Any:
        op = node["op"]
        lv = self.eval_node(node["left"], path + ".left")
        if op == "and":
            self.branches.append({"op": op, "path": path, "evaluated": True})
            if not bool(lv):
                return False
            return bool(self.eval_node(node["right"], path + ".right"))
        if op == "or":
            self.branches.append({"op": op, "path": path, "evaluated": True})
            if bool(lv):
                return True
            return bool(self.eval_node(node["right"], path + ".right"))
        rv = self.eval_node(node["right"], path + ".right")
        self.branches.append({"op": op, "path": path, "evaluated": True})
        if op == "eq":
            return lv == rv
        ln, rn = to_nanos(lv), to_nanos(rv)
        if op == "lt":
            return ln < rn
        if op == "gt":
            return ln > rn
        raise ValueError(op)

    def _eval_call(self, node: dict[str, Any], path: str) -> Any:
        fn = node["fn"]
        if fn == "has":
            self.branches.append({"op": "call", "path": path, "evaluated": True})
            self.has_call_count += 1
            arg = node["args"][0]
            return self.lookup(arg["name"]) is not None
        if fn == "cel.bind":
            val = self.eval_node(node["args"][0], path + ".bind.val")
            name = node["args"][1]["name"]
            self.frames.append({name: val})
            self.branches.append({"op": "bind", "path": path, "evaluated": True})
            try:
                return self.eval_node(node["args"][2], path + ".bind.body")
            finally:
                self.frames.pop()
        raise ValueError(fn)

    def _eval_map(self, node: dict[str, Any], path: str) -> Any:
        items = self.lookup(node["items"])
        if items is None:
            return {}
        out: dict[str, Any] = {}
        for i, item in enumerate(items):
            self.frames.append({"item": item})
            try:
                key = self.eval_node(node["key_expr"], f"{path}.key.{i}")
                val = self.eval_node(node["value_expr"], f"{path}.val.{i}")
            finally:
                self.frames.pop()
            out[str(key)] = val
        return out


def reference_eval(root: dict[str, Any], env: dict[str, Any]) -> tuple[Any, list[dict[str, Any]], int]:
    rt = RefRuntime(env)
    result = rt.eval_node(root)
    return result, rt.branches, rt.has_call_count
