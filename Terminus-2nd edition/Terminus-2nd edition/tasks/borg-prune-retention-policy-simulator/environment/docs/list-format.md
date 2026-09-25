# Borg list fixture format

Each non-comment line is tab-separated:

```
archive_name<TAB>utc_timestamp<TAB>original_size_bytes<TAB>segment_count
```

| Field | Meaning |
|-------|---------|
| archive_name | Unique per logical archive; duplicates allowed in file |
| utc_timestamp | ISO-8601 UTC with Z suffix, e.g. 2024-06-15T10:30:00Z |
| original_size_bytes | Positive integer original archive size |
| segment_count | Positive integer repository segment count attributed to archive |

Lines starting with # and blank lines are ignored.

## Duplicate archive names

When the same archive_name appears on multiple lines, **the last line in file order wins**. Earlier lines are discarded before retention evaluation.
