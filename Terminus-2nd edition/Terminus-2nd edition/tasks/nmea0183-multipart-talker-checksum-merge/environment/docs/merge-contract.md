# Merge contract

## Checksum
XOR every byte after the leading `$` up to (but not including) `*`. Compare to the two hex digits after `*`. Invalid checksum lines are rejected.

## Quoted fields
Split on commas outside quotes. Surrounding double quotes are **preserved** in field values. Inside quotes, `""` becomes a single `"`.

## Talker normalization
Canonical talker for merge keys: `GP` and `GN` both become `GN`. Other talkers (including `GL`) stay unchanged. Merge key format: `{canonical_talker}:{sentence}:{multipart_total}`.

## Multipart
Multipart sentences have `fields[0]` = total fragments and `fields[1]` = message number (1-based). Payload concatenates fields from index **3** onward, sorted by message number ascending.

## Single-pass vs session
Without `--state`, incomplete multipart groups (missing fragments) are still emitted in the report.
With `--state PATH`, incomplete groups are buffered in session pending and **not** reported. Orphan fragments that do not include message number `1` are dropped (not persisted). When a new valid RMC date differs from the stored session date, all pending buckets are discarded.

## Duplicate fragments
When pending fragments merge with new input for the same merge key, duplicate message numbers keep the fragment that arrived **later** in the combined pending-plus-input sequence.

## RMC date context
Only RMC sentences with navigation status field `A` update `rmc_date` / `rmc_time`. Status `V` (or other) must not update context. Time-only sentences attach UTC using the latest valid RMC date; midnight rollover advances the calendar across month and year boundaries (including leap days).

## Export
Export reads `/app/state/merge-snapshot.json`, verifies digest, validates talker prefixes, and builds the report from snapshot fields only — never by re-parsing the input stream.
