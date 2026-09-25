# Revocation and KRL

Revocation is checked before principal matching. Fingerprints in the KRL file are normalized to lowercase hex without colons. A revoked fingerprint always yields verdict deny with reason revoked regardless of principal match outcome.
