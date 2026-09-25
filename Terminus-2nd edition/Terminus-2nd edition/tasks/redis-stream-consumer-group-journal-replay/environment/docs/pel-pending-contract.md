# PEL pending contract

Consumer pending entries are created on XREADGROUP. They remain in the group PEL until XACK removes them.

The staging pending_log is an audit trail of when a message left the visible pending set during replay. A pending_log row must not appear until the XACK event for that message id has been replayed. The ack_seq field must reference that XACK seq, not the earlier XREADGROUP seq.

Tests compare pending_log ordering against an independent reference replay.
