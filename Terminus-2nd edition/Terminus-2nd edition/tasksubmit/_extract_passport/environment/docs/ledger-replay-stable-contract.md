# Ledger replay-stable contract

commit-ledger inserts one ledger row per decision for the current eval_pass. Re-running commit-ledger with the same eval_pass must not insert duplicate ledger rows or change validity-decisions.json from score-validity.

Second seal with unchanged eval_pass yields identical ledger row count and manifest digest.
