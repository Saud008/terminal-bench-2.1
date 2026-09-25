"""Independent reference for quadlet parse, order, and render."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, "/app/tools")
from quadlet_parser import file_meta, list_dropins, unit_name_from_container  # noqa: E402

CLI = "/app/bin/quadlet-resolver"
TOUCH = Path("/app/output/.parser-touch")


def _merge_lists(dst: list[str], src: list[str]) -> None:
    for item in src:
        if item not in dst:
            dst.append(item)


def build_parse_graph(tree: Path) -> dict:
    units: dict[str, dict] = {}
    for base in sorted(tree.rglob("*.container")):
        name = unit_name_from_container(base)
        merged: dict = {"unit": {}, "service": {}, "container": {}}
        fragments = [base] + list_dropins(base)
        for frag in fragments:
            sections = file_meta(frag)["sections"]
            unit = sections.get("Unit", {})
            svc = sections.get("Service", {})
            ctr = sections.get("Container", {})
            for key in ("Wants", "Requires"):
                if key in unit:
                    merged["unit"].setdefault(key, [])
                    vals = unit[key] if isinstance(unit[key], list) else [unit[key]]
                    _merge_lists(merged["unit"][key], vals)
            for key, val in unit.items():
                if key not in ("After", "Wants", "Requires"):
                    merged["unit"][key] = val
            for key, val in svc.items():
                if key == "EnvironmentFile":
                    merged["service"].setdefault(key, [])
                    items = val if isinstance(val, list) else [val]
                    _merge_lists(merged["service"][key], items)
                else:
                    merged["service"][key] = val
            for key, val in ctr.items():
                merged["container"][key] = val
        for frag in fragments:
            sections = file_meta(frag)["sections"]
            unit = sections.get("Unit", {})
            if "After" in unit:
                merged["unit"].setdefault("After", [])
                vals = unit["After"] if isinstance(unit["After"], list) else [unit["After"]]
                _merge_lists(merged["unit"]["After"], vals)
        merged["source"] = str(base.resolve())
        units[name] = merged
    return {"tree": str(tree.resolve()), "units": units}


def build_edges(units: dict[str, dict]) -> dict[str, list[str]]:
    names = sorted(units.keys())
    edges = {n: [] for n in names}
    for unit, meta in units.items():
        u = meta.get("unit", {})
        for key in ("After", "Wants"):
            for dep in u.get(key, []):
                if dep in names and dep != unit:
                    edges[unit].append(dep)
    return edges


def find_cycle(units: dict[str, dict]) -> list[str] | None:
    names = sorted(units.keys())
    edges = build_edges(units)
    state: dict[str, int] = {}
    stack: list[str] = []
    cycle: list[str] = []

    def dfs(node: str) -> None:
        state[node] = 1
        stack.append(node)
        for nxt in edges.get(node, []):
            if nxt not in state:
                dfs(nxt)
            elif state[nxt] == 1:
                i = stack.index(nxt)
                cycle.extend(stack[i:] + [nxt])
                return
        state[node] = 2
        stack.pop()

    for node in names:
        if node not in state:
            dfs(node)
        if cycle:
            return cycle
    return None


def topo_order(units: dict[str, dict]) -> list[str]:
    names = sorted(units.keys())
    edges = build_edges(units)
    indeg = {n: 0 for n in names}
    children = {n: [] for n in names}
    for unit, deps in edges.items():
        for dep in deps:
            children[dep].append(unit)
            indeg[unit] += 1
    queue = sorted([n for n in names if indeg[n] == 0])
    order: list[str] = []
    while queue:
        node = queue.pop(0)
        order.append(node)
        for child in sorted(children.get(node, [])):
            indeg[child] -= 1
            if indeg[child] == 0:
                queue.append(child)
                queue.sort()
    return order


def run_cli_parse(tree: Path, out: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [CLI, "parse", "--tree", str(tree), "--out", str(out)],
        capture_output=True,
        text=True,
        check=False,
    )


def run_cli_order(tree: Path, out: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [CLI, "order", "--tree", str(tree), "--out", str(out)],
        capture_output=True,
        text=True,
        check=False,
    )


def load_cli_parse(out: Path) -> dict:
    return json.loads(out.read_text(encoding="utf-8"))
