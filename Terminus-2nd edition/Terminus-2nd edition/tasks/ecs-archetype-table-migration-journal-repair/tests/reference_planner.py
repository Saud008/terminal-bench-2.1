"""Independent ECS reference planner — mirrors golden archecore semantics."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def seed_u64(seed: str) -> int:
    h = hashlib.sha256(seed.encode()).digest()
    return int.from_bytes(h[:8], "little")


def xorshift64(state: int) -> int:
    x = state & 0xFFFFFFFFFFFFFFFF
    x ^= (x << 13) & 0xFFFFFFFFFFFFFFFF
    x ^= (x >> 7) & 0xFFFFFFFFFFFFFFFF
    x ^= (x << 17) & 0xFFFFFFFFFFFFFFFF
    return x


def registration_order(names: list[str], seed: str) -> list[str]:
    order = list(names)
    state = seed_u64(seed)
    for i in range(len(order) - 1, 0, -1):
        state = xorshift64(state)
        j = state % (i + 1)
        order[i], order[j] = order[j], order[i]
    return order


def build_component_map(order: list[str]) -> dict[str, int]:
    return {name: idx for idx, name in enumerate(order)}


def archetype_hash(rows: list[tuple[int, int]], *, include_align: bool) -> int:
    h = hashlib.sha256()
    for cid, align in sorted(rows, key=lambda r: r[0]):
        h.update(cid.to_bytes(2, "little"))
        if include_align:
            h.update(align.to_bytes(4, "little"))
    return int.from_bytes(h.digest()[:8], "little")


def hash_hex(rows: list[tuple[int, int]]) -> str:
    return f"{archetype_hash(rows, include_align=True):016x}"


def parse_component_data(value: Any) -> tuple[str, int | None]:
    if isinstance(value, str):
        return value, None
    return value["data"], value.get("align")


class ReferenceWorld:
    def __init__(self, spec: dict[str, Any], seed: str) -> None:
        self.seed = seed
        self.spec = spec
        order = registration_order(spec["component_names"], seed)
        self.component_map = build_component_map(order)
        self.specs = spec["components"]
        self.entities: dict[int, dict[int, dict[str, Any]]] = {}
        self.tombstones: set[int] = set()
        self.generation = 0
        self.sparse_gen: dict[int, int] = {}
        self.free_slots: list[int] = []
        self.slot_of: dict[int, int] = {}
        self.slots: list[dict[str, Any]] = []
        for ent in spec.get("entities", []):
            self._insert_entity(ent)

    def default_align(self, name: str) -> int:
        return int(self.specs[name]["align"])

    def _alloc_slot(self, entity: int) -> None:
        if self.free_slots:
            idx = self.free_slots.pop()
            self.slots[idx]["generation"] += 1
            self.slots[idx]["entity"] = entity
            self.slots[idx]["alive"] = True
        else:
            idx = len(self.slots)
            self.slots.append({"entity": entity, "generation": 0, "alive": True})
        self.slot_of[entity] = idx
        self.sparse_gen[entity] = self.slots[idx]["generation"]

    def _free_slot(self, entity: int) -> None:
        idx = self.slot_of.pop(entity, None)
        if idx is None:
            return
        self.slots[idx]["alive"] = False
        self.free_slots.append(idx)
        self.sparse_gen.pop(entity, None)

    def _insert_entity(self, ent: dict[str, Any]) -> None:
        eid = int(ent["id"])
        if eid in self.tombstones:
            return
        self._alloc_slot(eid)
        comps: dict[int, dict[str, Any]] = {}
        for name, raw in ent["components"].items():
            data, align_override = parse_component_data(raw)
            cid = self.component_map[name]
            align = align_override if align_override is not None else self.default_align(name)
            comps[cid] = {"data": data, "align": align}
        self.entities[eid] = comps
        self.generation += 1

    def apply_journal(self, journal: list[dict[str, Any]]) -> None:
        for op in journal:
            kind = op["op"]
            if kind == "add_component":
                eid = int(op["entity"])
                if eid in self.tombstones:
                    continue
                name = op["component"]
                cid = self.component_map[name]
                align = op.get("align", self.default_align(name))
                if eid in self.entities:
                    self.entities[eid][cid] = {"data": op["data"], "align": align}
                    self.generation += 1
            elif kind == "remove_component":
                eid = int(op["entity"])
                cid = self.component_map[op["component"]]
                if eid in self.entities and cid in self.entities[eid]:
                    del self.entities[eid][cid]
                    self.generation += 1
            elif kind == "remove_entity":
                eid = int(op["entity"])
                self.entities.pop(eid, None)
                self._free_slot(eid)
                self.generation += 1
            elif kind == "tombstone":
                eid = int(op["entity"])
                self.tombstones.add(eid)
                self.generation += 1
            elif kind == "spawn":
                self._insert_entity({"id": op["entity"], "components": op["components"]})

    def archetype_rows(self, comps: dict[int, dict[str, Any]]) -> list[tuple[int, int]]:
        rows = [(cid, int(c["align"])) for cid, c in comps.items()]
        rows.sort(key=lambda r: r[0])
        return rows

    def migrate_export(self) -> dict[str, Any]:
        arch: dict[str, dict[str, Any]] = {}
        for comps in self.entities.values():
            rows = self.archetype_rows(comps)
            hx = hash_hex(rows)
            if hx not in arch:
                arch[hx] = {
                    "hash": hx,
                    "component_ids": [r[0] for r in rows],
                    "alignments": [r[1] for r in rows],
                    "count": 0,
                }
            arch[hx]["count"] += 1
        entities = []
        for eid in sorted(self.entities):
            comps = self.entities[eid]
            rows = self.archetype_rows(comps)
            entities.append(
                {
                    "id": eid,
                    "archetype_hash": hash_hex(rows),
                    "slot_generation": self.sparse_gen.get(eid, 0),
                    "components": {str(cid): c["data"] for cid, c in sorted(comps.items())},
                }
            )
        # normalize component keys to int in output like Rust BTreeMap
        for ent in entities:
            ent["components"] = {int(k): v for k, v in ent["components"].items()}
        return {
            "seed": self.seed,
            "generation": self.generation,
            "component_map": {k: v for k, v in self.component_map.items()},
            "archetypes": sorted(arch.values(), key=lambda a: a["hash"]),
            "entities": entities,
        }

    def query(self, component_ids: list[int]) -> list[int]:
        want = sorted(component_ids)
        out = []
        for eid, comps in self.entities.items():
            if eid in self.tombstones:
                continue
            have = sorted(comps.keys())
            if all(c in have for c in want):
                out.append(eid)
        return sorted(out)


def load_world(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def reference_migrate(world_path: Path, seed: str) -> dict[str, Any]:
    spec = load_world(world_path)
    world = ReferenceWorld(spec, seed)
    world.apply_journal(spec.get("journal", []))
    return world.migrate_export()


def reference_snapshot(world_path: Path, seed: str) -> dict[str, Any]:
    doc = reference_migrate(world_path, seed)
    return {"snapshot_version": 1, **doc}


def reference_query(world_path: Path, seed: str, component_ids: list[int]) -> dict[str, Any]:
    spec = load_world(world_path)
    world = ReferenceWorld(spec, seed)
    world.apply_journal(spec.get("journal", []))
    return {
        "seed": seed,
        "generation": world.generation,
        "query": component_ids,
        "entities": world.query(component_ids),
        "cache_hit": False,
    }


def reference_query_batch(batch_path: Path, seed: str) -> dict[str, Any]:
    batch = json.loads(batch_path.read_text(encoding="utf-8"))
    results = []
    for step in batch["steps"]:
        world_path = Path(step["world_path"])
        component_ids = [int(c) for c in step["components"]]
        results.append(reference_query(world_path, seed, component_ids))
    return {"seed": seed, "results": results}


def procedural_migrate(spec: dict[str, Any], seed: str) -> dict[str, Any]:
    world = ReferenceWorld(spec, seed)
    world.apply_journal(spec.get("journal", []))
    return world.migrate_export()


def tombstone_add_component_world() -> dict[str, Any]:
    """add_component on a tombstoned entity must not resurrect the id."""
    return {
        "component_names": ["Health", "Armor"],
        "components": {
            "Health": {"size": 4, "align": 4},
            "Armor": {"size": 4, "align": 4},
        },
        "entities": [{"id": 1, "components": {"Health": "64"}}],
        "journal": [
            {"op": "remove_entity", "entity": 1},
            {"op": "tombstone", "entity": 1},
            {"op": "add_component", "entity": 1, "component": "Armor", "data": "ff", "align": 4},
        ],
        "queries": [],
    }


def query_cache_refresh_worlds() -> tuple[dict[str, Any], dict[str, Any]]:
    """Same logical world before and after a generation-changing journal mutation."""
    base: dict[str, Any] = {
        "component_names": ["Marker"],
        "components": {"Marker": {"size": 4, "align": 4}},
        "queries": [],
    }
    before = {
        **base,
        "entities": [{"id": 1, "components": {"Marker": "aa"}}],
        "journal": [],
    }
    after = {
        **base,
        "entities": [{"id": 1, "components": {"Marker": "aa"}}],
        "journal": [{"op": "spawn", "entity": 2, "components": {"Marker": "bb"}}],
    }
    return before, after
