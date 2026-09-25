# Check contract

POST /v1/check evaluates whether subject has relation on object at the revision encoded in zed_token.

## Request fields

- namespace, object, relation, subject — permission probe coordinates
- zed_token — encoded revision per /app/docs/zed-token-schema.md

## Response fields

- allowed — boolean permission result
- revision — current head revision after evaluation
- zed_token — fresh token for head revision
- used_stale_snapshot — true when check read cached snapshot summaries instead of live store

## Evaluation order

1. Decode zed_token to at_revision.
2. Compare head revision lag against watch_stale_lag_threshold from /app/config/relationwatch.json.
3. When lag is strictly greater than watch_stale_lag_threshold, read live tuples via closure cache and caveat evaluator.
4. When lag is less than or equal to watch_stale_lag_threshold, read probe summaries from /app/state/revision-snapshot.json.

Stale snapshot rule: use stale snapshot summaries when head minus at_revision is less than or equal to watch_stale_lag_threshold. Live evaluation applies when lag is strictly greater than the threshold.

## Transitive permission

Direct tuple match or group tail expansion through the closure cache module. Legacy graph expansion helpers are not used on the check hot path.

## Caveats

When a direct tuple carries caveat_expr, tombstone_revision must be applied before caveat JSON is evaluated.
