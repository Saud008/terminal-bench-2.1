# Revocation epochs

A keyid listed in revocations.jsonl is revoked for verification epoch e when e is greater than or equal to revoked_epoch.

Revoked signers must not contribute toward quorum even when their witness signature bytes verify.

Witness rows signed before revocation may still appear in staging, but verify quorum must mark revoked_signer true and counts_toward_quorum false for those rows at revoked epochs.
