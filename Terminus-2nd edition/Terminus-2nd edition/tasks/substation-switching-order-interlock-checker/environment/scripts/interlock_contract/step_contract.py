"""Independent substation interlock reference engine for pytest."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


def load_yard_fixture(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def breaker_states_from_fixture(sf: dict[str, Any]) -> dict[str, str]:
    return {row["breaker_id"]: row["initial_state"] for row in sf["breakers"]}


def breaker_edges(sf: dict[str, Any]) -> list[tuple[str, str, str]]:
    return [(b["breaker_id"], b["from_bus"], b["to_bus"]) for b in sf["breakers"]]


def energized_buses(
    sources: list[str],
    edges: list[tuple[str, str, str]],
    states: dict[str, str],
) -> list[str]:
    live: set[str] = set(sources)
    graph: dict[str, list[str]] = {}
    for bid, a, b in edges:
        if states.get(bid) != "closed":
            continue
        graph.setdefault(a, []).append(b)
        graph.setdefault(b, []).append(a)
    growing = True
    while growing:
        growing = False
        frontier = list(live)
        for node in frontier:
            for nb in graph.get(node, ()):
                if nb not in live:
                    live.add(nb)
                    growing = True
    return sorted(live)


def loto_blocks_step(
    lockouts: list[dict[str, Any]],
    step: dict[str, Any],
    from_bus: str,
    to_bus: str,
) -> bool:
    for tag in lockouts:
        if not tag.get("active"):
            continue
        for target in tag.get("equipment_ids", ()):
            if target in (step["breaker_id"], from_bus, to_bus):
                return True
    return False


def isolation_close_blocked(step: dict[str, Any], bus: str, energized: list[str]) -> bool:
    return bool(step.get("requires_isolation")) and bus in energized


def isolation_open_blocked(
    step: dict[str, Any],
    bid: str,
    frm: str,
    to: str,
    sources: list[str],
    edges: list[tuple[str, str, str]],
    states: dict[str, str],
) -> bool:
    if not step.get("parallel_path_guard"):
        return False
    before = set(energized_buses(sources, edges, states))
    trial = dict(states)
    trial[bid] = "open"
    after = set(energized_buses(sources, edges, trial))
    return frm in before and to in before and (frm not in after or to not in after)


def reference_simulate_steps(sf: dict[str, Any], snap: dict[str, Any]) -> dict[str, Any]:
    """Independent reference math for verify-order step simulation."""
    return simulate_procedure(sf, snap)


def simulate_procedure(sf: dict[str, Any], snap: dict[str, Any]) -> dict[str, Any]:
    edges = breaker_edges(sf)
    states = breaker_states_from_fixture(sf)
    rows: list[dict[str, Any]] = []
    expect = 1
    for step in sorted(sf["procedure"], key=lambda s: s["step_index"]):
        codes: list[str] = []
        if step["step_index"] != expect:
            codes.append("out_of_order")
        frm = to = ""
        known = False
        for bid, a, b in edges:
            if bid == step["breaker_id"]:
                frm, to, known = a, b, True
                break
        if not known:
            codes.append("unknown_breaker")
        energized = energized_buses(snap["energized_sources"], edges, states)
        if loto_blocks_step(sf.get("lockouts", []), step, frm, to):
            codes.append("lockout_active")
        if isolation_close_blocked(step, to, energized):
            codes.append("close_blocked_energized")
        if isolation_open_blocked(step, step["breaker_id"], frm, to, snap["energized_sources"], edges, states):
            codes.append("open_parallel_risk")
        ok = not codes
        if ok:
            states[step["breaker_id"]] = "closed" if step["action"] == "close" else "open"
            expect += 1
        post = energized_buses(snap["energized_sources"], edges, states)
        rows.append(
            {
                "step_index": step["step_index"],
                "action": step["action"],
                "breaker_id": step["breaker_id"],
                "safe": ok,
                "reason_codes": sorted(set(codes)),
                "energized_buses": post,
            }
        )
    unsafe = sum(1 for r in rows if not r["safe"])
    final = rows[-1]["energized_buses"] if rows else energized_buses(snap["energized_sources"], edges, states)
    summary = {"total_steps": len(rows), "unsafe_count": unsafe, "final_energized_buses": final}
    idx = sorted(r["step_index"] for r in rows)
    reasons = Counter()
    for r in rows:
        reasons.update(r["reason_codes"])
    digest_body = json.dumps(
        {
            "total_steps": summary["total_steps"],
            "unsafe_count": summary["unsafe_count"],
            "step_indices": idx,
            "reasons": dict(sorted(reasons.items())),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return {"steps": rows, "summary": summary, "audit_digest": hashlib.sha256(digest_body.encode()).hexdigest()}


def loto_ticket_id(seed: str, scenario: str, load_seq: int) -> str:
    raw = f"{seed}:{scenario}:{load_seq}"
    return "loto-" + hashlib.sha256(raw.encode()).hexdigest()[:12]
