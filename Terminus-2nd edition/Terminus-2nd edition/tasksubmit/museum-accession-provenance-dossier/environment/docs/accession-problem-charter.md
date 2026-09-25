# Accession problem charter

This task is a **games** museum accession vault playtest for sealed dossier win conditions, not an MLflow run-lineage or experiment-pin binding workflow and not a Python package rebuild or pytest harness. The playfield keeps vault admission, compose-align gates, register supersession, and sealed dossier export aligned over accession objects: custody transfer graphs, exhibition loan calendars, rights restriction stacks, restoration chronology, and duplicate accession-id reconciliation.

Observable behaviors the verifier rejects when incomplete:

1. Custody lineage is emitted as alphabetical party lists, `"A to B"` edge strings, or other formats instead of the transfer_date-ordered party-name list (earliest `from_party`, then each `to_party`; same-date rows keep archive input order) defined in custody-lineage-contract.md.
2. Exhibition loans that overlap in inclusive calendar windows are absent from loan_conflicts, missed return_by gates relative to as_of_date stay unreported, repeated conflicts are collapsed, or loan_conflicts are not emitted in the deterministic missed-then-overlap order from loan-window-policy.md.
3. Rights restriction selection retains higher precedence integers instead of stricter (lower) precedence among still-valid unexpired rows.
4. Restoration timelines sort newest-first rather than ascending event_date history, or same-day rows ignore the technician and notes tie-breaks.
5. Object rows that share titles but carry distinct accession_id values are coalesced, while true duplicate accession_id rows remain unflagged, or shadow_accession_ids omit the repeated [aid] * n length required once per duplicate object.
6. Dossier publish elides loan_conflicts, duplicate_conflicts, and conflict_count even when align already computed them.
7. Vault archive_seq remains static across repeated vault load of the same seed, breaking cross-run persistence checks.
8. A mismatched archive_name or corrupt prior snapshot is silently admitted.
9. Publish accepts an active row aligned from an older archive_seq after the vault is reloaded under the same seed and archive name, or ignores a post-align snapshot byte change that breaks snapshot_digest.

The playtest succeeds only when the published dossier JSON under /app/output/ matches independent custody, loan-calendar, rights-stack, restoration, and accession-id reconciliation math for those museum gate behaviors.
