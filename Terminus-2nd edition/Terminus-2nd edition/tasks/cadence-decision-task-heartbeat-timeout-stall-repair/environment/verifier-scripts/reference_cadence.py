"""Independent Cadence decision-task replay reference FSM (verifier-only)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _latest_sticky(gens: list[dict[str, Any]], at_ms: int) -> dict[str, Any]:
    pick: dict[str, Any] = {}
    for g in gens:
        if g["at_ms"] <= at_ms and g.get("generation", 0) >= pick.get("generation", 0):
            pick = g
    return pick


def _apply_heartbeat(state: dict[str, Any], hb: dict[str, Any], sc: dict[str, Any]) -> None:
    timeout = sc["visibility_timeout_ms"]
    seq = hb["progress_seq"]
    at_ms = hb["at_ms"]
    if seq > state["last_progress_seq"]:
        state["last_progress_seq"] = seq
        state["visibility_deadline_ms"] = at_ms + timeout
        state["last_heartbeat_ms"] = at_ms
    elif seq == state["last_progress_seq"]:
        state["visibility_deadline_ms"] = at_ms + timeout
        state["last_heartbeat_ms"] = at_ms


def _check_timeout(state: dict[str, Any], now_ms: int, sc: dict[str, Any]) -> None:
    if state["timed_out"]:
        return
    if state["visibility_deadline_ms"] > 0 and now_ms <= state["visibility_deadline_ms"]:
        return
    if state["last_heartbeat_ms"] > 0 and now_ms - state["last_heartbeat_ms"] <= sc["heartbeat_grace_ms"]:
        return
    if now_ms >= sc["task_start_ms"] + sc["start_to_close_timeout_ms"]:
        state["timed_out"] = True


def _apply_history(state: dict[str, Any], ev: dict[str, Any]) -> None:
    eid = ev["event_id"]
    if eid in state["seen_event_ids"]:
        state["duplicate_skipped"] += 1
        return
    state["seen_event_ids"].add(eid)
    state["applied_names"].append(ev["name"])
    if ev["seq"] > state["history_cursor_seq"]:
        state["history_cursor_seq"] = ev["seq"]


def _process_query(state: dict[str, Any], q: dict[str, Any]) -> None:
    ok = state["last_progress_seq"] >= q["required_progress_seq"]
    state["query_results"].append(
        {
            "query_id": q["query_id"],
            "accepted": ok,
            "reason": "ok" if ok else "heartbeat progress insufficient",
        }
    )


def _evaluate_poll(state: dict[str, Any], poll_ms: int, sc: dict[str, Any]) -> None:
    gens = sc.get("sticky_generations") or []
    if poll_ms <= 0 or not gens:
        return
    expected = _latest_sticky(gens, poll_ms)
    state["sticky_partition"] = expected["partition"]


def _timeline(sc: dict[str, Any]) -> list[tuple[int, str, int]]:
    items: list[tuple[int, str, int]] = []
    for i, ev in enumerate(sc.get("history_events") or []):
        items.append((ev["at_ms"], "history", i))
    for i, hb in enumerate(sc.get("heartbeats") or []):
        items.append((hb["at_ms"], "heartbeat", i))
    for i, ms in enumerate(sc.get("timeout_checks_ms") or []):
        items.append((ms, "timeout", i))
    for i, q in enumerate(sc.get("query_tasks") or []):
        items.append((q["at_ms"], "query", i))
    if sc.get("decision_poll_ms", 0) > 0:
        items.append((sc["decision_poll_ms"], "poll", 0))
    items.sort(key=lambda t: (t[0], t[1]))
    return items


def reference_replay(scenario_path: Path) -> dict[str, Any]:
    sc = json.loads(scenario_path.read_text(encoding="utf-8"))
    state: dict[str, Any] = {
        "visibility_deadline_ms": 0,
        "last_progress_seq": 0,
        "last_heartbeat_ms": 0,
        "sticky_partition": "",
        "history_cursor_seq": 0,
        "seen_event_ids": set(),
        "applied_names": [],
        "duplicate_skipped": 0,
        "decision_task_lost": False,
        "lost_decision_reason": "",
        "timed_out": False,
        "query_results": [],
    }
    for _at_ms, kind, idx in _timeline(sc):
        if kind == "history":
            _apply_history(state, sc["history_events"][idx])
        elif kind == "heartbeat":
            _apply_heartbeat(state, sc["heartbeats"][idx], sc)
        elif kind == "timeout":
            _check_timeout(state, sc["timeout_checks_ms"][idx], sc)
        elif kind == "query":
            _process_query(state, sc["query_tasks"][idx])
        elif kind == "poll":
            _evaluate_poll(state, sc["decision_poll_ms"], sc)
    return {
        "workflow_id": sc["workflow_id"],
        "visibility_deadline_ms": state["visibility_deadline_ms"],
        "last_progress_seq": state["last_progress_seq"],
        "sticky_partition": state["sticky_partition"],
        "history_cursor_seq": state["history_cursor_seq"],
        "history_events_applied": list(state["applied_names"]),
        "duplicate_events_skipped": state["duplicate_skipped"],
        "decision_task_lost": state["decision_task_lost"],
        "timed_out": state["timed_out"],
        "query_results": list(state["query_results"]),
        "lost_decision_reason": state["lost_decision_reason"],
        "last_heartbeat_ms": state["last_heartbeat_ms"],
    }
