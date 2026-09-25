"""Independent reference for netifd-ctl harness (verifier-only).

teardown_log is the complete ordered harness event log (apply, reload, and teardown
steps), including rules_commit during apply and link_down/link_down_ack/route_del_default
during teardown — see /app/docs/export-schema.md.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HARNESS = Path("/app/harness")
if str(HARNESS) not in sys.path:
    sys.path.insert(0, str(HARNESS))
import state  # noqa: E402


def route_binding(payload: dict) -> str:
    parts = [
        payload["scenario"],
        payload["iface"],
        json.dumps(payload.get("routes", []), separators=(",", ":"), ensure_ascii=False),
        json.dumps(payload.get("addresses", []), separators=(",", ":"), ensure_ascii=False),
        json.dumps(payload.get("pd_leases", []), separators=(",", ":"), ensure_ascii=False),
        json.dumps(payload.get("rules", []), separators=(",", ":"), ensure_ascii=False),
        json.dumps(payload.get("teardown_log", []), separators=(",", ":"), ensure_ascii=False),
    ]
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


def load_scenario(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def apply_scenario(scenario: dict, scenario_name: str, *, reset: bool = True) -> dict:
    if reset:
        state.reset()
    iface = scenario["iface"]
    state.link_up(iface)
    bonus = int(scenario.get("kernel_metric_bonus", 0))
    config_metric = int(scenario["config_metric"])
    metric = state.assign_metric(iface, config_metric, bonus)
    for route in scenario.get("routes", []):
        state.route_add(route["dst"], route.get("via", ""), iface, metric)
    seen: set[tuple[str, str, str]] = set()
    for ev in scenario.get("hotplug", []) or []:
        if ev.get("op") != "add":
            continue
        key = (iface, ev.get("family", "inet"), ev["addr"])
        if key in seen:
            continue
        seen.add(key)
        state.addr_add(iface, ev.get("family", "inet"), ev["addr"], dedupe=True)
    prefix = scenario.get("pd_prefix")
    if prefix:
        lease_id = scenario.get("pd_lease_id") or "pd-default"
        state.pd_acquire(iface, prefix, lease_id)
    state.rules_set(list(scenario.get("rules", [])))
    state.rules_commit()
    payload = state.export_payload(scenario_name, iface)
    payload["schema"] = 1
    payload["route_binding"] = route_binding(payload)
    return payload


def reload_scenario(scenario: dict, scenario_name: str) -> dict:
    state.pd_release_iface(scenario["iface"])
    state.reload_prepare(scenario["iface"])
    return apply_scenario(scenario, scenario_name, reset=False)


def teardown_scenario(scenario: dict, scenario_name: str) -> None:
    iface = scenario["iface"]
    state.link_down(iface)
    state.link_down_ack(iface)
    state.route_del_default(iface)
    assigned = state.get_assigned_metric(iface, int(scenario["config_metric"]))
    for route in scenario.get("routes", []):
        state.route_add(route["dst"], route.get("via", ""), iface, assigned)


def payload_to_export(payload: dict) -> dict:
    return {
        "scenario": payload["scenario"],
        "iface": payload["iface"],
        "routes": payload["routes"],
        "addresses": payload["addresses"],
        "pd_leases": payload["pd_leases"],
        "rules": payload["rules"],
        "rules_committed": payload["rules_committed"],
        "teardown_log": payload["teardown_log"],
        "route_binding": payload["route_binding"],
    }


def reference_export(scenario_path: Path, *, reload: bool = False, teardown: bool = False) -> dict:
    scenario = load_scenario(scenario_path)
    name = scenario_path.stem
    if reload:
        payload = reload_scenario(scenario, name)
    else:
        payload = apply_scenario(scenario, name)
    if teardown:
        teardown_scenario(scenario, name)
        payload = state.export_payload(name, scenario["iface"])
        payload["schema"] = 1
        payload["route_binding"] = route_binding(payload)
    return payload_to_export(payload)


def expected_teardown_order() -> list[str]:
    """Teardown-phase step names in required order (subset of full teardown_log)."""
    return ["link_down", "link_down_ack", "route_del_default"]
