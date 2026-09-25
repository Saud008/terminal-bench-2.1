"""AS-path and relationship feature extraction."""
from __future__ import annotations

from typing import Any


FEATURE_NAMES = [
    "path_len",
    "origin_asn",
    "private_origin",
    "reserved_hop",
    "unique_asn_ratio",
    "valley_count",
    "peer_peer_transit",
    "first_hop_customer",
]


def _is_private(asn: int) -> bool:
    return 64512 <= asn <= 65534


def _is_reserved(asn: int) -> bool:
    return 64496 <= asn <= 64511


def extract_features(example: dict[str, Any], relationships: dict[str, str]) -> list[float]:
    path = list(example.get("as_path") or [])
    path_len = float(len(path))
    origin = float(path[-1]) if path else 0.0
    private_origin = 1.0 if path and _is_private(path[-1]) else 0.0
    reserved_hop = 1.0 if any(_is_reserved(a) for a in path) else 0.0
    unique_asn_ratio = (len(set(path)) / path_len) if path_len > 0 else 0.0

    valley = 0.0
    peer_peer = 0.0
    for i in range(len(path) - 1):
        a, b = path[i], path[i + 1]
        role = relationships.get(f"{a}|{b}")
        if role == "peer":
            peer_peer = 1.0
        if i + 2 < len(path):
            c = path[i + 2]
            if role == "provider" and relationships.get(f"{b}|{c}") == "customer":
                valley += 1.0

    first_hop_customer = 0.0
    if len(path) >= 2 and relationships.get(f"{path[0]}|{path[1]}") == "customer":
        first_hop_customer = 1.0

    return [
        path_len,
        origin,
        private_origin,
        reserved_hop,
        unique_asn_ratio,
        valley,
        peer_peer,
        first_hop_customer,
    ]
