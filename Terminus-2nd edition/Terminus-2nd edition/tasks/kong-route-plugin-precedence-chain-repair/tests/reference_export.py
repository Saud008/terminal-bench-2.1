"""Independent reference for OpenAPI staging and JWT scope checks."""

from __future__ import annotations

from typing import Any

from reference_chain import merge_plugins


def staged_headers(service_plugins: list[dict], route_plugins: list[dict]) -> set[str]:
    headers: set[str] = set()
    for pl in merge_plugins(service_plugins, route_plugins):
        name = pl["name"]
        cfg: dict[str, Any] = pl.get("config") or {}
        if name == "response-transformer":
            add = cfg.get("add") or {}
            for line in add.get("headers") or []:
                key, _ = line.split(":", 1)
                headers.add(key.strip())
        if name == "rate-limiting":
            headers.add("X-RateLimit-Limit")
            headers.add("X-RateLimit-Remaining")
    return headers


def scope_allows(consumer_scopes: list[str], route_scope_tags: list[str], route_tags: list[str]) -> bool:
    if not route_scope_tags:
        return True
    granted = set(consumer_scopes)
    return all(tag in granted for tag in route_scope_tags)
