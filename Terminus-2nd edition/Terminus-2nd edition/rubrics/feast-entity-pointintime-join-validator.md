# Platform rubric — feast-entity-pointintime-join-validator

**Task folder:** tasks/feast-entity-pointintime-join-validator/
**Written:** 2026-07-27T16:30:00Z
**Upload:** copy lines below into Snorkel platform rubric form (not in zip).

Agent implements point-in-time join selection with event_ts less than or equal to as_of, +3
Agent enforces TTL window width using inclusive as_of minus event_ts bound, +3
Agent matches composite entity keys on every declared key column, +3
Agent scopes joins to active_partition from as_of_entries per backfill contract, +2
Agent deduplicates duplicate event timestamps keeping highest seq before join, +3
Agent compares online and offline values with three-decimal rounding parity, +2
Agent persists parity_runs rows and parity_rows into /app/work/parity.db, +2
Agent exports summary JSON with canonical audit_digest over summary object, +2
Agent honors TB3_TTL_BIAS when validating hidden scenarios, +2
Agent increments ingest_seq across repeated load calls to staging snapshot, +1
Agent validates join resets SQLite parity tables between scenario runs, +2
Agent materializes seed-scoped entity identifiers into staging events, +2
Agent writes export report under the caller-provided /app/output path, +1
Agent uses strict less-than for point-in-time event_ts breaking as_of boundary rows, -3
Agent applies strict less-than TTL window excluding boundary events, -3
Agent matches composite entities on first key column only ignoring device or session, -3
Agent ignores active_partition allowing cross-partition backfill contamination, -3
Agent keeps lowest seq on duplicate timestamps discarding newer events, -2
Agent compares raw float string formatting instead of three-decimal parity rounding, -2
Agent edits the decoy package on the load validate export path, -1
