# Version anti-replay (monotonicity)

Document version on open is the client-supplied value from `didOpen` (defaults to **0** when omitted). Each accepted `didChange` sets version to the client-supplied value **after** staging accepts the batch under admission policy.

If the plane receives a change whose `textDocument.version` equals `last_change_version` already recorded for that URI, it must not append or re-apply the batch (anti-replay).

Version exposed via snapshot attestation must match the merged document state, not a value bumped before staging merges.
