# Platform rubric — bluez-bond-trust-reconnect-attestor

**Task folder:** tasks/bluez-bond-trust-reconnect-attestor/
**Written:** 2026-07-16T12:34:09Z
**Upload:** copy lines below into Snorkel platform rubric form (not in zip).

Agent implements bondattest absorb against pairing-addr-type-gate.md for trusted reconnect mismatches, +3
Agent clears resume tokens on bond_remove and increments resume_tokens_cleared per resume-token-revoke.md, +3
Agent captures adapter_power on disconnect rows in seq order per disconnect-power-capture.md, +3
Agent deduplicates GATT discoveries by mac plus lowercased UUID per gatt-uuid-identity.md, +3
Agent applies debounce_ms from config to battery_level reconnect storms per battery-debounce-policy.md, +3
Agent writes midstate snapshot to /app/state/bondattest-midstate.json with midstate_digest per midstate-and-bundle-seals.md, +3
Agent seals /app/output/bond-reconnect-attestation.json with ledger_fingerprint and bundle_seal formulas, +3
Agent honors TB3_TRACE_DIR when resolving relative --trace paths for hidden verifier fixtures, +2
Agent leaves /app/docs and /app/fixtures unchanged while implementing policy modules under /app/lib, +1
Agent implements absorb midstate correctly but leaves seal bundle digests incorrect, -3
Agent hardcodes fixture counts into the attestation bundle without replaying traces, -3
Agent edits protected docs or fixtures to weaken the verifier contracts, -5
