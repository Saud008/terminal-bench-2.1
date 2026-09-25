#!/usr/bin/env python3
"""Build scenario bundle.json files with randomized teacher and room labels."""
from __future__ import annotations

import hashlib
import json
import os
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HIDDEN_ROOT = os.environ.get("TTALLOC_HIDDEN_ROOT")
TARGET = Path(HIDDEN_ROOT) if HIDDEN_ROOT else ROOT

BUNDLED = ["clean-timetable", "lab-room-required", "split-section-sync", "capacity-edge", "teacher-double-block", "stable-score-order", "multi-section-lab", "steady-rerun-atlas"]
HIDDEN = ["hidden-lab-trap", "hidden-split-trap"]

def _scenario_bundle(name: str, rng: random.Random, *, hidden: bool = False) -> dict:
    teachers = [
        {"teacher_id": f"T{rng.randint(100,999)}", "available_slots": []},
        {"teacher_id": f"T{rng.randint(100,999)}", "available_slots": []},
    ]
    slots = [
        {"slot_id": "MON-P1", "day": "MON", "period": 1},
        {"slot_id": "MON-P2", "day": "MON", "period": 2},
        {"slot_id": "TUE-P1", "day": "TUE", "period": 1},
    ]
    for t in teachers:
        t["available_slots"] = [s["slot_id"] for s in slots]
    rooms = [
        {"room_id": f"R{rng.randint(10,99)}", "capacity": 30, "room_kind": "classroom"},
        {"room_id": f"R{rng.randint(10,99)}", "capacity": 24, "room_kind": "lab"},
    ]
    policies = {"capacity_margin": 0}
    sections = []

    if name == "clean-timetable":
        sections = [
            {"section_id": "S1", "course_id": "C1", "teacher_id": teachers[0]["teacher_id"], "enrolled": 20, "requires_lab": False, "split_group": "", "preferred_slots": ["MON-P1"]},
            {"section_id": "S2", "course_id": "C2", "teacher_id": teachers[1]["teacher_id"], "enrolled": 18, "requires_lab": False, "split_group": "", "preferred_slots": ["MON-P2"]},
        ]
    elif name == "lab-room-required":
        sections = [
            {"section_id": "S1", "course_id": "CHEM", "teacher_id": teachers[0]["teacher_id"], "enrolled": 20, "requires_lab": True, "split_group": "", "preferred_slots": ["MON-P1"]},
        ]
    elif name == "split-section-sync":
        sections = [
            {"section_id": "S1A", "course_id": "MATH", "teacher_id": teachers[0]["teacher_id"], "enrolled": 15, "requires_lab": False, "split_group": "GRP1", "preferred_slots": ["MON-P1"]},
            {"section_id": "S1B", "course_id": "MATH", "teacher_id": teachers[1]["teacher_id"], "enrolled": 15, "requires_lab": False, "split_group": "GRP1", "preferred_slots": ["TUE-P1"]},
        ]
    elif name == "capacity-edge":
        policies["capacity_margin"] = 0
        rooms[0]["capacity"] = 25
        sections = [
            {"section_id": "S1", "course_id": "C1", "teacher_id": teachers[0]["teacher_id"], "enrolled": 15, "requires_lab": False, "split_group": "", "preferred_slots": ["MON-P1"]},
            {"section_id": "S2", "course_id": "C2", "teacher_id": teachers[1]["teacher_id"], "enrolled": 12, "requires_lab": False, "split_group": "", "preferred_slots": ["MON-P1"]},
        ]
    elif name == "teacher-double-block":
        sections = [
            {"section_id": "S1", "course_id": "C1", "teacher_id": teachers[0]["teacher_id"], "enrolled": 20, "requires_lab": False, "split_group": "", "preferred_slots": ["MON-P1"]},
            {"section_id": "S2", "course_id": "C2", "teacher_id": teachers[0]["teacher_id"], "enrolled": 18, "requires_lab": False, "split_group": "", "preferred_slots": ["MON-P1"]},
        ]
    elif name == "stable-score-order":
        sections = [
            {"section_id": "S2", "course_id": "C2", "teacher_id": teachers[0]["teacher_id"], "enrolled": 10, "requires_lab": False, "split_group": "", "preferred_slots": ["MON-P2"]},
            {"section_id": "S1", "course_id": "C1", "teacher_id": teachers[0]["teacher_id"], "enrolled": 10, "requires_lab": False, "split_group": "", "preferred_slots": ["MON-P1", "MON-P2"]},
        ]
    elif name == "multi-section-lab":
        sections = [
            {"section_id": "S1", "course_id": "BIO", "teacher_id": teachers[0]["teacher_id"], "enrolled": 12, "requires_lab": True, "split_group": "", "preferred_slots": ["MON-P1"]},
            {"section_id": "S2", "course_id": "BIO", "teacher_id": teachers[1]["teacher_id"], "enrolled": 10, "requires_lab": True, "split_group": "", "preferred_slots": ["TUE-P1"]},
        ]
    elif name == "steady-rerun-atlas":
        sections = [
            {"section_id": "S1", "course_id": "C1", "teacher_id": teachers[0]["teacher_id"], "enrolled": 20, "requires_lab": False, "split_group": "", "preferred_slots": ["MON-P1"]},
        ]
    elif name == "hidden-lab-trap":
        rooms[1]["capacity"] = 18
        sections = [
            {"section_id": "S1", "course_id": "PHYS", "teacher_id": teachers[0]["teacher_id"], "enrolled": 16, "requires_lab": True, "split_group": "", "preferred_slots": ["MON-P2"]},
        ]
    elif name == "hidden-split-trap":
        sections = [
            {"section_id": "S1A", "course_id": "ENG", "teacher_id": teachers[0]["teacher_id"], "enrolled": 14, "requires_lab": False, "split_group": "HSPL", "preferred_slots": ["MON-P1"]},
            {"section_id": "S1B", "course_id": "ENG-LIT", "teacher_id": teachers[1]["teacher_id"], "enrolled": 14, "requires_lab": False, "split_group": "HSPL", "preferred_slots": ["MON-P2"]},
        ]
    else:
        raise ValueError(name)

    seed = hashlib.sha256(f"{name}-{'hidden' if hidden else 'bundled'}".encode()).hexdigest()[:16]
    return {
        "seed": seed,
        "sections": sections,
        "teachers": teachers,
        "rooms": rooms,
        "slots": slots,
        "policies": policies,
    }



def build(name: str, hidden: bool = False) -> None:
    rng = random.Random(name + ("hidden" if hidden else "bundled"))
    body = _scenario_bundle(name, rng, hidden=hidden)
    dest = TARGET / "scenarios" / name
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "bundle.json").write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    for s in BUNDLED:
        build(s, hidden=False)
    if HIDDEN_ROOT:
        for s in HIDDEN:
            build(s, hidden=True)


if __name__ == "__main__":
    main()
