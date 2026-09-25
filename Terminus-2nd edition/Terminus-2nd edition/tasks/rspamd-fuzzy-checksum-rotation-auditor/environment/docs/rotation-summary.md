# Rotation summary

Summary JSON fields:

- schema: 1
- key_epoch: from manifest
- checksum_algo_id: from manifest
- mails_processed: count of mails.tsv data rows processed
- unique_shingles: count of distinct hash values in fuzzy_hashes after the run
- total_shingle_rows: count of all fuzzy_hashes rows (includes duplicate hashes across mails)
- console_lines_matched: verified console dump lines
- dry_run: boolean

unique_shingles must use SELECT COUNT(DISTINCT hash) semantics, not total row count.

Dry-run still writes summary JSON but must not write rotation-run.json.

Dry-run unique_shingles: because --dry-run skips sqlite mutation, compute unique_shingles from the in-memory or streaming shingle hash set produced during the rotate pass. The count must equal the number of distinct lowercase hash digests that would be inserted, matching SELECT COUNT(DISTINCT hash) on the post-run index. Do not substitute total_shingle_rows or count rows that were never emitted.

Verifier runs may write additional summary-out paths under /app/output including hidden-near.json, hidden-upper.json, hidden-salt.json, and rollback-fail.json for hidden or negative-path scenarios.

rotation-run.json on success mirrors summary counters plus completed_at epoch seconds.
