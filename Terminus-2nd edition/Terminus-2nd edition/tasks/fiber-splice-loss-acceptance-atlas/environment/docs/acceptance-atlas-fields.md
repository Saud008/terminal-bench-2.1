# Acceptance atlas fields

Atlas rows sorted by segment_id ascending.
Summary includes accepted_segment_count, rejected_segment_count, event_count, suppressed_duplicate_count, and audit_digest.
audit_digest hashes a compact JSON object with alphabetically sorted keys: run_id, event_count, accepted_segment_count, and sorted segment_id list. Use SHA-256 hex over that JSON body.
