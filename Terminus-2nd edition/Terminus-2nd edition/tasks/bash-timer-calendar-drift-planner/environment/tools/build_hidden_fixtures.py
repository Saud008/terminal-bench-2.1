#!/usr/bin/env python3
"""Build hidden verifier fixture bundles under /opt/verifier-fixtures/systemd-timer."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path("/opt/verifier-fixtures/systemd-timer")


def write_bundle(path: Path, timer_body: str, dropins: dict[str, str], activation: dict) -> None:
    path.mkdir(parents=True, exist_ok=True)
    name = path.name.replace(".timer.bundle", "")
    (path / f"{name}.timer").write_text(timer_body, encoding="utf-8")
    drop_dir = path / f"{name}.timer.d"
    drop_dir.mkdir(exist_ok=True)
    for fname, body in dropins.items():
        (drop_dir / fname).write_text(body, encoding="utf-8")
    (path / "activation.json").write_text(json.dumps(activation, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)

    write_bundle(
        ROOT / "hidden-persistent.timer.bundle",
        """[Timer]
OnCalendar=*-*-* 04:00:00
Persistent=false
""",
        {
            "05-persistent.conf": "[Timer]\nPersistent=true\n",
            "10-timezone.conf": "[Timer]\nTimezone=Europe/Berlin\n",
        },
        {"last_trigger_utc": "2024-06-01T02:00:00Z", "unit_active_monotonic_usec": 0, "boot_monotonic_usec": 0},
    )

    write_bundle(
        ROOT / "hidden-monotonic.timer.bundle",
        """[Timer]
OnUnitActiveSec=15min
""",
        {},
        {
            "last_trigger_utc": "2024-06-30T12:00:00Z",
            "unit_active_monotonic_usec": 1000000,
            "boot_monotonic_usec": 500000,
        },
    )


if __name__ == "__main__":
    main()
