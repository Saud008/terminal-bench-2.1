# rspamd-fuzzy-audit specification

The driver command is:

    /app/bin/rspamd-fuzzy-audit rotate --corpus-dir DIR --key-manifest PATH \
      --window-size N --console-dump PATH [--dry-run] --summary-out PATH

Inputs:

- corpus-dir: directory with mails.tsv and .eml message bodies (see shingle-window.md).
- key-manifest: JSON with key_epoch, checksum_algo_id, and epoch_salt (key-epoch-rotation.md).
- window-size: shingle character window length (shingle-window.md).
- console-dump: rspamdctl-style fuzzy hash listing (console-dump.md).
- dry-run: compute summary math without mutating sqlite or writing rotation-run.json.
- summary-out: JSON summary path (rotation-summary.md).

Pipeline order (mandatory):

1. Read key manifest and corpus manifest (mails.tsv).
2. Publish shingle snapshot to /app/state/shingle-snapshot.json (shingle-snapshot-contract.md).
3. Rotate sqlite fuzzy index epoch and algorithm id together (fuzzy-index.md, key-epoch-rotation.md).
4. Normalize each mail body, emit shingles with the configured window (shingle-window.md).
5. Insert hashed shingles into /app/state/fuzzy-index.db
6. Parse console dump with lowercase hex normalization and verify every line matches the index (console-dump.md).
7. On console verification failure, write /app/state/rotation-rollback.json before exiting non-zero (key-epoch-rotation.md).
8. Write rotation summary JSON unless dry-run; on success write /app/state/rotation-run.json

Manifest format (mails.tsv): tab-separated header mail_id then eml_file rows listing corpus members in processing sequence.

Bundled scenarios live under /app/fixtures/scenarios/ and are listed in /app/fixtures/catalog.json. Each catalog entry includes a name field identifying the scenario subdirectory (for example basic-two-mails or overlap-duplicates), plus key_manifest, window_size, and console_dump paths relative to that directory.

Platform verification replays contract math through tests/fuzzy_contract_math.py using hashlib and sqlite3 against the same paths documented here.

Environment variable RF_EPOCH_SALT_SUFFIX may append extra salt bytes during hidden fixture runs (key-epoch-rotation.md).
