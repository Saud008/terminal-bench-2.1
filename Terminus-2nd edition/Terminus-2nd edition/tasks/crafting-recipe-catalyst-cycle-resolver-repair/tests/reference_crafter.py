"""Independent reference crafting engine for verifier anti-cheat."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from copy import deepcopy
from pathlib import Path
from typing import Any


def splitmix64(x: int) -> int:
    x = (x + 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF
    z = x
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & 0xFFFFFFFFFFFFFFFF
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & 0xFFFFFFFFFFFFFFFF
    return (z ^ (z >> 31)) & 0xFFFFFFFFFFFFFFFF


def seed_u32(seed: str, tag: str) -> int:
    digest = hashlib.sha256(f"{seed}:{tag}".encode()).digest()
    return int.from_bytes(digest[:4], "little")


def mutate_substitutes(book: dict[str, Any], seed: str) -> dict[str, str]:
    subs = dict(book.get("substitutes") or {})
    if seed_u32(seed, "flip-sub") % 2 == 0:
        subs.setdefault("iron_ore", "scrap_iron")
    else:
        subs["iron_ore"] = "scrap_iron"
    return subs


def slot_limit_for_seed(book: dict[str, Any], seed: str) -> int:
    base = int(book.get("slot_limit", 8))
    bump = seed_u32(seed, "slot-bump") % 2
    return base if bump == 0 else base


def resolve_inputs(book: dict[str, Any], recipe: dict[str, Any], batch_qty: int) -> list[dict[str, Any]]:
    subs = book.get("substitutes") or {}
    merged: dict[str, int] = defaultdict(int)
    for ing in recipe["inputs"]:
        effective = subs.get(ing["item"], ing["item"])
        merged[effective] += int(ing["qty"]) * batch_qty
    return [{"item": k, "qty": v} for k, v in sorted(merged.items())]


def item_def(book: dict[str, Any], item_id: str) -> dict[str, Any]:
    for item in book["items"]:
        if item["id"] == item_id:
            return item
    raise KeyError(item_id)


def plan_outputs(
    book: dict[str, Any], slots: list[dict[str, Any]], output: dict[str, Any], batch_qty: int
) -> list[dict[str, Any]]:
    total_qty = int(output["qty"]) * batch_qty
    idef = item_def(book, output["item"])
    placements: list[dict[str, Any]] = []
    new_slots = 0

    if output.get("stackable", True) and idef.get("stackable", True):
        existing = next((s for s in slots if s["item"] == output["item"]), None)
        if existing:
            if existing["qty"] + total_qty > idef["stack_max"]:
                raise ValueError("stack overflow")
            placements.append(
                {
                    "item": output["item"],
                    "qty": total_qty,
                    "target_slot": existing["slot"],
                    "new_slot": False,
                }
            )
        else:
            if total_qty > idef["stack_max"]:
                raise ValueError("stack overflow")
            new_slots = 1
            placements.append(
                {"item": output["item"], "qty": total_qty, "target_slot": None, "new_slot": True}
            )
    else:
        new_slots = batch_qty
        for _ in range(batch_qty):
            if int(output["qty"]) > idef["stack_max"]:
                raise ValueError("stack overflow")
            placements.append(
                {
                    "item": output["item"],
                    "qty": int(output["qty"]),
                    "target_slot": None,
                    "new_slot": True,
                }
            )

    if len(slots) + new_slots > int(book["slot_limit"]):
        raise ValueError("inventory full")
    return placements


def item_qty(slots: list[dict[str, Any]], item: str) -> int:
    return sum(int(s["qty"]) for s in slots if s["item"] == item)


def preview(book: dict[str, Any], slots: list[dict[str, Any]], recipe_id: str, batch_qty: int) -> dict[str, Any]:
    recipe = next((r for r in book["recipes"] if r["id"] == recipe_id), None)
    if recipe is None:
        return {"ok": False, "reason": "unknown recipe"}

    inputs = resolve_inputs(book, recipe, batch_qty)
    catalyst = None
    if recipe.get("catalyst"):
        cat = recipe["catalyst"]
        qty = int(cat["qty"]) * batch_qty if cat.get("consumed") else int(cat["qty"])
        catalyst = {"item": cat["item"], "qty": qty}

    try:
        outputs = plan_outputs(book, slots, recipe["output"], batch_qty)
    except ValueError as exc:
        return {"ok": False, "reason": str(exc), "inputs": inputs, "catalyst": catalyst}

    for need in inputs:
        if item_qty(slots, need["item"]) < need["qty"]:
            return {"ok": False, "reason": "insufficient materials", "inputs": inputs, "catalyst": catalyst}
    if catalyst and item_qty(slots, catalyst["item"]) < catalyst["qty"]:
        return {"ok": False, "reason": "missing catalyst", "inputs": inputs, "catalyst": catalyst}

    return {"ok": True, "inputs": inputs, "catalyst": catalyst, "outputs": outputs}


def apply(book: dict[str, Any], slots: list[dict[str, Any]], recipe_id: str, batch_qty: int) -> dict[str, Any]:
    snap = deepcopy(slots)
    plan = preview(book, slots, recipe_id, batch_qty)
    if not plan["ok"]:
        return plan

    recipe = next(r for r in book["recipes"] if r["id"] == recipe_id)
    working = deepcopy(slots)

    def deduct(item: str, qty: int) -> None:
        nonlocal working
        remaining = qty
        for slot in working:
            if slot["item"] != item:
                continue
            take = min(remaining, int(slot["qty"]))
            slot["qty"] -= take
            remaining -= take
        working = [s for s in working if int(s["qty"]) > 0]
        if remaining > 0:
            raise ValueError("deduction failed")

    try:
        for need in plan["inputs"]:
            deduct(need["item"], need["qty"])
        if plan.get("catalyst") and recipe.get("catalyst", {}).get("consumed"):
            deduct(plan["catalyst"]["item"], plan["catalyst"]["qty"])
        for placement in plan["outputs"]:
            if placement["new_slot"]:
                nxt = max((int(s["slot"]) for s in working), default=0) + 1
                working.append(
                    {"slot": nxt, "item": placement["item"], "qty": int(placement["qty"])}
                )
            else:
                for slot in working:
                    if slot["slot"] == placement["target_slot"]:
                        slot["qty"] += int(placement["qty"])
    except ValueError:
        return {"ok": False, "reason": "apply failed", "slots": snap}

    return {"ok": True, "slots": sorted(working, key=lambda s: s["slot"])}


def detect_cycles(book: dict[str, Any]) -> dict[str, Any]:
    producers = {r["output"]["item"]: r["id"] for r in book["recipes"]}
    edges: set[tuple[str, str]] = set()
    for recipe in book["recipes"]:
        items = [i["item"] for i in recipe["inputs"]]
        if recipe.get("catalyst"):
            items.append(recipe["catalyst"]["item"])
        for item in items:
            prod = producers.get(item)
            if prod and prod != recipe["id"]:
                edges.add((recipe["id"], prod))

    graph: dict[str, list[str]] = defaultdict(list)
    for a, b in edges:
        graph[a].append(b)

    cycles: list[list[str]] = []
    visiting: set[str] = set()
    visited: set[str] = set()
    stack: list[str] = []

    def dfs(node: str) -> None:
        if node in visiting:
            if node in stack:
                idx = stack.index(node)
                cycles.append(stack[idx:])
            return
        if node in visited:
            return
        visiting.add(node)
        stack.append(node)
        for nxt in graph.get(node, []):
            dfs(nxt)
        stack.pop()
        visiting.remove(node)
        visited.add(node)

    for node in {r["id"] for r in book["recipes"]}:
        if node not in visited:
            dfs(node)

    return {
        "recipe_count": len(book["recipes"]),
        "edge_count": len(edges),
        "cyclic": bool(cycles),
        "cycles": cycles,
    }


def overlay_book(path: Path, seed: str) -> dict[str, Any]:
    book = json.loads(path.read_text(encoding="utf-8"))
    book["substitutes"] = mutate_substitutes(book, seed)
    book["slot_limit"] = slot_limit_for_seed(book, seed)
    return book


def smelt_batch_for_seed(seed: str) -> int:
    return 1 + (seed_u32(seed, "smelt-qty") % 3)


def overflow_batch(seed: str) -> int:
    return 2 + (seed_u32(seed, "overflow-qty") % 2)
