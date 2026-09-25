# Signal aspect policy

When aspect equals restrict, the signal blocks train movement through the signal block and every block in that block protected zone during [start_min, end_min).

A reservation conflicts with a restrict signal when the reservation half-open window overlaps the signal window and the reservation blocks intersect the signal protected zone from zone_map.

Signals with aspect clear or stop do not emit signal_restrict conflict rows.
