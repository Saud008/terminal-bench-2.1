#!/usr/bin/env python3
"""Generate NLDM route dump fixtures for nlctl task."""

from __future__ import annotations

import hashlib
import ipaddress
import struct
from pathlib import Path

OUT = Path(__file__).resolve().parent / "environment" / "fixtures" / "dumps"

RTA_OIF = 4
RTA_GATEWAY = 5
RTA_PRIORITY = 6
RTA_MULTIPATH = 8
RTA_TABLE = 15
RTA_METRICS = 39
RTA_NH_ID = 52

AF_INET = 2
AF_INET6 = 10


def attr_u32(atype: int, value: int) -> bytes:
    payload = struct.pack("<I", value)
    return struct.pack("<HH", atype, len(payload)) + payload


def attr_gateway(family: int, addr: str) -> bytes:
    ip = ipaddress.ip_address(addr)
    payload = ip.packed
    return struct.pack("<HH", RTA_GATEWAY, len(payload)) + payload


def encode_multipath(hops: list[dict]) -> bytes:
    blob = struct.pack("<B", len(hops))
    for hop in hops:
        gw_family = hop.get("gw_family", 0)
        parts = [struct.pack("<iB", hop["ifindex"], hop["weight_raw"]), struct.pack("<B", gw_family)]
        if gw_family:
            ip = ipaddress.ip_address(hop["gateway"])
            parts.append(ip.packed)
        blob += b"".join(parts)
    return struct.pack("<HH", RTA_MULTIPATH, len(blob)) + blob


def encode_metrics(entries: list[tuple[int, int]]) -> bytes:
    blob = struct.pack("<B", len(entries))
    for mtype, value in entries:
        blob += struct.pack("<HI", mtype, value)
    return struct.pack("<HH", RTA_METRICS, len(blob)) + blob


def encode_route(family: int, table_id: int, dst: str, plen: int, attrs: list[bytes]) -> bytes:
    ip = ipaddress.ip_address(dst)
    addr = ip.packed
    body = struct.pack("<BI", family, table_id) + struct.pack("<B", plen) + addr
    body += struct.pack("<H", len(attrs))
    body += b"".join(attrs)
    return body


def encode_dump(seed: str, routes: list[bytes]) -> bytes:
    seed_b = seed.encode("utf-8")
    header = b"NLDM" + struct.pack("<HB", 1, len(seed_b)) + seed_b + struct.pack("<I", len(routes))
    return header + b"".join(routes)


def write(name: str, data: bytes) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    path.write_bytes(data)
    print(name, hashlib.sha256(data).hexdigest(), len(data))


