# Fuzzy index (sqlite)

Database path: /app/state/fuzzy-index.db

The rotate pipeline uses the sqlite3 command-line tool and Python sqlite3 bindings when mutating fuzzy_hashes during non-dry-run passes.

Table fuzzy_hashes:

- hash TEXT NOT NULL
- mail_id TEXT NOT NULL
- shingle TEXT NOT NULL
- key_epoch INTEGER NOT NULL
- checksum_algo_id INTEGER NOT NULL

Primary key (hash, mail_id, shingle).

During rotate, after epoch rotation, insert one row per emitted shingle for each processed mail. The hash column stores the lowercase 16-hex digest from shingle-window.md.

Summary unique_shingles counts distinct hash values across all rows after the run. total_shingle_rows counts rows (may exceed unique when duplicate shingles appear across mails).
