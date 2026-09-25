# Fixture catalog

| File | Role |
|------|------|
| `baseline.bin` | 8192-byte mixed pattern |
| `repeat.bin` | Periodic runs for boundary probes |
| `sparse.bin` | Mostly zero with short bursts |
| `resume.bin` | 16384-byte structured blob for checkpoint resume |
| `boundary.bin` | 12288-byte ramp for multi-phase resume window sensitivity |
| `oddleaf.bin` | 4300-byte ramp tuned for odd-level merkle pairing checks |

Seeds in `/app/config/seeds.json`.
