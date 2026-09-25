# Archive fixture catalog

Bundled archives under /app/fixtures/archives/:

| Stem | Purpose |
|------|---------|
| alpha | Continuous timeline 1 segments 1-5 |
| gap | Missing segment 3 on timeline 1 |
| timeline-switch | Timeline 1 segments, 00000002.history, timeline 2 segments |
| partial-block | Segment 4 exists only as .partial |
| shuffle-label | backup_label with extra whitespace on START TIME |

Hidden archives may appear under /opt/verifier-fixtures/wal-archives/ with non-bundled timeline ids and alternate segment-clock.json under /opt/verifier-fixtures/wal-config/ when TB3_CLOCK_ROOT is set.
