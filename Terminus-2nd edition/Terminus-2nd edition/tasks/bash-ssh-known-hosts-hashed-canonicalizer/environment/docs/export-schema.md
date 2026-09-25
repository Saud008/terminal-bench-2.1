# Normalized export schema

After ingest seals the ledger manifest, `kh-normalize` merges staged records and passes them through `/app/lib/kh_emit.sh` for final line emission.

`kh-normalize` writes a UTF-8 text file containing normalized `known_hosts` lines followed by a trailing newline when at least one record is emitted.

Each non-comment output line matches:

```text
[marker ]host-field key-type key-blob[ comment]
```

There is no JSON wrapper. Tests compare the full output text to the independent reference normalizer.

When the input contains no parseable records, the output file is empty (zero bytes).
