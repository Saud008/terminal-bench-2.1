# Quorum policy

Quorum counting uses distinct signer_keyid values from witnesses that satisfy all of:

- Ed25519 signature verifies over canonical TW1 message bytes
- witness provenance chain is valid per witness-provenance.md
- signer is not revoked at the verification epoch per revocation-epochs.md

Count each signer_keyid at most once toward quorum even when multiple witness rows share the same signer.

quorum_met is true when the distinct valid signer count is greater than or equal to policy.quorum.threshold.
