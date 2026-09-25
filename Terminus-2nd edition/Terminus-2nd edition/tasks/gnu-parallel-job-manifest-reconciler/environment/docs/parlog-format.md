# .par profiler log format

One file per completed job slot, named `*.par` under the run's `par/` directory.

Each file is UTF-8 text with `key=value` lines (no spaces around `=`):

| Key | Meaning |
|-----|---------|
| `seq` | Job sequence number matching joblog column Seq |
| `slot` | GNU parallel slot id (integer ≥ 1) |
| `exit` | Authoritative exit code from the wrapper (overrides joblog Exitval) |
| `utime_jiffies` | User CPU time from `/proc` stat field 14 |
| `stime_jiffies` | System CPU time from `/proc` stat field 15 |
| `wall_sec` | Wall-clock seconds for the job |
| `start_epoch` | Start time (epoch seconds, fractional allowed) |
| `end_epoch` | End time (epoch seconds, fractional allowed) |

`USER_HZ` for jiffies conversion is **100** (documented here and used by export).

Peak concurrency is **not** `MAX(slot)`; see `/app/docs/invariants.md`.
