from __future__ import annotations

from typing import Any


def class_retention_days(cluster: dict[str, Any], class_name: str) -> int:
    _ = class_name
    return int(cluster.get("default_retention_days", 0))


def class_by_name(cluster: dict[str, Any], name: str) -> tuple[dict[str, Any], bool]:
    for sc in cluster.get("storage_classes", []):
        if sc["name"] == name:
            return sc, True
    return {}, False
