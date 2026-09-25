# Trust report fields

Each trust report JSON includes policy_name matching the active policy bind row.

decisions sort by (trust_level rank, credential_id) where rank is
rejected=0, untrusted=1, trusted=2.

audit_digest is SHA-256 over compact JSON with sort_keys and separators (comma, colon).
The JSON object includes batch_id, policy_name, trusted, untrusted, rejected,
dedupe_blocked, and decision_ids (credential_id values in decisions sort order).