def main() -> None:
    write(
        "001-multipath-v4.bin",
        encode_dump(
            "nl-seed-6",
            [
                encode_route(
                    AF_INET,
                    254,
                    "10.0.0.0",
                    8,
                    [
                        attr_u32(RTA_PRIORITY, 100),
                        encode_multipath(
                            [
                                {"ifindex": 2, "weight_raw": 5, "gw_family": AF_INET, "gateway": "192.168.1.1"},
                                {"ifindex": 3, "weight_raw": 9, "gw_family": AF_INET, "gateway": "192.168.1.2"},
                            ]
                        ),
                    ],
                )
            ],
        ),
    )

    write(
        "002-nh-id-scope.bin",
        encode_dump(
            "nl-seed-6",
            [
                encode_route(
                    AF_INET,
                    254,
                    "172.16.0.0",
                    12,
                    [
                        encode_multipath(
                            [
                                {"ifindex": 10, "weight_raw": 3, "gw_family": AF_INET, "gateway": "10.10.0.1"},
                                {"ifindex": 11, "weight_raw": 4, "gw_family": AF_INET, "gateway": "10.10.0.2"},
                            ]
                        )
                    ],
                ),
                encode_route(
                    AF_INET,
                    254,
                    "172.17.0.0",
                    12,
                    [
                        encode_multipath(
                            [
                                {"ifindex": 20, "weight_raw": 6, "gw_family": AF_INET, "gateway": "10.20.0.1"},
                                {"ifindex": 21, "weight_raw": 7, "gw_family": AF_INET, "gateway": "10.20.0.2"},
                            ]
                        )
                    ],
                ),
            ],
        ),
    )

    write(
        "003-v6-gateway.bin",
        encode_dump(
            "nl-seed-6",
            [
                encode_route(
                    AF_INET6,
                    254,
                    "2001:db8::",
                    32,
                    [
                        attr_gateway(AF_INET6, "2001:db8:1::1"),
                        attr_u32(RTA_OIF, 8),
                    ],
                )
            ],
        ),
    )

    write(
        "004-table-override.bin",
        encode_dump(
            "nl-seed-6",
            [
                encode_route(
                    AF_INET,
                    100,
                    "192.168.0.0",
                    16,
                    [
                        attr_u32(RTA_TABLE, 200),
                        attr_gateway(AF_INET, "192.168.0.1"),
                        attr_u32(RTA_OIF, 4),
                        attr_u32(RTA_NH_ID, 42),
                    ],
                )
            ],
        ),
    )

    write(
        "005-metrics-nested.bin",
        encode_dump(
            "nl-seed-6",
            [
                encode_route(
                    AF_INET,
                    254,
                    "203.0.113.0",
                    24,
                    [
                        attr_gateway(AF_INET, "203.0.113.1"),
                        attr_u32(RTA_OIF, 5),
                        encode_metrics([(2, 1500), (5, 1440)]),
                    ],
                )
            ],
        ),
    )

    write(
        "006-mixed-dual.bin",
        encode_dump(
            "nl-seed-6",
            [
                encode_route(
                    AF_INET,
                    254,
                    "198.51.100.0",
                    24,
                    [attr_gateway(AF_INET, "198.51.100.1"), attr_u32(RTA_OIF, 6)],
                ),
                encode_route(
                    AF_INET6,
                    254,
                    "fd00::",
                    64,
                    [attr_gateway(AF_INET6, "fd00::1"), attr_u32(RTA_OIF, 7)],
                ),
            ],
        ),
    )

    write(
        "007-alt-seed.bin",
        encode_dump(
            "nl-seed-2",
            [
                encode_route(
                    AF_INET,
                    254,
                    "10.0.0.0",
                    8,
                    [
                        attr_u32(RTA_PRIORITY, 100),
                        encode_multipath(
                            [
                                {"ifindex": 2, "weight_raw": 5, "gw_family": AF_INET, "gateway": "192.168.1.1"},
                                {"ifindex": 3, "weight_raw": 9, "gw_family": AF_INET, "gateway": "192.168.1.2"},
                            ]
                        ),
                    ],
                )
            ],
        ),
    )

    write(
        "008-v6-multipath.bin",
        encode_dump(
            "nl-seed-9",
            [
                encode_route(
                    AF_INET6,
                    254,
                    "2001:db8::",
                    48,
                    [
                        encode_multipath(
                            [
                                {
                                    "ifindex": 3,
                                    "weight_raw": 4,
                                    "gw_family": AF_INET6,
                                    "gateway": "2001:db8:1::1",
                                },
                                {
                                    "ifindex": 4,
                                    "weight_raw": 6,
                                    "gw_family": AF_INET6,
                                    "gateway": "2001:db8:2::2",
                                },
                            ]
                        )
                    ],
                )
            ],
        ),
    )

    write(
        "009-table-multipath.bin",
        encode_dump(
            "nl-seed-6",
            [
                encode_route(
                    AF_INET,
                    100,
                    "10.64.0.0",
                    16,
                    [
                        attr_u32(RTA_TABLE, 220),
                        encode_multipath(
                            [
                                {"ifindex": 12, "weight_raw": 8, "gw_family": AF_INET, "gateway": "10.64.0.1"},
                                {"ifindex": 13, "weight_raw": 10, "gw_family": AF_INET, "gateway": "10.64.0.2"},
                            ]
                        ),
                    ],
                )
            ],
        ),
    )

    write(
        "010-three-hop-priority.bin",
        encode_dump(
            "nl-seed-6",
            [
                encode_route(
                    AF_INET,
                    100,
                    "10.80.0.0",
                    16,
                    [
                        attr_u32(RTA_PRIORITY, 500),
                        attr_u32(RTA_TABLE, 190),
                        encode_multipath(
                            [
                                {"ifindex": 5, "weight_raw": 5, "gw_family": AF_INET, "gateway": "10.80.0.1"},
                                {"ifindex": 6, "weight_raw": 9, "gw_family": AF_INET, "gateway": "10.80.0.2"},
                                {"ifindex": 7, "weight_raw": 3, "gw_family": AF_INET, "gateway": "10.80.0.3"},
                            ]
                        ),
                    ],
                )
            ],
        ),
    )

    write(
        "011-v6-dst-minimal.bin",
        encode_dump(
            "nl-seed-6",
            [
                encode_route(
                    AF_INET6,
                    254,
                    "2001:db8:0:0:0:0:0:1",
                    64,
                    [
                        attr_gateway(AF_INET6, "2001:db8::1"),
                        attr_u32(RTA_OIF, 9),
                    ],
                )
            ],
        ),
    )

    write(
        "012-route-message-order.bin",
        encode_dump(
            "nl-seed-6",
            [
                encode_route(
                    AF_INET,
                    300,
                    "10.30.0.0",
                    16,
                    [attr_gateway(AF_INET, "10.30.0.1"), attr_u32(RTA_OIF, 30)],
                ),
                encode_route(
                    AF_INET,
                    100,
                    "10.40.0.0",
                    16,
                    [attr_gateway(AF_INET, "10.40.0.1"), attr_u32(RTA_OIF, 40)],
                ),
            ],
        ),
    )

    write(
        "013-dual-multipath-nh-chain.bin",
        encode_dump(
            "nl-seed-13",
            [
                encode_route(
                    AF_INET,
                    254,
                    "10.90.0.0",
                    16,
                    [
                        encode_multipath(
                            [
                                {"ifindex": 21, "weight_raw": 7, "gw_family": AF_INET, "gateway": "10.90.0.1"},
                                {"ifindex": 22, "weight_raw": 14, "gw_family": AF_INET, "gateway": "10.90.0.2"},
                            ]
                        )
                    ],
                ),
                encode_route(
                    AF_INET,
                    254,
                    "10.91.0.0",
                    16,
                    [
                        encode_multipath(
                            [
                                {"ifindex": 23, "weight_raw": 5, "gw_family": AF_INET, "gateway": "10.91.0.1"},
                                {"ifindex": 24, "weight_raw": 11, "gw_family": AF_INET, "gateway": "10.91.0.2"},
                            ]
                        )
                    ],
                ),
            ],
        ),
    )

    write(
        "014-multipath-metrics-isolated.bin",
        encode_dump(
            "nl-seed-14",
            [
                encode_route(
                    AF_INET,
                    254,
                    "10.95.0.0",
                    16,
                    [
                        encode_metrics([(2, 1500), (5, 1440)]),
                        encode_multipath(
                            [
                                {"ifindex": 31, "weight_raw": 8, "gw_family": AF_INET, "gateway": "10.95.0.1"},
                                {"ifindex": 32, "weight_raw": 12, "gw_family": AF_INET, "gateway": "10.95.0.2"},
                            ]
                        ),
                    ],
                )
            ],
        ),
    )


if __name__ == "__main__":
    main()
