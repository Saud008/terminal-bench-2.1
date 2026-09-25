# Platform rubric — rust-fido2-attestation-chain-policy-evaluator

**Task folder:** tasks/rust-fido2-attestation-chain-policy-evaluator/

Agent parses authData user verification from flag bit 0x04 per cbor-attestation-layout.md, +3
Agent validates attestation certificate chain leaf-to-root fingerprint linkage, +3
Agent normalizes AAGUID registry lookup keys to lowercase hyphenated form, +3
Agent applies named UV policy levels from /app/registry/policies/, +3
Agent blocks duplicate credential_id only on second batch occurrence, +3
Agent increments transcript cache run_seq on repeated run-batch, +2
Agent couples policy bind_seq to transcript cache run_seq, +2
Agent sorts trust decisions by trust rank then credential_id ascending, +2
Agent emits 64-char audit_digest over summary and decision ids, +2
Agent honors hidden overlay registry root for alternate transcript bundles, +2
Agent rebuilds cargo release --locked fido2eval before CLI subprocess checks, +2
Agent treats discouraged UV policy as requiring UV bit set, -3
Agent looks up AAGUID without registry normalization and misses metadata hits, -3
Agent rejects the first duplicate credential row instead of the second, -3
Agent leaves run_seq at zero across repeated run-batch invocations, -3
