# Schema bump abort

Each record may append names to the schema epoch via `schema_marks`. A record
also carries a `commit` flag.

A snapshot of the graph **and** the current schema-mark set is taken before
the record runs. The record's edits are evaluated and its `schema_marks` are
appended as usual, but the record only takes effect when `commit` is true.

When `commit` is false (or absent) the record **aborts**: the graph is rolled
back to the pre-record snapshot and the schema-mark set is restored to its
pre-record contents. An aborted record therefore leaves no writes and no
schema marks behind, and its winning edits do not count toward
`applied_edits`. Its outcome lines are still reported for the record.

The sealed atlas field `schema_marks` is the final schema-mark set sorted
ascending, containing only marks from committed records.
