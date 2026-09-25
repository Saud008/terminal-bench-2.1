"""Independent ConnMan-style WiFi roam handoff reference."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SECURITY_RANK = {"wpa3": 3, "wpa2": 2, "wpa": 1, "open": 0}


def load_scenario(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_fsm_states(scenario: dict[str, Any], scan_credited: bool, handoff_success: bool) -> list[str]:
    states = ["CONNECTED", "DISCONNECTING", "DISCONNECT_COMPLETE", "SCANNING"]
    if scan_credited:
        states.extend(["ASSOCIATING", "DHCP_RENEW"])
    if handoff_success:
        states.append("CONNECTED_TARGET")
    return states


def build_scan_ledger(scenario: dict[str, Any]) -> tuple[list[dict[str, Any]], bool]:
    required = set(scenario["scan"]["required_bssids"])
    ledger: list[dict[str, Any]] = []
    credited_any = False
    for idx, event in enumerate(scenario["scan"]["events"]):
        credited = False
        if (
            not credited_any
            and event["type"] == "full"
            and float(event["coverage"]) >= 1.0
            and required.issubset(set(event.get("bssids_seen", [])))
        ):
            credited = True
            credited_any = True
        ledger.append(
            {
                "event_index": idx,
                "event_type": event["type"],
                "coverage": float(event["coverage"]),
                "credited": credited,
            }
        )
    return ledger, credited_any


def rank_service(scenario: dict[str, Any]) -> tuple[dict[str, Any] | None, bool]:
    candidates: list[dict[str, Any]] = list(scenario.get("services") or [])
    hidden = scenario.get("hidden_candidate")
    consent = bool(scenario.get("user_consent_hidden"))
    if hidden:
        if consent:
            candidates.append(hidden)
    if not candidates:
        return None, True

    def sort_key(item: dict[str, Any]) -> tuple:
        sec = SECURITY_RANK.get(item["security"], -1)
        return (
            -int(item["preference"]),
            -int(item["signal"]),
            -sec,
            str(item["ssid"]),
        )

    winner = sorted(candidates, key=sort_key)[0]
    honored = not (winner.get("hidden") and not consent)
    return (
        {
            "ssid": winner["ssid"],
            "security": winner["security"],
            "hidden": bool(winner.get("hidden")),
        },
        honored,
    )


def dhcp_gateway(scenario: dict[str, Any]) -> str:
    return str(scenario["target_bss"]["gateway"])


def simulate_handoff(scenario: dict[str, Any], seed: int) -> dict[str, Any]:
    _ = seed  # reserved for timestamp jitter in extended fixtures
    ledger, scan_credited = build_scan_ledger(scenario)
    selected, consent_honored = rank_service(scenario)
    gateway = dhcp_gateway(scenario) if scan_credited and selected else scenario["current_bss"]["gateway"]
    handoff_success = bool(
        scan_credited
        and selected
        and consent_honored
        and gateway == scenario["target_bss"]["gateway"]
        and selected["ssid"] == scenario["target_bss"]["ssid"]
    )
    states = run_fsm_states(scenario, scan_credited, handoff_success)
    return {
        "scenario_id": scenario["scenario_id"],
        "seed": int(seed),
        "fsm_states": states,
        "scan_ledger": ledger,
        "scan_credited": scan_credited,
        "selected_service": selected,
        "dhcp_gateway": gateway,
        "handoff_success": handoff_success,
        "consent_honored": consent_honored,
    }


def reference_export(scenario_path: Path, seed: int) -> dict[str, Any]:
    scenario = load_scenario(scenario_path)
    return simulate_handoff(scenario, seed)
