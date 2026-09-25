#!/usr/bin/env python3
"""Generate deterministic iptables-restore fixtures."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESTORES = ROOT / "fixtures" / "restores"


def write(name: str, content: str) -> None:
    RESTORES.mkdir(parents=True, exist_ok=True)
    (RESTORES / f"{name}.v4").write_text(content.strip() + "\n", encoding="utf-8")


def main() -> None:
    write(
        "core-filter",
        """
*filter
:INPUT DROP [120:48000]
:FORWARD ACCEPT [0:0]
-A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT [44:8192]
-A INPUT -m conntrack --ctstate NEW -j DROP [9:540]
COMMIT
""",
    )
    write(
        "mangle-mark",
        """
*mangle
:PREROUTING ACCEPT [0:0]
-A PREROUTING -m conntrack --ctstate NEW -j CT --notrack
-A PREROUTING -j MARK --set-mark 0x20
COMMIT
*nat
:PREROUTING ACCEPT [0:0]
-A PREROUTING -m mark --mark 0x20/0xff -j DNAT --to-destination 10.0.0.5 [3:180]
-A PREROUTING -m mark --mark 0x40/0xff -j DNAT --to-destination 10.0.0.9 [1:60]
COMMIT
""",
    )
    write(
        "triple-order",
        """
*mangle
:PREROUTING ACCEPT [5:300]
-A PREROUTING -j MARK --set-mark 0x10
COMMIT
*nat
:PREROUTING ACCEPT [2:120]
-A PREROUTING -m mark --mark 0x10/0xff -j DNAT --to-destination 192.168.1.10 [2:120]
COMMIT
*filter
:INPUT DROP [200:90000]
:FORWARD ACCEPT [0:0]
-A INPUT -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT [80:12000]
-A INPUT -m conntrack --ctstate NEW -j DROP [15:900]
COMMIT
""",
    )
    write(
        "counter-heavy",
        """
*filter
:INPUT REJECT [77:15400]
-A INPUT -p tcp --dport 22 -j ACCEPT [31:2480]
COMMIT
*nat
:POSTROUTING ACCEPT [12:720]
-A POSTROUTING -o eth0 -j MASQUERADE [12:720]
COMMIT
""",
    )
    write(
        "ctstate-mix",
        """
*mangle
:INPUT ACCEPT [0:0]
-A INPUT -m conntrack --ctstate INVALID -j DROP
-A INPUT -j CT --notrack
COMMIT
*filter
:INPUT DROP [0:0]
-A INPUT -m conntrack --ctstate ESTABLISHED -j ACCEPT
-A INPUT -m conntrack --ctstate NEW,RELATED -j ACCEPT
-A INPUT -m conntrack --ctstate INVALID -j DROP
COMMIT
""",
    )
    write(
        "nat-only-deps",
        """
*mangle
:PREROUTING ACCEPT [0:0]
-A PREROUTING -j MARK --set-mark 0x5
-A PREROUTING -j MARK --set-mark 0xa
COMMIT
*nat
:PREROUTING ACCEPT [0:0]
-A PREROUTING -m mark --mark 0x5/0xff -j DNAT --to-destination 10.1.0.2
-A PREROUTING -m mark --mark 0xa/0xff -j DNAT --to-destination 10.1.0.3
-A PREROUTING -m mark --mark 0xf/0xff -j DNAT --to-destination 10.1.0.4
COMMIT
""",
    )

    seeds = {
        "restores": [
            "core-filter",
            "mangle-mark",
            "triple-order",
            "counter-heavy",
            "ctstate-mix",
            "nat-only-deps",
        ],
        "seeds": ["1", "7", "11", "seed-a", "seed-b"],
    }
    (ROOT / "fixtures" / "seeds.json").write_text(
        json.dumps(seeds, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
