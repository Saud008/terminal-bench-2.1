# Sequence reset gate

When a logon row has 35=A and 141=Y, replay resets the expected MsgSeqNum baseline for that session to zero. The next execution report for the session may use MsgSeqNum 1 even if earlier rows had higher sequence numbers.

Replay rejects MsgSeqNum less than or equal to the last seen sequence for the session unless a reset occurred immediately before the row. ingest records reset_seq true on staging events sourced from reset logons,
