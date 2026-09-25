"""Independent reference middleware chain simulation."""

from __future__ import annotations

from typing import Any


def merge_plugins(service_plugins: list[dict], route_plugins: list[dict]) -> list[dict]:
    by_name: dict[str, dict] = {}
    order: list[str] = []
    for pl in service_plugins:
        name = pl["name"]
        if name not in by_name:
            order.append(name)
        by_name[name] = pl
    for pl in route_plugins:
        name = pl["name"]
        if name not in by_name:
            order.append(name)
        if name in by_name and name == "response-transformer":
            by_name[name] = _merge_transformer(by_name[name], pl)
        else:
            by_name[name] = pl
    return [by_name[n] for n in order]


def _merge_transformer(base: dict, overlay: dict) -> dict:
    def header_map(pl: dict) -> dict[str, str]:
        cfg = pl.get("config") or {}
        out: dict[str, str] = {}
        add = cfg.get("add") or {}
        for line in add.get("headers") or []:
            key, val = line.split(":", 1)
            out[key.strip()] = val.strip()
        return out

    merged = header_map(base)
    merged.update(header_map(overlay))
    headers = [f"{k}:{v}" for k, v in merged.items()]
    return {"name": "response-transformer", "config": {"add": {"headers": headers}}}


def run_chain(
    plugins: list[dict],
    *,
    rate_counts: dict[str, int],
    rate_key: str,
    limit: int,
) -> tuple[bool, dict[str, str], int]:
    phase_order = ["jwt", "rate-limiting", "response-transformer"]
    by_name = {pl["name"]: pl for pl in plugins}
    ordered = [by_name[name] for name in phase_order if name in by_name]
    headers: dict[str, str] = {}
    blocked = False
    code = 200
    for pl in ordered:
        name = pl["name"]
        cfg: dict[str, Any] = pl.get("config") or {}
        if name == "rate-limiting":
            minute = int(cfg.get("minute", limit))
            rate_counts[rate_key] = rate_counts.get(rate_key, 0) + 1
            count = rate_counts[rate_key]
            headers["X-RateLimit-Limit"] = str(minute)
            headers["X-RateLimit-Remaining"] = str(max(0, minute - count))
            if count > minute:
                blocked = True
                code = 429
                break
        elif name == "response-transformer":
            add = cfg.get("add") or {}
            for line in add.get("headers") or []:
                key, val = line.split(":", 1)
                headers[key.strip()] = val.strip()
    return blocked, headers, code
