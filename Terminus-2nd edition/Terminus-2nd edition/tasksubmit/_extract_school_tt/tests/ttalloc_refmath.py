"""Independent school timetable constraint reference simulator."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


def load_bundle(root: Path, scenario: str) -> dict:
    return json.loads((root / "scenarios" / scenario / "bundle.json").read_text(encoding="utf-8"))


def graph_fingerprint(bundle: dict) -> str:
    h = hashlib.sha256()
    h.update(bundle["seed"].encode())
    for sec in sorted(bundle["sections"], key=lambda s: s["section_id"]):
        h.update(sec["section_id"].encode())
    return h.hexdigest()


def score_bias() -> float:
    raw = os.environ.get("TB3_SCORE_BIAS", "")
    if not raw:
        return 0.0
    try:
        return float(raw)
    except ValueError:
        return 0.0


def stable_score(sec: dict, room: dict, slot: dict, bundle: dict) -> float:
    pref = 0.0
    for i, p in enumerate(sec.get("preferred_slots", [])):
        if p == slot["slot_id"]:
            pref = float(len(sec["preferred_slots"]) - i)
    tie = float(ord(sec["section_id"][0])) - float(ord(sec["teacher_id"][0]))
    return round((pref * 10.0 + float(room["capacity"]) * 0.01 + tie + score_bias()) * 1000) / 1000


def assignment_sort_key(row: dict) -> tuple:
    return (-row["score"], row["section_id"], row["teacher_id"], row["room_id"], row["slot_id"])


def reference_assignments(fixture_root: Path, scenario: str) -> dict:
    bundle = load_bundle(fixture_root, scenario)
    teachers = {t["teacher_id"]: t for t in bundle["teachers"]}
    rooms = sorted(bundle["rooms"], key=lambda r: r["room_id"])
    slots = sorted(bundle["slots"], key=lambda s: s["slot_id"])
    sections = sorted(bundle["sections"], key=lambda s: s["section_id"])
    margin = int(bundle["policies"].get("capacity_margin", 0))
    teacher_taken: dict[str, str] = {}
    room_usage: dict[str, int] = {}
    group_slot: dict[str, str] = {}
    assignments: list[dict] = []

    for sec in sections:
        sg = sec.get("split_group") or ""
        if sg and sg in group_slot:
            slot_id = group_slot[sg]
            room = _pick_room(sec, slot_id, rooms, room_usage, margin)
            if room is None:
                continue
            row = _make_row(sec, room, slot_id, bundle)
            assignments.append(row)
            _add_usage(room, slot_id, sec, room_usage)
            continue
        for slot in slots:
            if sec["teacher_id"] not in teachers:
                continue
            if slot["slot_id"] not in teachers[sec["teacher_id"]]["available_slots"]:
                continue
            if teacher_taken.get(sec["teacher_id"]) == slot["slot_id"]:
                continue
            room = _pick_room(sec, slot["slot_id"], rooms, room_usage, margin)
            if room is None:
                continue
            row = _make_row(sec, room, slot["slot_id"], bundle)
            assignments.append(row)
            teacher_taken[sec["teacher_id"]] = slot["slot_id"]
            _add_usage(room, slot["slot_id"], sec, room_usage)
            if sg:
                group_slot[sg] = slot["slot_id"]
            break

    assignments.sort(key=assignment_sort_key)
    return {
        "scenario": scenario,
        "engine": "ttalloc",
        "graph_fingerprint": graph_fingerprint(bundle),
        "assignments": assignments,
    }


def _pick_room(sec: dict, slot_id: str, rooms: list[dict], usage: dict[str, int], margin: int):
    for room in rooms:
        if sec.get("requires_lab") and room.get("room_kind") != "lab":
            continue
        key = room["room_id"] + "|" + slot_id
        total = usage.get(key, 0) + int(sec["enrolled"])
        if total <= int(room["capacity"]) - margin:
            return room
    return None


def _add_usage(room: dict, slot_id: str, sec: dict, usage: dict[str, int]) -> None:
    key = room["room_id"] + "|" + slot_id
    usage[key] = usage.get(key, 0) + int(sec["enrolled"])


def _make_row(sec: dict, room: dict, slot_id: str, bundle: dict) -> dict:
    slot = next(s for s in bundle["slots"] if s["slot_id"] == slot_id)
    return {
        "section_id": sec["section_id"],
        "teacher_id": sec["teacher_id"],
        "room_id": room["room_id"],
        "slot_id": slot_id,
        "score": stable_score(sec, room, slot, bundle),
    }


def reference_conflicts(fixture_root: Path, scenario: str, assignments: list[dict]) -> list[dict]:
    bundle = load_bundle(fixture_root, scenario)
    conflicts: list[dict] = []
    by_teacher_slot: dict[str, int] = {}
    by_room_slot: dict[str, int] = {}
    split_slots: dict[str, set[str]] = {}
    margin = int(bundle["policies"].get("capacity_margin", 0))
    room_cap = {r["room_id"]: int(r["capacity"]) for r in bundle["rooms"]}
    sec_map = {s["section_id"]: s for s in bundle["sections"]}

    for row in assignments:
        ts = row["teacher_id"] + "|" + row["slot_id"]
        by_teacher_slot[ts] = by_teacher_slot.get(ts, 0) + 1
        rs = row["room_id"] + "|" + row["slot_id"]
        by_room_slot[rs] = by_room_slot.get(rs, 0) + int(sec_map[row["section_id"]]["enrolled"])
        sec = sec_map[row["section_id"]]
        sg = sec.get("split_group") or ""
        if sg:
            split_slots.setdefault(sg, set()).add(row["slot_id"])

    for key, count in by_teacher_slot.items():
        if count > 1:
            conflicts.append({"kind": "teacher_double_book", "detail": key})
    for key, total in by_room_slot.items():
        room_id = key.split("|")[0]
        if total > room_cap[room_id] - margin:
            conflicts.append({"kind": "room_over_capacity", "detail": key})
    for sg, slots in split_slots.items():
        if len(slots) > 1:
            conflicts.append({"kind": "split_group_mismatch", "detail": sg})
    for row in assignments:
        sec = sec_map[row["section_id"]]
        room = next(r for r in bundle["rooms"] if r["room_id"] == row["room_id"])
        if sec.get("requires_lab") and room.get("room_kind") != "lab":
            conflicts.append({"kind": "lab_room_violation", "detail": row["section_id"]})
    conflicts.sort(key=lambda c: (c["kind"], c.get("detail", "")))
    return conflicts


def reference_graph_edges(bundle: dict) -> list[dict]:
    edges = []
    for sec in bundle["sections"]:
        edges.append({"kind": "section_teacher", "section_id": sec["section_id"], "teacher_id": sec["teacher_id"]})
        if sec.get("requires_lab"):
            edges.append({"kind": "lab_requirement", "section_id": sec["section_id"]})
    return edges
