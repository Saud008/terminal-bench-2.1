"""Independent reference for turnctl ingest → simulate → export."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class ReferenceError(Exception):
    pass


def fnv1a64(text: str) -> int:
    h = 0xCBF29CE484222325
    for b in text.encode("utf-8"):
        h ^= b
        h = (h * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return h


@dataclass
class Actor:
    id: str
    name: str
    initiative: int
    hp: int
    max_hp: int
    bleed: int
    action_points: int
    stunned: bool = False
    pinned: bool = False
    alive: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "initiative": self.initiative,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "bleed": self.bleed,
            "action_points": self.action_points,
            "stunned": self.stunned,
            "pinned": self.pinned,
            "alive": self.alive,
        }


@dataclass
class CombatState:
    seed: str
    rounds_planned: int
    actors: list[Actor]
    rounds: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "state_version": 1,
            "seed": self.seed,
            "rounds_planned": self.rounds_planned,
            "actors": [a.to_dict() for a in self.actors],
            "rounds": self.rounds,
        }


def roster_checksum(actors: list[dict[str, Any]]) -> str:
    normalized = [Actor(**row).to_dict() for row in actors]
    payload = json.dumps(normalized, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def reference_ingest(roster_path: Path, staging_path: Path | None = None) -> dict[str, Any]:
    doc = json.loads(roster_path.read_text(encoding="utf-8"))
    actors = doc.get("actors", [])
    if not actors:
        raise ReferenceError("empty roster")
    for row in actors:
        if int(row.get("bleed", 0)) < 0:
            raise ReferenceError("negative bleed")
        if int(row.get("hp", 0)) <= 0:
            raise ReferenceError("invalid hp")
    staging = {
        "staging_version": 1,
        "rounds": int(doc.get("rounds", 1)),
        "actors": actors,
        "checksum": roster_checksum(actors),
    }
    if staging_path is not None:
        staging_path.parent.mkdir(parents=True, exist_ok=True)
        staging_path.write_text(json.dumps(staging, indent=2) + "\n", encoding="utf-8")
    return staging


def apply_seed_mutation(actors: list[Actor], seed: str) -> None:
    if not seed:
        return
    idx = fnv1a64(seed) % len(actors)
    delta = (fnv1a64(seed + ":bleed") % 3) + 1
    actors[idx].bleed += delta


def turn_order(actors: list[Actor]) -> list[Actor]:
    living = [a for a in actors if a.alive]
    ordered = sorted(living, key=lambda a: (-a.initiative, a.name))
    pinned = [a for a in ordered if a.pinned]
    rest = [a for a in ordered if not a.pinned]
    return pinned + rest


def apply_bleed_start(actor: Actor) -> dict[str, Any] | None:
    if actor.bleed <= 0:
        return None
    damage = actor.bleed
    actor.hp = max(0, actor.hp - damage)
    actor.bleed = max(0, actor.bleed - 1)
    return {
        "kind": "bleed",
        "actor": actor.id,
        "damage": damage,
        "hp_after": actor.hp,
        "bleed_after": actor.bleed,
    }


def mark_death(actor: Actor) -> dict[str, Any]:
    actor.alive = False
    actor.hp = 0
    actor.pinned = False
    actor.stunned = False
    return {"kind": "death", "actor": actor.id}


def reference_simulate(staging: dict[str, Any], seed: str = "") -> CombatState:
    actors = [Actor(**row) for row in deepcopy(staging["actors"])]
    apply_seed_mutation(actors, seed)
    state = CombatState(seed=seed, rounds_planned=int(staging["rounds"]), actors=actors)
    for rnd in range(1, state.rounds_planned + 1):
        events: list[dict[str, Any]] = []
        for actor in turn_order(actors):
            if not actor.alive or actor.action_points <= 0:
                continue
            bleed_ev = apply_bleed_start(actor)
            if bleed_ev:
                events.append(bleed_ev)
            if actor.hp <= 0:
                events.append(mark_death(actor))
                continue
            if actor.stunned:
                actor.action_points -= 1
                actor.stunned = False
                events.append({"kind": "stun_skip", "actor": actor.id, "ap_after": actor.action_points})
                continue
            actor.action_points -= 1
            events.append({"kind": "act", "actor": actor.id, "ap_after": actor.action_points})
        state.rounds.append({"round": rnd, "events": events})
    return state


def transcript_hash(state: CombatState) -> str:
    payload = json.dumps(state.rounds, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def reference_export(state: CombatState) -> dict[str, Any]:
    return {
        "export_version": 1,
        "seed": state.seed,
        "transcript_hash": transcript_hash(state),
        "rounds": deepcopy(state.rounds),
        "actors_final": [a.to_dict() for a in state.actors],
    }


def reference_pipeline(roster_path: Path, seed: str = "") -> dict[str, Any]:
    staging = reference_ingest(roster_path)
    state = reference_simulate(staging, seed)
    return reference_export(state)


def mutate_roster(roster: dict[str, Any], seed: str, tag: str) -> dict[str, Any]:
    out = deepcopy(roster)
    actors = out["actors"]
    idx = fnv1a64(f"{seed}:{tag}") % len(actors)
    actors[idx]["initiative"] = int(actors[idx]["initiative"]) + int(fnv1a64(tag) % 5)
    return out
