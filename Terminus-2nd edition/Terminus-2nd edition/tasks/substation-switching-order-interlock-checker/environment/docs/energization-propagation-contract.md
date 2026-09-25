# Energization propagation

Source buses listed in energized_sources start energized at procedure start.

After each switching step, recompute energized buses:

1. Start with energized_sources energized.
2. For each closed breaker, if either connected bus is energized, both buses become energized.
3. Repeat closure until no new buses energize.

Opening a breaker may de-energize buses no longer connected to any source through closed breakers. Recompute from scratch after every step; do not retain stale energization.
