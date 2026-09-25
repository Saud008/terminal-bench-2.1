# Hotplug contract

Hotplug events in scenario JSON are processed during apply only.

Each event with op add and family inet or inet6 adds an address to the iface in the harness address table.

Duplicate add events with the same (dev, family, addr) triple must be ignored after the first successful add. Burst fixtures rely on deduplication.

The export addresses array lists unique entries in arrival order.
