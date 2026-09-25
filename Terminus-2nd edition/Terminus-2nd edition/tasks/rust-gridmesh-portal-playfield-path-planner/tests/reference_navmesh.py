"""Independent reference navmesh validate + pathfind."""

from __future__ import annotations

import hashlib
import json
import math
from collections import deque
from pathlib import Path

Q16_ONE = 65536


def seed_tag(seed: int, mesh_id: str) -> str:
    return hashlib.sha256(f"{seed}:{mesh_id}".encode()).hexdigest()[:8]


def perturb_cost_q16(base: int, seed: int) -> int:
    bump = (seed % 511) * 128
    return base + bump


def synthetic_offmesh(seed: int, mesh: dict) -> dict | None:
    walkable = [c for c in mesh["cells"] if c["walkable"]]
    if len(walkable) < 2:
        return None
    digest = hashlib.sha256(f"offmesh:{seed}:{mesh['mesh_id']}".encode()).digest()
    pairs: list[tuple[dict, dict]] = []
    for i, left in enumerate(walkable):
        for right in walkable[i + 1 :]:
            if abs(left["gx"] - right["gx"]) + abs(left["gy"] - right["gy"]) == 1:
                pairs.append((left, right))
    if not pairs:
        return None
    pick = digest[0] % len(pairs)
    from_cell, to_cell = pairs[pick]
    cost_q16 = 196608 + (digest[1] % 2048) * 16
    return {
        "id": f"seed-{seed_tag(seed, mesh['mesh_id'])}",
        "from": from_cell["id"],
        "to": to_cell["id"],
        "cost_q16": cost_q16,
        "snap_radius_q16": 131072,
    }


def load_mesh(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def cell_map(mesh: dict) -> dict[str, dict]:
    return {c["id"]: c for c in mesh["cells"]}


def linear_dist_q16(a: dict, b: dict) -> int:
    dx = a["gx"] - b["gx"]
    dy = a["gy"] - b["gy"]
    dist = math.sqrt(dx * dx + dy * dy)
    return int(round(dist * Q16_ONE))


def snap_ok(a: dict, b: dict, snap_radius_q16: int) -> bool:
    return linear_dist_q16(a, b) <= snap_radius_q16


def count_islands(mesh: dict) -> int:
    walkable = {(c["gx"], c["gy"]) for c in mesh["cells"] if c["walkable"]}
    seen: set[tuple[int, int]] = set()
    islands = 0
    dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    for gx, gy in walkable:
        if (gx, gy) in seen:
            continue
        islands += 1
        q = deque([(gx, gy)])
        seen.add((gx, gy))
        while q:
            x, y = q.popleft()
            for dx, dy in dirs:
                nxt = (x + dx, y + dy)
                if nxt in walkable and nxt not in seen:
                    seen.add(nxt)
                    q.append(nxt)
    return islands


def reference_validate(mesh: dict, seed: int) -> dict:
    cells = cell_map(mesh)
    errors: list[str] = []
    links_checked = 0
    portals_checked = 0

    for portal in mesh.get("portals", []):
        portals_checked += 1
        if portal.get("require_region_match"):
            left = cells[portal["from"]]
            right = cells[portal["to"]]
            if left["region"] != right["region"]:
                errors.append(
                    f"portal {portal['id']} region mismatch {left['region']} vs {right['region']}"
                )

    for link in mesh.get("offmesh", []):
        links_checked += 1
        left = cells[link["from"]]
        right = cells[link["to"]]
        if not snap_ok(left, right, link["snap_radius_q16"]):
            errors.append(f"offmesh {link['id']} snap radius exceeded")

    seed_link = synthetic_offmesh(seed, mesh)
    if seed_link:
        links_checked += 1
        left = cells[seed_link["from"]]
        right = cells[seed_link["to"]]
        if not snap_ok(left, right, seed_link["snap_radius_q16"]):
            errors.append(f"offmesh {seed_link['id']} snap radius exceeded")

    return {
        "mesh_id": mesh["mesh_id"],
        "seed": seed,
        "ok": not errors,
        "errors": errors,
        "islands": count_islands(mesh),
        "links_checked": links_checked,
        "portals_checked": portals_checked,
    }


def build_graph(mesh: dict, seed: int) -> tuple[dict[str, dict], dict[str, list[tuple[str, int]]]]:
    nodes = {c["id"]: c for c in mesh["cells"]}
    adj: dict[str, list[tuple[str, int]]] = {}

    def add_bidir(frm: str, to: str, cost_q16: int) -> None:
        adj.setdefault(frm, []).append((to, cost_q16))
        adj.setdefault(to, []).append((frm, cost_q16))

    for edge in mesh.get("edges", []):
        cost = perturb_cost_q16(edge["cost_q16"], seed)
        add_bidir(edge["from"], edge["to"], cost)

    for portal in mesh.get("portals", []):
        add_bidir(portal["from"], portal["to"], portal["cost_q16"])

    for link in mesh.get("offmesh", []):
        add_bidir(link["from"], link["to"], link["cost_q16"])

    seed_link = synthetic_offmesh(seed, mesh)
    if seed_link:
        add_bidir(seed_link["from"], seed_link["to"], seed_link["cost_q16"])

    return nodes, adj


def path_total_q16(edge_costs_f64: list[float]) -> int:
    acc = 0
    for cost in edge_costs_f64:
        acc += int(round(cost * Q16_ONE))
    return acc


def dijkstra(adj: dict[str, list[tuple[str, int]]], start: str, goal: str) -> tuple[list[str], list[float]]:
    import heapq

    dist: dict[str, float] = {start: 0.0}
    parent: dict[str, str | None] = {start: None}
    heap = [(0.0, start)]
    seen: set[str] = set()

    while heap:
        cost, node = heapq.heappop(heap)
        if node in seen:
            continue
        seen.add(node)
        if node == goal:
            break
        for nxt, step_q16 in adj.get(node, []):
            step = step_q16 / Q16_ONE
            nxt_cost = cost + step
            if nxt not in dist or nxt_cost < dist[nxt]:
                dist[nxt] = nxt_cost
                parent[nxt] = node
                heapq.heappush(heap, (nxt_cost, nxt))

    if goal not in seen:
        return [], []

    path: list[str] = []
    cur: str | None = goal
    while cur is not None:
        path.append(cur)
        cur = parent.get(cur)
    path.reverse()

    edge_costs: list[float] = []
    for left, right in zip(path, path[1:]):
        step_q16 = next(c for n, c in adj[left] if n == right)
        edge_costs.append(step_q16 / Q16_ONE)
    return path, edge_costs


def reference_path(mesh: dict, seed: int, frm: str, to: str) -> dict:
    _, adj = build_graph(mesh, seed)
    path, edge_costs = dijkstra(adj, frm, to)
    if not path:
        return {
            "mesh_id": mesh["mesh_id"],
            "seed": seed,
            "from": frm,
            "to": to,
            "status": "unreachable",
            "cost_q16": 0,
            "path": [],
        }
    return {
        "mesh_id": mesh["mesh_id"],
        "seed": seed,
        "from": frm,
        "to": to,
        "status": "ok",
        "cost_q16": path_total_q16(edge_costs),
        "path": path,
    }
