# Suppression expiry

Policy suppress_until rows define temporary acceptance windows.

## Active suppression

A finding matches a row when:

- canonical rule_key equals row.rule_key
- remapped uri has prefix row.uri_prefix

The finding is actively suppressed when observed_at instant is less than or equal to the row until instant parsed in policy.timezone.

## Rejected findings

When a finding matches a suppress_until row but observed_at is strictly after until, append a rejected-findings.jsonl row with reason suppression_expired. Expired findings must not appear in baseline-revision curated entries or in finding-delta.json export rows.

Findings with active suppression remain in baseline-revision entries with suppressed true.
