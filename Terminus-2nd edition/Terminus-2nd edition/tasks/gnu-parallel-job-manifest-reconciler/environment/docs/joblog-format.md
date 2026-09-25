# GNU parallel --joblog format

Tab-separated values. First line is a header row and is ignored.

| Column | Name | Meaning |
|--------|------|---------|
| 1 | Seq | Job sequence number (integer, unique) |
| 2 | Host | Hostname |
| 3 | Starttime | Epoch seconds with fractional part |
| 4 | JobRuntime | Wall seconds reported by GNU parallel |
| 5 | Send | Bytes sent (ignored) |
| 6 | Receive | Bytes received (ignored) |
| 7 | Exitval | Exit code from GNU parallel |
| 8 | Signal | Signal number (ignored) |
| 9+ | Command | Remaining columns joined as the command string |

Reconcile inserts one row per data line using the gawk helpers in `/app/lib/joblog.sh`. When a matching `.par` exists for the same `seq`, profiler fields override joblog timing and exit metadata in the database.
