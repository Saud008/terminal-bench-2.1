# Credential dedupe contract

When reject_duplicate_credential_id is true, the second and later rows sharing
the same credential_id within the batch must be rejected with duplicate_credential.
