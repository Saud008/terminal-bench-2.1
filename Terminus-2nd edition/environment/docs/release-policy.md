# Release policy

Hold tokens gate optional release authorization on quarantine meta files. Policy digest seals which hold tokens were present at staging time.

## hold_token

When msg.QUARANTINE_ID.meta.json includes a hold_token field, reconcile must allow the release only when that value equals the first twelve hexadecimal characters of sha256(seed + ":" + quarantine_id) for the reconcile --seed argument.

When the meta file is missing, or the meta file has no hold_token field, the policy check must allow the release (backward compatible with older fixtures).

A failed hold_token check records a failed release attempt and must not consume a ledger sequence number.

## policy_digest

After ingest, while writing /app/state/release-staging.json, compute policy_digest from /app/state/spool-manifest.json messages:

1. For each manifest message whose on-disk meta contains hold_token, form the line quarantine_id:hold_token.
2. Sort those lines lexicographically.
3. If the list is empty, policy_digest is the empty string. Otherwise policy_digest is the sha256 hex digest of the lines joined by a single newline (no trailing newline after the last line).

Export JSON must copy policy_digest from release staging for the same reconcile. When staging includes policy_digest, export must publish that exact staging value.
