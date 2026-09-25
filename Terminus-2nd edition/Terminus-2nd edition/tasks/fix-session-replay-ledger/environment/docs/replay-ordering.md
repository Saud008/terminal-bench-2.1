# Replay ordering

When multiple execution reports appear in one session file, replay order is **not** file offset order.

Sort all ingested messages by:

1. `SendingTime` (tag 52) ascending (lexicographic `YYYYMMDD-HH:MM:SS` or `YYYYMMDD-HH:MM:SS.sss`)
2. `ClOrdID` (tag 11) ascending
3. `ExecID` (tag 17) ascending

Cancel/replace chains must be applied in this order even when the capture file stores messages out of order.
