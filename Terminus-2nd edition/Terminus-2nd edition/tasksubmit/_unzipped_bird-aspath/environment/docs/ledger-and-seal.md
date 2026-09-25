# Ledger and seal

Ledger fields: schema_version=1, run_id, wave_aborted, peer_order, rows, rib_after.

Row fields: peer_id, prefix, action, as_path, communities, med, matched_filter, aborted.

Seal report fields: schema_version, run_id, wave_aborted, peer_order, rows, audit_digest.

audit_digest is lowercase hex sha256 of UTF-8 lines peer_id|prefix|action|as_path-commas joined by newlines with no trailing newline, in ledger row order.
