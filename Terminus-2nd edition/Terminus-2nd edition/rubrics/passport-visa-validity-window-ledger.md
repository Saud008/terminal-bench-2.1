# Platform rubric — passport-visa-validity-window-ledger

**Task folder:** tasks/passport-visa-validity-window-ledger/
**Upload:** copy lines below into Snorkel platform rubric form (not in zip).

Agent treats passport expiry_date as inclusive on the reference inspection day, +3
Agent requires full visa valid_from and valid_to span inside passport issue and expiry bounds, +3
Agent sums cumulative stay days through reference_date including open entry stamps, +3
Agent applies federal max_stay cap over port scope when both rules exist, +3
Agent suppresses visa evaluation when linked passport is revoked, +3
Agent blocks entry when watchlist hold is active for the holder, +2
Agent increments eval_pass before writing validity-decisions.json eval_pass field, +2
Agent refuses commit-ledger when eval_pass is zero, +2
Agent inserts ledger rows once per eval_pass on repeated commit-ledger runs, +3
Agent writes ingest snapshot at /app/state/manifest-snapshot.json during import-manifest, +2
Agent rebuilds /app/bin/borderdocctl after policy changes and validates the CLI, +2
Agent loads verifier scenarios from --fixture-dir when provided, +2
Agent consumes already-remapped seeded fixture IDs without remapping again, +2
Agent treats passport expiry as exclusive on the expiry calendar day, -3
Agent validates visa only on reference day without span containment check, -3
Agent skips open stamp tail days when exit_date is empty, -3
Agent prefers port max_stay over federal precedence, -3
Agent ignores passport revocation when evaluating linked visas, -3
Agent treats active watchlist holds as non-blocking, -2
Agent duplicates SQLite ledger rows on second commit-ledger invocation, -3
