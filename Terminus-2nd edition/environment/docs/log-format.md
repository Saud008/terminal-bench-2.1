# Amavis log format

Release parsing reads a single syslog line per request. Extract fields using these labels:

| Field | Pattern |
|-------|---------|
| Quarantine-ID | Quarantine-ID: TOKEN |
| Queue-ID | Queue-ID: TOKEN |

The quarantine id used for spool file names and ledger keys is the Quarantine-ID token, not Queue-ID. Both fields may appear on the same line; Queue-ID is stored in ledger entries for audit only.

Example shape:

Mar 10 12:00:01 mail amavis[4242]: (4242-01) Blocked SPAM, Queue-ID: AAA11101, Quarantine-ID: 04Rx-0001-sp, Hits: 7.1
