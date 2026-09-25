# Fixture catalog

Bundled release approval bundle:

- /app/data/bundles/release-alpha — release_id app-v2.4.0, four signers, threshold 2, key-c revoked at round 50, four witness rows with provenance chain w001 to w002 to w003 and parallel w004 from w001

Hidden verifier bundles under /opt/verifier-fixtures/witness-bundles:

- tb3-bundle — svc-v9.1 release, witness tw03 with signer tb3-c revoked at round 37, forked provenance from tw01
- revoke-edge-bundle — edge-a revoked at round 100, quorum should fail at round 100

TB3_EPOCH_BIAS environment variable adds its unsigned integer value to the verify quorum round at runtime for hidden runs.
