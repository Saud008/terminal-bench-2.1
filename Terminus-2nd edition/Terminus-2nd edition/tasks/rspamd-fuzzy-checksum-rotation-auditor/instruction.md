Security operators use the rspamd fuzzy storage audit driver at /app/bin/rspamd-fuzzy-audit to rotate fuzzy checksum indexes over mail corpora and publish contract-compliant rotation summaries. Complete the Bash, awk, and sqlite modules documented in /app/docs/spec.md so the rotate subcommand implements the pipeline together with /app/docs/shingle-window.md, /app/docs/key-epoch-rotation.md, /app/docs/fuzzy-index.md, /app/docs/console-dump.md, /app/docs/shingle-snapshot-contract.md, and /app/docs/rotation-summary.md.

## Expected outputs

Every rotate run (bundled fixtures, generated manifests, and hidden corpora when TB3_FIXTURES_DIR points at an absolute directory) must produce artifacts that match the referenced contracts:

- Rotation summary JSON at the --summary-out path with schema, key_epoch, checksum_algo_id, mails_processed, unique_shingles, total_shingle_rows, console_lines_matched, and dry_run (rotation-summary.md).
- Shingle snapshot at /app/state/shingle-snapshot.json before any sqlite mutation, including mails listed in mails.tsv sequence, mail_digest, and epoch_salt (shingle-snapshot-contract.md).
- On non-dry-run success: sqlite rows in /app/state/fuzzy-index.db for each emitted shingle and /app/state/rotation-run.json mirroring summary counters plus completed_at.
- On console verification failure after index mutation: /app/state/rotation-rollback.json with reason console_mismatch and a non-zero exit status.

Dry-run (--dry-run) still writes the shingle snapshot and summary JSON but must not mutate sqlite, write rotation-run.json, or leave rollback markers.

## Success criteria

Shingle normalization and window emission, epoch and algorithm rotation, lowercase console hash verification, summary counter semantics, and state file lifecycle must all agree with the cited docs. Hidden fixture runs may set RF_EPOCH_SALT_SUFFIX to append extra salt bytes during snapshot digest computation (key-epoch-rotation.md).

## Observable symptoms when behavior diverges

The following output-level mismatches indicate the pipeline is not yet contract-compliant. Authoritative field definitions and algorithms remain in /app/docs/:

- unique_shingles equals total_shingle_rows when duplicate shingles appear across different mails, instead of counting distinct hash values only.
- console_lines_matched differs from unique_shingles even though every console dump line should match an indexed hash for the active epoch and algorithm.
- Console verification fails because dump lines use mixed-case hex while the index stores lowercase digests, or because epoch or algorithm values on a line do not match the rotated index.
- Shingle snapshot mails includes .eml files not listed in mails.tsv, or mail_digest does not match the manifest mail_id sequence.
- Dry-run leaves rows in fuzzy-index.db, writes rotation-run.json, or reports unique_shingles using total row count instead of distinct-hash semantics.
- A failed console verify after sqlite mutation exits zero or omits rotation-rollback.json.

The environment has no outbound network access. Do not edit /app/docs/, /app/fixtures/, or /tests/.

Verification harness replay uses fuzzy_contract_math with hashlib and sqlite3 against the contracts cited above (see /app/docs/spec.md).
