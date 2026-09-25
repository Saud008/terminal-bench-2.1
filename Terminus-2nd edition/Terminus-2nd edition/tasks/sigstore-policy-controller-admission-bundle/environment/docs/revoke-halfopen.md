# Revocation seal

Revocation seals deny pulls whose **normalized image digest** equals a revocation `subject_digest` while the pull `timestamp` lies in a half-open window `[start, end)` (end exclusive, RFC3339 UTC).

Revocation hits are terminal denies with reason `revocation_hit`. They cannot be overridden by quorum or builder allow.

Merged policy packs **union** all revocation entries.
