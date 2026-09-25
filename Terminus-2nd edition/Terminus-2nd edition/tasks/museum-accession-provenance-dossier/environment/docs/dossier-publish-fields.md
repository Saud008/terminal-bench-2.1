# Dossier dossier publish fields

On this games museum accession playtest, publish dossier seals compliance JSON with seed, archive, focus_accession_id, custody_lineage, active_restrictions, restoration_timeline, loan_conflicts, duplicate_conflicts, conflict_count, summary, audit_digest.

custody_lineage is an ordered JSON array of party name strings for the focus accession: earliest `from_party`, then each `to_party` in `transfer_date` ascending order; same-date rows keep archive input order. Each element is one custodian name, not an `"A to B"` edge string. See custody-lineage-contract.md.

conflict_count = len(loan_conflicts) + len(duplicate_conflicts).

Each loan_conflicts row is an object with exactly two keys: accession_id (the focus accession id string) and reason (missed_return_window or overlapping_loan). Do not add borrower, loan_start, loan_end, return_by, pair indexes, or other diagnostic fields. The verifier compares loan_conflicts with full JSON equality, so richer rows fail even when reason codes and ordering are correct. Emission order and multiplicity follow loan-window-policy.md.

summary is an object with exactly these five integer fields: custody_depth, restriction_count, restoration_count, loan_conflict_count, and duplicate_count. Do not add extra summary keys. The verifier compares summary with full JSON equality against that five-field shape.

duplicate_conflicts primary accession_id must be an accession_id. Only group objects sharing the same accession_id.

shadow_accession_ids must list the shared accession id once per duplicate object (length n, same id repeated). That matches the verifier [aid] * n rule. Grouping by accession_id alone is not enough: emitting a unique-id set, n-1 shadows, or any other length still fails the duplicate tests.

audit_digest = sha256 of {"custody_depth":N,"duplicate_count":N,"lineage":[...],"loan_conflicts":N} with lineage JSON array. The loan_conflicts value in that hash payload is the integer summary.loan_conflict_count, not the loan_conflicts array.

Callers pass --output under /app/output/, for example /app/output/partial.json when probing publish without a prior align.
