"""Simulated netlink/route kernel state for netifd-ctl harness."""

from __future__ import annotations

import json
from pathlib import Path

RUNTIME = Path("/app/harness/runtime")
ROUTES = RUNTIME / "routes.json"
ADDRS = RUNTIME / "addresses.json"
PD = RUNTIME / "pd_leases.json"
RULES = RUNTIME / "rules.json"
LINKS = RUNTIME / "links.json"
META = RUNTIME / "meta.json"
TEARDOWN = RUNTIME / "teardown.log"


def _load(path: Path, default):
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _save(path: Path, data) -> None:
    RUNTIME.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def reload_prepare(iface: str) -> None:
    """Clear runtime routes, addresses, and rules without touching PD leases."""
    _save(ROUTES, [])
    _save(ADDRS, [])
    _save(RULES, [])
    meta = _load(META, {"rules_committed": False, "assigned_metrics": {}})
    meta["rules_committed"] = False
    _save(META, meta)


def reset() -> None:
    RUNTIME.mkdir(parents=True, exist_ok=True)
    _save(ROUTES, [])
    _save(ADDRS, [])
    _save(PD, [])
    _save(RULES, [])
    _save(LINKS, {})
    _save(META, {"rules_committed": False, "assigned_metrics": {}})
    TEARDOWN.write_text("", encoding="utf-8")


def log_teardown(step: str) -> None:
    with TEARDOWN.open("a", encoding="utf-8") as fh:
        fh.write(step + "\n")


def teardown_log() -> list[str]:
    if not TEARDOWN.is_file():
        return []
    return [line for line in TEARDOWN.read_text(encoding="utf-8").splitlines() if line]


def link_up(iface: str) -> None:
    links = _load(LINKS, {})
    links[iface] = {"state": "up", "down_ack": True}
    _save(LINKS, links)


def link_down(iface: str) -> None:
    links = _load(LINKS, {})
    links[iface] = {"state": "down", "down_ack": False}
    _save(LINKS, links)
    log_teardown("link_down")


def link_down_ack(iface: str) -> None:
    links = _load(LINKS, {})
    entry = links.get(iface, {"state": "down", "down_ack": False})
    entry["down_ack"] = True
    links[iface] = entry
    _save(LINKS, links)
    log_teardown("link_down_ack")


def link_down_acknowledged(iface: str) -> bool:
    links = _load(LINKS, {})
    return bool(links.get(iface, {}).get("down_ack"))


def assign_metric(iface: str, config_metric: int, bonus: int) -> int:
    meta = _load(META, {"rules_committed": False, "assigned_metrics": {}})
    assigned = int(config_metric) + int(bonus)
    meta.setdefault("assigned_metrics", {})[iface] = assigned
    _save(META, meta)
    return assigned


def get_assigned_metric(iface: str, fallback: int) -> int:
    meta = _load(META, {"assigned_metrics": {}})
    return int(meta.get("assigned_metrics", {}).get(iface, fallback))


def route_add(dst: str, via: str, dev: str, metric: int) -> None:
    routes = _load(ROUTES, [])
    routes.append({"dst": dst, "via": via, "dev": dev, "metric": metric})
    _save(ROUTES, routes)


def route_del_default(dev: str) -> None:
    routes = _load(ROUTES, [])
    routes = [r for r in routes if not (r.get("dst") in {"0.0.0.0/0", "default"} and r.get("dev") == dev)]
    _save(ROUTES, routes)
    log_teardown("route_del_default")


def routes_snapshot() -> list[dict]:
    return list(_load(ROUTES, []))


def addr_add(dev: str, family: str, addr: str, dedupe: bool) -> None:
    addrs = _load(ADDRS, [])
    key = (dev, family, addr)
    if dedupe:
        existing = {(a["dev"], a["family"], a["addr"]) for a in addrs}
        if key in existing:
            return
    addrs.append({"dev": dev, "family": family, "addr": addr})
    _save(ADDRS, addrs)


def addresses_snapshot() -> list[dict]:
    return list(_load(ADDRS, []))


def pd_acquire(iface: str, prefix: str, lease_id: str) -> None:
    leases = _load(PD, [])
    leases.append({"iface": iface, "prefix": prefix, "id": lease_id})
    _save(PD, leases)


def pd_release_iface(iface: str) -> None:
    leases = _load(PD, [])
    leases = [x for x in leases if x.get("iface") != iface]
    _save(PD, leases)
    log_teardown("pd_release")


def pd_snapshot() -> list[dict]:
    return list(_load(PD, []))


def rules_set(entries: list[dict]) -> None:
    _save(RULES, list(entries))


def rules_commit() -> None:
    meta = _load(META, {"rules_committed": False, "assigned_metrics": {}})
    meta["rules_committed"] = True
    _save(META, meta)
    log_teardown("rules_commit")


def rules_committed() -> bool:
    meta = _load(META, {"rules_committed": False})
    return bool(meta.get("rules_committed"))


def rules_snapshot() -> list[dict]:
    return list(_load(RULES, []))


def export_payload(scenario: str, iface: str) -> dict:
    return {
        "scenario": scenario,
        "iface": iface,
        "routes": routes_snapshot(),
        "addresses": addresses_snapshot(),
        "pd_leases": pd_snapshot(),
        "rules": rules_snapshot(),
        "rules_committed": rules_committed(),
        "teardown_log": teardown_log(),
    }
